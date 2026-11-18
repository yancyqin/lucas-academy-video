"""Time 「怎么骗过 AI：面包还是狗？」 from its narration takes: timeline, two mixes and both SRTs.

  /Users/yqin/repo/playground/lucas-academy-video/.venv-align/bin/python scripts/bread-or-dog/build_timeline.py
      [--voice louise --speed 1.1] [--langs en,zh] [--music <file> --music-from S] [--tag NAME]

Writes public/bread-or-dog/timeline.json (read by src/videos/bread-or-dog/BreadOrDogVideo.tsx) and
out/bread-or-dog/<tag>/{mix.<lang>.wav, bread-or-dog.<lang>-track.<en|zh-Hans>.srt}.

One picture, two voice tracks (Yancy, 2026-11-16: 「Louise 1.1，英文视频配中文音轨」), as the butterfly film: every line
gets one slot, as long as the longer of its English and Chinese takes, and each language's take starts at its slot's
start, so either track fits the same picture. The picture's beats hang on the slots (the cake is cut in the silence
before sc01-04 「其实是一个蛋糕」, which is its own line for that reason). Each language gets its own mix (its own lines
duck the music, scripts/music_ducking.py) and its own SRTs; the other-language SRT of each track is the same timing with
the paired line. Music: music/chosen.json in the data folder (picked from music/listen.html), or --music.
"""
import importlib.util
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(HERE))
import music_ducking  # noqa: E402
import narrate  # noqa: E402

# 「跨越中等收入陷阱」's builder for decode, lufs, ffread, stamp, SR, SRT_MAX (loaded by path; it reads argv on import)
_spec = importlib.util.spec_from_file_location("mit_build_timeline", ROOT / "scripts/middle-income-trap/build_timeline.py")
mit = importlib.util.module_from_spec(_spec)
_argv, sys.argv = sys.argv, sys.argv[:1]
_spec.loader.exec_module(mit)
sys.argv = _argv

args = sys.argv[1:]
VOICE = narrate.opt(args, "--voice", "louise")
SPEED = float(narrate.opt(args, "--speed", "1.1"))
LANGS = narrate.opt(args, "--langs", "en,zh").split(",")
DATA = next(p / "lucas-academy-video-data" for p in ROOT.parents if (p / "lucas-academy-video-data").is_dir()) / "bread-or-dog"
# music/chosen.json (file, from, credit) names the bed; --music / --music-from override it for a listening test
_chosen = json.loads((DATA / "music/chosen.json").read_text()) if (DATA / "music/chosen.json").exists() else {}
MUSIC = Path(narrate.opt(args, "--music", str(DATA / "music" / _chosen["file"]) if _chosen else ""))
MUSIC_FROM = float(narrate.opt(args, "--music-from", str(_chosen.get("from", 0))))
MUSIC_CREDIT = _chosen.get("credit", "") if "--music" not in args else ""
PUB = ROOT / "public/bread-or-dog"
OUT = ROOT / "out/bread-or-dog" / narrate.opt(args, "--tag", f"{VOICE}-{SPEED:.2f}-{'-'.join(LANGS)}")
SR = mit.SR
FPS = 30

TITLE = 3.0                 # title card, music only
GAP, QUESTION_GAP = 0.45, 0.9
SECTION_GAP = 1.0           # between tricks: the music comes up, the next picture settles
HOLD_AFTER = {"sc00-04": 0.9,   # both wrong answers (teddy bear, snout) land on the muffin
              "sc00-06": 1.0,   # ResNet-50's "Indian elephant" lands on the cat
              "sc01-02": 0.6,   # the six AIs' answers finish before the pause
              "sc02-04": 1.8,   # time to read LLaVA's answer before Astra's part
              "sc02-08": 1.6,   # the question to the viewer breathes
              "sc05-04": 0.8,   # ear, eye and tail tied together
              "sc05-05": 1.0}   # the wall of pictures
END_TAIL, CREDITS = 2.5, 7.0
BED_LUFS, FINAL_LUFS, FINAL_TP = -20.0, -16.0, -2.2
EN_MAX, CUE_PAD = 42, 4


def en_cues(text: str, start: float, end: float):
    """English captions (as the butterfly film): at most two lines of EN_MAX letters per cue, timed by length."""
    def balanced(words):
        k = min(range(1, len(words)), key=lambda k: abs(len(" ".join(words[:k])) - len(" ".join(words[k:]))))
        return " ".join(words[:k]), " ".join(words[k:])

    def fits(words):
        if len(" ".join(words)) <= EN_MAX:
            return True
        return len(words) > 1 and all(len(x) <= EN_MAX for x in balanced(words))

    pieces, cur = [], []
    for w in text.split():
        if cur and not fits(cur + [w]):
            pieces.append(cur); cur = [w]
        else:
            cur.append(w)
            if re.search(r"[.?!:;]$", w) and len(" ".join(cur)) > EN_MAX:
                pieces.append(cur); cur = []
    if cur:
        pieces.append(cur)
    if len(pieces) > 1 and len(pieces[-1]) < 3:
        words = pieces[-2] + pieces[-1]
        k = min(range(1, len(words)), key=lambda k: abs(len(" ".join(words[:k])) - len(" ".join(words[k:]))))
        if fits(words[:k]) and fits(words[k:]):
            pieces[-2:] = [words[:k], words[k:]]
        elif fits(words):
            pieces[-2:] = [words]
    total, t = sum(len(" ".join(p)) + CUE_PAD for p in pieces), start
    for p in pieces:
        line = " ".join(p)
        d = (end - start) * (len(line) + CUE_PAD) / total
        if len(line) > EN_MAX:
            line = "\n".join(balanced(p))
        yield t, t + d, line
        t += d


def zh_cues(text: str, start: float, end: float):
    """Chinese captions: split after punctuation, merged up to SRT_MAX characters (punctuation at the end not counted)."""
    bare = lambda x: x.rstrip("，。；、！？：…")  # noqa: E731
    parts = [q for q in re.split(r"(?<=[，。；：？！、])", text) if q.strip()]
    merged = []
    for q in parts:
        if merged and len(bare(merged[-1] + q)) <= mit.SRT_MAX:
            merged[-1] += q
        else:
            merged.append(q)
    total, t = sum(len(q) + CUE_PAD for q in merged), start
    for q in merged:
        d = (end - start) * (len(q) + CUE_PAD) / total
        yield t, t + d, q.rstrip("，。；、")
        t += d


def main():
    lines = {"zh": {l["id"]: l for l in narrate.load(SPEED, SPEED)}, "en": {l["id"]: l for l in narrate.load_en(SPEED)}}
    takes = {lang: narrate.takes_dir(VOICE, lang) for lang in LANGS}
    ids = list(lines["zh"])
    audio = {lang: np.zeros(int(60 * 6 * SR), np.float32) for lang in LANGS}
    placed = {lang: {} for lang in LANGS}
    slots = {}

    def put(lid: str, t: float) -> float:
        ends = []
        for lang in LANGS:
            y = mit.decode(takes[lang] / f"s{lines[lang][lid]['speed']:.2f}" / f"{lid}.wav", trim=True)
            i = int(t * SR)
            audio[lang][i:i + len(y)] += y
            placed[lang][lid] = (round(t, 3), round(t + len(y) / SR, 3))
            ends.append(t + len(y) / SR)
        slots[lid] = (round(t, 3), round(max(ends), 3))
        return max(ends) + HOLD_AFTER.get(lid, 0)

    sections = {}
    t = TITLE
    for sec in sorted({i[:4] for i in ids}):
        group = [i for i in ids if i.startswith(sec)]
        start = t
        t += 0.5 if sec == "sc00" else SECTION_GAP * 0.6
        for k, lid in enumerate(group):
            if k:
                asked = any(lines[lang][group[k - 1]]["question"] for lang in ("zh", "en"))
                t += max(lines["zh"][lid]["pause"] or GAP, QUESTION_GAP if asked else 0)
            t = put(lid, t)
        t += SECTION_GAP * 0.4 if sec != "sc05" else END_TAIL
        sections[sec] = [round(start, 3), round(t, 3)]
        t += SECTION_GAP * 0.6 if sec not in ("sc05",) else 0
    keys = list(sections)  # sections run back to back: each ends where the next begins (the last at the credits)
    for a_, b_ in zip(keys, keys[1:]):
        sections[a_][1] = sections[b_][0]
    sections[keys[-1]][1] = round(t, 3)
    credits = [round(t, 3), round(t + CREDITS, 3)]
    total = t + CREDITS
    # Yancy's Muse clip of the cut (data muse/clip.json: {"file": <mp4 under muse/>, "open": seconds into the clip when the
    # cut cake is clearly open}): copied to public/, started as the right card fills the frame (sc01-03), and offset so the
    # open cake lands on sc01-04 「其实是一个蛋糕」. Without it the picture dissolves to the end reference frame.
    muse = None
    clip_json = DATA / "muse/clip.json"
    if clip_json.exists():
        c = json.loads(clip_json.read_text())
        PUB.mkdir(parents=True, exist_ok=True)
        shutil.copy(DATA / "muse" / c["file"], PUB / "muse-cut.mp4")
        start = slots["sc01-03"][0] - 0.3
        offset = c["open"] - (slots["sc01-04"][0] - start)
        if offset < 0:
            start -= offset
            offset = 0.0
        length = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                       str(PUB / "muse-cut.mp4")], capture_output=True, text=True, check=True).stdout)
        if offset + sections["sc01"][1] - start > length:
            print(f"Muse clip ends {offset + sections['sc01'][1] - start - length:.1f} s before trick 1 does (last frame holds)")
        last = None
        if c.get("last"):  # the clip's last frame, held after the clip ends (it is shorter than the rest of trick 1)
            subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", "92", str(DATA / "muse" / c["last"]),
                            "--out", str(PUB / "muse-last.jpg")], check=True, capture_output=True)
            last = "muse-last.jpg"
        muse = {"src": "muse-cut.mp4", "from": round(offset, 3), "at": round(start, 3), "until": sections["sc01"][1],
                "length": round(length, 3), "last": last}
    tl = {"fps": FPS, "voice": f"{VOICE} {SPEED} ({','.join(LANGS)})", "durationSeconds": round(total, 3), "muse": muse,
          "title": [0, TITLE], "sections": sections, "credits": credits,
          "lines": {k: {"start": a, "end": b} for k, (a, b) in slots.items()}, "music": MUSIC_CREDIT}

    OUT.mkdir(parents=True, exist_ok=True)
    n = int(total * SR)
    if MUSIC.is_file():
        bed = mit.ffread(MUSIC)[int(MUSIC_FROM * SR):]
        bed *= 10 ** ((BED_LUFS - mit.lufs(bed)) / 20)
        bed = np.tile(bed, int(np.ceil(n / len(bed))))[:n]
    else:
        print("no music (draft without a bed)")
        bed = np.zeros(n, np.float32)
    for lang in LANGS:
        cues = [{"speech": {"start": a, "end": b}} for a, b in placed[lang].values()]
        env_path = OUT / f"env.{lang}.wav"
        music_ducking.envelope(cues, total, BED_LUFS, env_path)
        env = mit.ffread(env_path)
        m = min(len(env), n)
        mix = audio[lang][:m] + bed[:m] * env[:m]
        mix *= 10 ** ((FINAL_LUFS - mit.lufs(mix)) / 20)
        sf.write(OUT / f"mix.{lang}.raw.wav", mix, SR, subtype="FLOAT")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(OUT / f"mix.{lang}.raw.wav"), "-af",
                        f"alimiter=limit={10 ** (FINAL_TP / 20):.4f}:attack=5:release=60:level=false",
                        "-c:a", "pcm_s24le", str(OUT / f"mix.{lang}.wav")], check=True)
        own, other = [], []
        for lid, (a, b) in sorted(placed[lang].items(), key=lambda kv: kv[1][0]):
            zc = list(zh_cues(lines["zh"][lid]["caption"], a, b))
            ec = list(en_cues(lines["en"][lid]["caption"], a, b))
            own += ec if lang == "en" else zc
            other += zc if lang == "en" else ec
        sub = {"en": ("en", "zh-Hans"), "zh": ("zh-Hans", "en")}[lang]
        for name, cues_ in ((sub[0], own), (sub[1], other)):
            (OUT / f"bread-or-dog.{lang}-track.{name}.srt").write_text(
                "".join(f"{k}\n{mit.stamp(a)} --> {mit.stamp(b)}\n{s}\n\n" for k, (a, b, s) in enumerate(cues_, 1)))
    PUB.mkdir(parents=True, exist_ok=True)
    (PUB / "timeline.json").write_text(json.dumps(tl, ensure_ascii=False, indent=1))
    for lang in LANGS:
        pad = sum((slots[k][1] - slots[k][0]) - (b - a) for k, (a, b) in placed[lang].items())
        print(f"{lang}: {len(placed[lang])} lines, padding to the shared slots {pad:.1f} s")
    print(f"{VOICE} {SPEED} {LANGS}: {total:.1f} s; music {MUSIC.name or '-'} from {MUSIC_FROM}s -> {OUT}")


if __name__ == "__main__":
    main()
