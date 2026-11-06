"""Check the delivered single-picture review, subtitle selection and provenance."""
from pathlib import Path
import hashlib
import json
import re
import subprocess
import html
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "out/family-ai-lab-01"


def main():
    voiced = '--voiced' in sys.argv
    delivery = OUT / ('delivery' if voiced else 'review')
    tl = json.loads((ROOT / "public/family-ai-lab-01/timeline.json").read_text())
    revision=tl.get('revision',1)
    visual_revision=tl.get('visualRevision',revision)
    if visual_revision>=2:delivery=delivery/f'v{visual_revision}'
    selected = json.loads((ROOT / "docs/family-ai-lab-01/selected-data.json").read_text())
    if voiced:
        assert tl.get('narrated')
        voices = json.loads((ROOT / 'public/family-ai-lab-01/narration.json').read_text())
        choices = json.loads((ROOT / 'docs/family-ai-lab-01/voice-choices.json').read_text())
        assert len(choices) == 2 * len(tl['lines'])
        for lang in ('en', 'zh'):
            assert len(voices[lang]) == len(tl['lines'])
            for line in tl['lines']:
                voice = voices[lang][line['id']]
                assert voice['caption'] == line['text'][lang]
                assert choices[f'{lang}/{line["id"]}']['checked']
                assert hashlib.sha256((ROOT / 'public/family-ai-lab-01' / voice['clip']).read_bytes()).hexdigest() == voice['sha256']
                assert voice['seconds'] + .1 <= line['duration'] / tl['fps']
    for name, digest in selected["sha256"].items():
        p = ROOT / "scripts/perceptron-race/results" / (name + ".json")
        assert hashlib.sha256(p.read_bytes()).hexdigest() == digest, name
    assert [l["id"] for l in tl["lines"] if l["scene"] == 2] == ["fa01-02-01"]
    assert {l["scene"] for l in tl["lines"]} == set(range(1, 9))
    assert len(set(l["id"] for l in tl["lines"])) == len(tl["lines"])
    assert all("{" not in t and "}" not in t for l in tl["lines"] for t in l["text"].values())
    for left, right in zip(tl["lines"], tl["lines"][1:]):
        assert left["from"] + left["duration"] == right["from"]
    race = next(l for l in tl["lines"] if l["visual"] == "race-run")
    astra = json.loads((ROOT / "scripts/perceptron-race/results/astra-low.json").read_text())
    assert race["duration"] / tl["fps"] > astra["median_model"] + .5
    # All external subtitles use exactly the common cue boundaries.
    cue_times = []
    for lang in ("en", "zh-Hans"):
        text = (delivery / (lang + ".srt")).read_text()
        cues = re.findall(r"\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}", text)
        assert len(cues) == len(tl["lines"])
        cue_times.append(cues)
        blocks=re.split(r'\n\s*\n',text.strip())
        for block,line in zip(blocks,tl['lines']):
            words=' '.join(block.splitlines()[2:])
            expected=line['text']['en' if lang=='en' else 'zh']
            assert re.sub(r'\s','',words)==re.sub(r'\s','',expected),(lang,line['id'])
    assert cue_times[0] == cue_times[1]
    film = delivery / ('family-ai-lab-01.bilingual.mp4' if voiced else 'family-ai-lab-01.review.mp4')
    probe = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(film)]))
    videos = [s for s in probe["streams"] if s["codec_type"] == "video"]
    subtitles = [s for s in probe["streams"] if s["codec_type"] == "subtitle"]
    assert len(videos) == 1 and (videos[0]["width"], videos[0]["height"]) == (1920, 1080)
    assert videos[0]["r_frame_rate"] == "30/1"
    audio = [s for s in probe['streams'] if s['codec_type']=='audio']
    if voiced:
        assert len(audio)==2
        assert [(s['tags']['language'],s['disposition']['default']) for s in audio]==[('eng',1),('zho',0)]
        assert all(s['codec_name']=='aac' for s in audio)
    else:
        assert not audio, 'No narration at review stage'
    assert len(subtitles) == (0 if revision>=2 else 2)
    if revision<2:assert [(s["tags"]["language"], s["disposition"]["default"]) for s in subtitles] == [("eng", 1), ("zho", 0)]
    for index, lang in ([] if revision>=2 else enumerate(("en", "zh"))):
        embedded = subprocess.check_output(["ffmpeg", "-v", "error", "-i", str(film), "-map", f"0:s:{index}", "-c:s", "srt", "-f", "srt", "-"], text=True)
        blocks = re.split(r"\n\s*\n", embedded.strip())
        assert len(blocks) == len(tl["lines"])
        for block, line in zip(blocks, tl["lines"]):
            words = " ".join(block.splitlines()[2:])
            words = html.unescape(re.sub(r"<[^>]+>", "", words))
            assert re.sub(r"\s", "", words) == re.sub(r"\s", "", line["text"][lang]), (lang, line["id"])
    assert abs(float(probe["format"]["duration"]) - tl["durationInFrames"] / tl["fps"]) < .1
    if voiced:
        assert all(abs(float(s['duration']) - tl['durationInFrames']/tl['fps']) < .1 for s in audio)
    covers=[OUT/f"cover/cover-v2.{lang}.png" for lang in ('en','zh')] if revision>=2 else [OUT/f"cover/design-{n}.{lang}.png" for n in (1,2,3) for lang in ('en','zh')]
    for image in covers:
        dims=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','stream=width,height','-of','json',str(image)]))['streams'][0]
        assert (dims['width'],dims['height'])==(1280,720)
    if revision>=2:
        intro=json.loads((ROOT/'public/family-ai-lab-01/intro.json').read_text())
        assert intro['ready']
        assert hashlib.sha256((ROOT/'public/family-ai-lab-01'/intro['path']).read_bytes()).hexdigest()==intro['sha256']
        assert tl['lines'][0]['visual']=='time-travel-intro'
        assert tl['lines'][0]['duration']/tl['fps']>=intro['seconds']
        assert len(tl['lines'])==77
        accepted=json.loads((ROOT/'docs/family-ai-lab-01/accepted-script-v2.json').read_text())
        for name,digest in accepted['sha256'].items():
            assert hashlib.sha256((ROOT/'docs/family-ai-lab-01'/name).read_bytes()).hexdigest()==digest,name
    if visual_revision>=3:
        atmosphere=json.loads((ROOT/'docs/family-ai-lab-01/atmosphere-v3.json').read_text())
        assert atmosphere['unchanged']['durationFrames']==tl['durationInFrames']
        inputs=ROOT/'public/family-ai-lab-01'
        assert hashlib.sha256((inputs/'narration.json').read_bytes()).hexdigest()==atmosphere['unchanged']['narrationManifestSha256']
        for asset in atmosphere['screenBackgrounds']:
            assert hashlib.sha256((ROOT/asset['path']).read_bytes()).hexdigest()==asset['sha256'],asset['path']
        for lang in ('en','zh'):
            assert hashlib.sha256((inputs/f'review.{lang}.srt').read_bytes()).hexdigest()==atmosphere['unchanged']['srtSha256'][lang]
            sound=atmosphere['unchanged']['audio'][lang]
            assert hashlib.sha256((ROOT/sound['path']).read_bytes()).hexdigest()==sound['sha256']
    check = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(film), "-vf", "blackdetect=d=0.07:pix_th=0.06:pic_th=0.985", "-an", "-sn", "-f", "null", "-"], text=True, capture_output=True, check=True)
    black = [l for l in check.stderr.splitlines() if "black_start:" in l]
    assert not black, black
    result = {"durationSeconds": tl["durationInFrames"] / tl["fps"], "video": "1920x1080, 30 fps",
              "audioTracks": len(audio), "subtitleTracks": [] if revision>=2 else [{"language": "English", "default": True}, {"language": "Simplified Chinese", "default": False}],
              "captions": "no embedded or burned captions; external SRTs only; no reserved subtitle band" if revision>=2 else "separate selectable tracks, not burned in", "cueCountPerLanguage": len(tl["lines"]),
              "blackSegments": black, "covers": f"{len(covers)} PNGs, 1280x720", "baselineHashes": "all selected originals unchanged"}
    result['visualRevision']=visual_revision
    result['narrationRevision']=revision
    if visual_revision>=3:
        result['atmosphere']='1957 CRT, instrument console and classroom projection screen; no chapter, series or source overlays'
        result['unchangedNarration']='v2 WAVs, selected narration manifest and both external SRTs verified by SHA256'
    if voiced:
        levels = {}
        for index, lang in enumerate(('en','zh')):
            m = subprocess.run(['ffmpeg','-hide_banner','-i',str(film),'-map',f'0:a:{index}','-af','loudnorm=I=-16:TP=-1:LRA=7:print_format=json','-f','null','-'],capture_output=True,text=True,check=True)
            a=m.stderr.rfind('{');b=m.stderr.rfind('}')+1
            measured=json.loads(m.stderr[a:b]);levels[lang]=measured
            assert abs(float(measured['input_i'])+16)<.5,(lang,measured)
            assert float(measured['input_tp'])<0,(lang,measured)
        result['audioLoudness']=levels
    (delivery / 'verification.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
