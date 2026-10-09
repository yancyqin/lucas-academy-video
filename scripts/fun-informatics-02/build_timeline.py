"""Reuse episode 1's narration/timeline/mix pipeline for the Chinese-only episode.

--draft explicitly permits missing voice takes for visual previews. Final builds
require all 84 WAVs. No English narration or English composition is generated.
"""
import argparse
import array
import difflib
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import tempfile
import textwrap
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
media = ROOT.parent / "lucas-academy-media"
if not media.is_dir(): media = ROOT.parents[1] / "lucas-academy-media"
os.environ.setdefault("LUCAS_MEDIA", str(media))
spec = importlib.util.spec_from_file_location("fi01_timeline", ROOT / "scripts/fun-informatics-01/build_timeline.py")
shared = importlib.util.module_from_spec(spec)
spec.loader.exec_module(shared)
shared.PUB = ROOT / "public/fun-informatics-02"
shared.DELIVERY = ROOT / "out/fun-informatics-02/delivery"
shared.FILM_NAME = "fun-informatics-02"
shared.VOICES = {"zh": shared.MEDIA / "outputs/louise/zh/fun-informatics-02-v1"}
shared.TITLE = {"zh": "你认识 Claude 吗？", "en": "Do You Know Claude?"}
shared.LEAD_IN = 0.6
shared.END_CARD = 8.0
shared.wp.MUSIC = shared.PUB / "music/clair-de-lune-goedhart.ogg"
shared.wp.PEAK_DB = -2.0  # AAC headroom for the final <= -1.5 dBTP ceiling.
MUSIC_SOURCE = shared.wp.MUSIC
CODA_START = 272.0
CODA_END = shared.seconds(MUSIC_SOURCE)
ORIGINAL_MIX = shared.wp.mix_with_music
ORIGINAL_ENVELOPE = shared.wp.music_envelope
LISTEN_BOOST_DB = 20.0  # The original pianissimo ending is much quieter than the full piece.
# Feedback is only a quiet confirmation, including when narration is absent.
FEEDBACK_SPEAKING_LUFS = -50.0
FEEDBACK_PAUSE_LUFS = -43.0
shared.HOLD = {
    "cl00-01": 2.0, "cl00-02": 1.0, "cl00-03": 1.5, "cl00-04": 3.0, "cl00-05": 1.5, "cl00-06": 1.5, "cl00-07": 4.0,
    "cl01-03": 1.0, "cl01-04": 1.0, "cl01-05": 1.0,
    "cl02-04": 1.0, "cl02-07": 2.0, "cl02-08": 1.0, "cl02-09": 2.0, "cl02-10": 1.0, "cl02-11": 2.0, "cl02-12": 4.0,
    "cl02-13": 2.0, "cl02-14": 2.5, "cl02-16": 1.0,
    "cl03-02": 1.5, "cl03-03": 1.0, "cl03-04": 2.0, "cl03-05": 2.0, "cl03-06": 2.0, "cl03-08": 2.0,
    "cl03-10": 1.0, "cl03-12": 1.5, "cl03-13": 2.0, "cl03-14": 1.0, "cl03-15": 1.0, "cl03-18": 1.0,
    "cl04-01": 1.5, "cl04-04": 1.0, "cl04-05": 15.0, "cl04-08": 1.5, "cl04-10": 1.0, "cl04-11": 1.5,
    "cl04-12": 1.0, "cl04-17": 2.0, "cl04-18": 1.5, "cl04-19": 4.0,
    "cl05-05": 1.5, "cl05-07": 3.0,
    "cl06-01": 1.5, "cl06-02": 2.0, "cl06-03": 2.0, "cl06-04": 4.0, "cl06-05": 1.0, "cl06-06": 1.5,
    "cl07-01": 4.0,
}


def episode_music_envelope(cues, total, bed_lufs, path):
    """Keep normal ducking, then make the piano the focus during listening."""
    ORIGINAL_ENVELOPE(cues, total, bed_lufs, path)
    with wave.open(str(path)) as wav:
        envelope = array.array("h", wav.readframes(wav.getnframes()))
    cue = next(c for c in cues if c["id"] == "cl06-04")
    begin, end = cue["speech"]["end"], cue["end"]
    rate = shared.wp.ENV_RATE
    samples = array.array("f", (value / 32767 for value in envelope))
    for k in range(max(0, round(begin * rate)), min(len(samples), round(end * rate))):
        t = k / rate
        progress = max(0.0, min(1.0, (t - begin) / 1.5, (end - t) / 0.8))
        smooth = progress * progress * (3 - 2 * progress)
        samples[k] *= 10 ** (LISTEN_BOOST_DB * smooth / 20)
    # Float envelopes retain gain above unity without silently clipping it.
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(rate), "-ac", "1", "-i", "-", "-c:a", "pcm_f32le", str(path)], input=samples.tobytes(), check=True)


def episode_mix(voice, out, cues, total):
    """A complete, unsped coda replaces the bed during the harmony example."""
    coda_cue = next(c for c in cues if c["id"] == "cl06-04")
    begin = coda_cue["start"]+1
    end = begin+CODA_END-CODA_START
    if end+.5>coda_cue["end"]:
        raise SystemExit("Coda needs enough viewing hold to preserve the final chord")
    loops = max(1, __import__("math").ceil((total-shared.wp.MUSIC_XFADE)/(CODA_END-shared.wp.MUSIC_XFADE)))
    inputs = sum((["-i",str(MUSIC_SOURCE)] for _ in range(loops)),[])
    chain, last=[],"[0:a]"
    for n in range(1,loops):
        chain.append(f"{last}[{n}:a]acrossfade=d={shared.wp.MUSIC_XFADE}:c1=tri:c2=tri[m{n}]")
        last=f"[m{n}]"
    gate=f"if(lt(t,{begin}),1,if(lt(t,{begin+1}),{begin+1}-t,if(lt(t,{end}),0,if(lt(t,{end+1}),t-{end},1))))"
    chain.extend([
        f"{last}atrim=0:{total},asetpts=PTS-STARTPTS,volume='{gate}':eval=frame[bed]",
        f"[{loops}:a]atrim=start={CODA_START}:end={CODA_END},asetpts=PTS-STARTPTS,afade=t=in:d=0.8,adelay={round(begin*1000)}|{round(begin*1000)}[coda]",
        f"[bed][coda]amix=inputs=2:normalize=0,atrim=0:{total}[music]",
    ])
    with tempfile.TemporaryDirectory() as tmp:
        prepared=Path(tmp)/"music-with-complete-coda.wav"
        subprocess.run(["ffmpeg","-v","error","-y",*inputs,"-i",str(MUSIC_SOURCE),"-filter_complex",";".join(chain),"-map","[music]","-ar","48000","-c:a","pcm_f32le",str(prepared)],check=True)
        shared.wp.MUSIC=prepared
        shared.wp.music_envelope=episode_music_envelope
        try: ORIGINAL_MIX(voice,out,cues,total)
        finally:
            shared.wp.MUSIC=MUSIC_SOURCE
            shared.wp.music_envelope=ORIGINAL_ENVELOPE


shared.wp.mix_with_music=episode_mix


def markers(tl):
    """Align approved caption units to checked Whisper words after trim offset."""
    path = ROOT / "out/fun-informatics-02/narration-check.json"
    checked = json.loads(path.read_text())["cues"] if path.exists() else {}
    result, word_times = {}, {}
    phrases = {
        "cl02-12": ["这是街道", "这是操场", "这是海边"],
        "cl03-04": ["英文这里", "中文这里"],
        "cl03-05": ["你一下就选了"],
        "cl04-11": ["读到最后"],
        "cl04-18": ["听着很通顺", "莫奈"],
        "cl07-01": ["有多少是新的呢？", "有多少是真的呢？", "什么是重要的呢？", "什么是可以忽略的呢？", "这也是", "一起学习"],
    }
    for cue in tl["cues"]:
        cid = cue["id"]
        if cid not in checked:
            continue
        record = checked[cid]
        audio = shared.VOICES["zh"] / (cid + ".wav")
        if hashlib.sha256(audio.read_bytes()).hexdigest() != record["sha256"]:
            continue
        analysis = record["analyses"].get("medium", record["analyses"].get("small"))
        if "_cut" not in analysis:
            continue
        words = analysis["_cut"]["words"]
        normalize = lambda s: re.sub(r"[^一-鿿a-z0-9]", "", s.lower())
        want = normalize(cue["zh"])
        got, times = "", []
        for word in words:
            text = normalize(word["word"])
            got += text
            times.extend([word["start"]] * len(text))
        matched = {}
        for op, a, b, x, y in difflib.SequenceMatcher(None, want, got, autojunk=False).get_opcodes():
            if op == "equal":
                matched.update({a+i: times[x+i] for i in range(b-a)})
        raw = shared.wp.read_wav(audio)
        loud = [i for i in range(0, len(raw), 120) if abs(raw[i]) > shared.wp.SILENCE]
        offset = max(0, loud[0]-shared.wp.KEEP) / shared.RATE if loud else 0
        raw_indices = [m.start() for m in re.finditer(r"[一-鿿a-zA-Z0-9]",cue["zh"])]
        word_times[cid] = [{"offset":raw_indices[i],"time":round(cue["speech"]["start"]+max(0,t-offset),3)} for i,t in sorted(matched.items())]
        entries = {}
        for phrase in phrases.get(cid,[]):
            index = want.find(normalize(phrase))
            if index < 0:
                continue
            found = next((matched[i] for i in range(index, min(index+3,len(want))) if i in matched), None)
            if found is not None:
                entries[phrase] = round(cue["speech"]["start"] + max(0,found-offset), 3)
        result[cid] = entries
    return result, word_times


def subtitles(tl):
    """Two readable external caption files, timed to the Chinese film only."""
    for suffix, language in [("zh-Hans", "zh"), ("en", "en")]:
        blocks = []
        for cue in tl["cues"]:
            text = cue[language]
            # Sentence punctuation gives useful breath/meaning boundaries.
            pieces = re.findall(r"[^。？！]+[。？！]*", text) if language == "zh" else re.findall(r"[^.!?]+[.!?]*", text)
            parts = []
            for piece in pieces:
                piece = piece.strip()
                if not piece: continue
                width = 38 if language == "zh" else 84
                if language == "en":
                    wrapped=textwrap.wrap(piece,width=42,break_long_words=False)
                    parts.extend(" ".join(wrapped[i:i+2]) for i in range(0,len(wrapped),2))
                    continue
                if len(piece) <= width:
                    parts.append(piece)
                elif language == "zh":
                    units = re.findall(r"[^，；：]+[，；：]*", piece)
                    current = ""
                    for unit in units:
                        if current and len(current+unit)>width:
                            parts.append(current); current = ""
                        while len(unit)>width:
                            if current: parts.append(current); current=""
                            parts.append(unit[:width]); unit=unit[width:]
                        current += unit
                    if current: parts.append(current)
                else:
                    parts.extend(textwrap.wrap(piece, width=width, break_long_words=False))
            total_weight = sum(len(part) for part in parts)
            begin = cue["speech"]["start"]
            span = cue["speech"]["end"]-begin
            cursor = 0
            raw_cursor = 0
            for i, part in enumerate(parts):
                a = begin + span*cursor/total_weight
                cursor += len(part)
                b = begin+span*cursor/total_weight
                if language == "zh":
                    raw_index=cue["zh"].find(part,raw_cursor)
                    aligned=next((word["time"] for word in tl["wordTimes"].get(cue["id"],[]) if raw_index<=word["offset"]<raw_index+min(4,len(part))),None)
                    if aligned is not None: a=aligned
                    raw_cursor=raw_index+len(part)
                if i==len(parts)-1: b=cue["speech"]["end"]+.35
                if language == "zh":
                    formatted = part if len(part)<=22 else part[:22]+"\n"+part[22:]
                else:
                    formatted = "\n".join(textwrap.wrap(part,width=42,break_long_words=False))
                blocks.append((a,b,formatted))
        # Keep boundaries non-overlapping when a Whisper word replaces an estimate.
        for i in range(len(blocks)-1):
            a,b,text=blocks[i]; next_start=blocks[i+1][0]
            blocks[i]=(a,max(a+.08,min(b,next_start-.01)),text)
        output = "\n".join(f"{i}\n{shared.wp.srt_time(a)} --> {shared.wp.srt_time(b)}\n{text}\n" for i,(a,b,text) in enumerate(blocks,1))
        (shared.DELIVERY / f"fun-informatics-02.zh.{suffix}.srt").write_text(output)


def mix_feedback(tl):
    """Restore the app's original short cues at the curve's actual event times."""
    sounds = tl.get("gameFeedback", [])
    if not sounds: return
    rate=48000
    track=array.array("f", [0.0]) * round(tl["durationSeconds"]*rate*2)
    for sound in sounds:
        source=shared.PUB / "sfx" / sound["file"]
        data=subprocess.run(["ffmpeg","-v","error","-i",str(source),"-ar",str(rate),"-ac","2","-f","f32le","-"],capture_output=True,check=True).stdout
        clip=array.array("f", data)
        level=shared.wp.loudness("-i",str(source))
        speaking=any(c["speech"]["start"]<=sound["time"]<c["speech"]["end"] for c in tl["cues"])
        target=FEEDBACK_SPEAKING_LUFS if speaking else FEEDBACK_PAUSE_LUFS
        gain=10**((target-level)/20)
        at=round(sound["time"]*rate)*2
        for i,value in enumerate(clip):
            if at+i<len(track): track[at+i]+=value*gain
    sfx=shared.PUB / "audio/game-feedback.f32"
    sfx.write_bytes(track.tobytes())
    base=shared.PUB / "audio/zh.mix.wav"
    premix=shared.PUB / "audio/zh.feedback-premix.wav"
    subprocess.run(["ffmpeg","-v","error","-y","-i",str(base),"-f","f32le","-ar",str(rate),"-ac","2","-i",str(sfx),"-filter_complex","[0:a][1:a]amix=inputs=2:normalize=0", "-c:a","pcm_s16le",str(premix)],check=True)
    gain=shared.wp.FILM_LUFS-shared.wp.loudness("-i",str(premix))
    limited=shared.PUB / "audio/zh.peak-limited.wav"
    subprocess.run(["ffmpeg","-v","error","-y","-i",str(premix),"-af",f"volume={gain:.3f}dB,aresample=192000,alimiter=limit=0.7079:level=false:latency=true,aresample=48000",str(limited)],check=True)
    makeup=min(.6,shared.wp.FILM_LUFS-shared.wp.loudness("-i",str(limited)))
    subprocess.run(["ffmpeg","-v","error","-y","-i",str(limited),"-af",f"volume={makeup:.3f}dB",str(base)],check=True)
    limited.unlink()
    premix.unlink();sfx.unlink()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--draft", action="store_true")
    args = ap.parse_args()
    cues = json.loads((shared.PUB / "narration/cues.json").read_text())
    missing = [c["id"] for c in cues if not (shared.VOICES["zh"] / (c["id"] + ".wav")).is_file()]
    if missing and not args.draft:
        raise SystemExit(f"Final timeline needs all 84 Chinese takes; missing {len(missing)}: {', '.join(missing[:6])}")
    coda_voice=shared.VOICES["zh"] / "cl06-04.wav"
    spoken=len(shared.wp.trim(shared.wp.read_wav(coda_voice)))/shared.RATE if coda_voice.exists() else len(cues[[c["id"] for c in cues].index("cl06-04")]["zh"])/4.6
    shared.HOLD["cl06-04"]=max(4.0,CODA_END-CODA_START+2.0-shared.ONSET-spoken-shared.GAP)
    shared.build(["zh"])
    path = shared.PUB / "timeline.zh.json"
    tl = json.loads(path.read_text())
    tl.update({"draft": bool(missing), "missingNarration": missing, "narrationPolicy": "Chinese only; English voice on hold"})
    tl["art"] = [str(p.relative_to(shared.PUB)) for p in (shared.PUB / "art").glob("*.jpg")]
    tl["recordings"] = {p.stem: json.loads(p.read_text()) for p in (shared.PUB / "footage").glob("*.json")}
    tl["markers"],tl["wordTimes"] = markers(tl)
    coda_cue=next(c for c in tl["cues"] if c["id"]=="cl06-04")
    tl["musicExample"]={"sourceStart":CODA_START,"sourceEnd":CODA_END,"start":coda_cue["start"]+1,"end":coda_cue["start"]+1+CODA_END-CODA_START,"route":"I–III♭–I rather than the familiar I–V–I; real final tonic retained","analysisSource":"https://johnhooker.tepper.cmu.edu/osherMusicDebussy.pdf#page=31"}
    path.write_text(json.dumps(tl, ensure_ascii=False, indent=2) + "\n")
    subprocess.run(["node",str(ROOT / "scripts/fun-informatics-02/playback.cjs")],check=True,cwd=ROOT)
    tl=json.loads(path.read_text())
    subtitles(tl)
    mix_feedback(tl)


if __name__ == "__main__":
    main()
