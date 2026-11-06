"""Build common bilingual timelines from the owner's selected ORIGINAL race.

No benchmark or model call is made here. scripts/perceptron-race/reruns is never read.
"""
from pathlib import Path
import hashlib
import importlib.util
import json
import math
import re
import textwrap
import sys

ROOT = Path(__file__).resolve().parents[2]
DIR = ROOT / "public/family-ai-lab-01"
DOC = ROOT / "docs/family-ai-lab-01"
FPS = 30


def load(name):
    return json.loads((ROOT / "scripts/perceptron-race/results" / (name + ".json")).read_text())


def numbers():
    x, claude, astra, qwen = (load(n) for n in ("perceptron-js", "claude-fable", "astra-low", "qwen-fast"))
    assert (x["n"], x["right"], x["training"]["pictures"]) == (10, 10, 419)
    return {
        "x_us": f'{x["median_seconds"] * 1e6:.2f}',
        "x_seconds": f'{x["median_seconds"]:.8f}',
        "test_n_zh": "十", "test_n_en": "ten",
        "claude_seconds": f'{claude["median_model"]:.2f}',
        "astra_seconds": f'{astra["median_model"]:.2f}',
        "qwen_seconds": f'{qwen["median_model"]:.2f}',
        "claude_million_zh": str(round(claude["median_model"] / x["median_seconds"] / 1e6) * 100),
        "claude_million_en": str(round(claude["median_model"] / x["median_seconds"] / 1e6)),
        "astra_ten_million_zh": str(math.floor(astra["median_model"] / x["median_seconds"] / 1e7) * 1000),
        "astra_ten_million_en": str(math.floor(astra["median_model"] / x["median_seconds"] / 1e7) * 10),
        "train_n": x["training"]["pictures"],
        "pixel_n": len(import_pictures().TEST[0][1]),
        "qwen_right_zh": {5: "五"}[qwen["right"]],
        "qwen_right_en": {5: "five"}[qwen["right"]],
    }


def import_pictures():
    spec = importlib.util.spec_from_file_location("race_pictures", ROOT / "scripts/perceptron-race/pictures.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def reading_seconds(text, lang):
    if lang == "zh":
        units = len(re.findall(r"[\u3400-\u9fff]", text))
        units += sum(max(2, len(w) * 0.35) for w in re.findall(r"[A-Za-z]+", text))
        units += len(re.findall(r"[0-9]", text))
        return max(2.0, units / 3.5)
    return max(2.0, len(re.findall(r"\b[\w]+(?:[.’'-][\w]+)*\b", text)) / 2.6)


def timestamp(seconds):
    ms = round(seconds * 1000)
    return f"{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}"


def caption_text(text, lang):
    return "\n".join(textwrap.wrap(text, width=58 if lang == "en" else 36, break_long_words=True, break_on_hyphens=False))


def ass_time(frame):
    centi = round(frame / FPS * 100)
    return f"{centi//360000}:{centi//6000%60:02}:{centi//100%60:02}.{centi%100:02}"


def main():
    DIR.mkdir(parents=True, exist_ok=True)
    DOC.mkdir(parents=True, exist_ok=True)
    values = numbers()
    source = json.loads((Path(__file__).parent / "script.json").read_text())
    revision = source.get('revision',1)
    narrated = "--voiced" in sys.argv
    narration = json.loads((DIR / "narration.json").read_text()) if narrated else None
    titles = {
        "zh": ["同一张图", "速度标题卡", "纸和笔", "你来当神经元", "网页实验室", "揭晓 X", "后来发生了什么", "从餐桌开始"],
        "en": ["The same picture", "The speed headline", "Paper and pencil", "Be a neuron", "The browser lab", "Meet X", "What came next", "Start at the table"],
    }
    frame, counts, lines = 0, {}, []
    for scene, visual, zh, en in source["lines"]:
        counts[scene] = counts.get(scene, 0) + 1
        text = {"zh": zh.format(**values), "en": en.format(**values)}
        spoken = max(math.ceil(reading_seconds(t, lang) * FPS) for lang, t in text.items())
        line_id = f"fa01-{scene:02}-{counts[scene]:02}"
        if narration:
            for lang in ("en", "zh"):
                assert narration[lang][line_id]["caption"] == text[lang], (lang, line_id, "stale narration")
            spoken = max(math.ceil(narration[lang][line_id]["seconds"] * FPS) for lang in ("en", "zh")) + 3
        if visual == 'time-travel-intro':
            spoken = max(spoken, round(10.8*FPS))
        if visual == "race-run":
            spoken = max(spoken, math.ceil((load("astra-low")["median_model"] + 1.5) * FPS))
        duration = spoken + round(0.4 * FPS)
        lines.append({"id": line_id, "scene": scene, "visual": visual,
                      "text": text, "from": frame, "duration": duration, "captionFrames": spoken})
        frame += duration
    lines[-1]["duration"] += 5 * FPS
    lines[-1]["captionFrames"] += 5 * FPS
    frame += 5 * FPS
    tl = {"fps": FPS, "revision":revision, "visualRevision":source.get('visualRevision',revision), "defaultLanguage": "en", "durationInFrames": frame, "lines": lines,
          "titles": titles["en"], "values": values,
          "dataSelection": "original full round, explicitly retained by owner; no reruns",
          "delivery": "one picture, English default, independent Chinese audio/subtitles" if narrated else "one picture, English labels, English default captions, separate Chinese captions; audio deferred",
          "narrated": narrated}
    (DIR / "timeline.json").write_text(json.dumps(tl, ensure_ascii=False, indent=2) + "\n")
    for lang in ("zh", "en"):
        md = [f"# {'家庭AI实验室 1 · 中文审核稿' if lang == 'zh' else 'Family AI Lab 1 · English review script'}", "",
              ("Louise 配音稿，共用画面，中文独立音轨。实验数字仅取原始 results/*.json。" if narrated else "无配音审核版。实验数字仅取原始 results/*.json；复测不入片。") if lang == "zh" else ("Louise narration script. One common picture, English default audio. Original experiment values only." if narrated else "Unvoiced review. Experiment values come only from the original results/*.json, excluding reruns."), ""]
        for scene in range(1, 9):
            md += [f"## S{scene} · {titles[lang][scene-1]}", ""]
            md += [f"- **{line['id']}** {line['text'][lang]}" for line in lines if line["scene"] == scene]
            md += [""]
        (DOC / f"{lang}-script.md").write_text("\n".join(md))
        (DIR / f"review.{lang}.srt").write_text("\n\n".join(
            f"{i+1}\n{timestamp(line['from']/FPS)} --> {timestamp((line['from']+line['captionFrames'])/FPS)}\n{caption_text(line['text'][lang],lang)}"
            for i, line in enumerate(lines)) + "\n")
        header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 0
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,FONTNAME,42,&H00F3FAFF,&H00F3FAFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,2,100,100,35,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""".replace("FONTNAME", "Arial" if lang == "en" else "Hiragino Sans GB")
        events = []
        for line in lines:
            text = caption_text(line["text"][lang], lang).replace("\n", r"\N")
            events.append(f"Dialogue: 0,{ass_time(line['from'])},{ass_time(line['from']+line['captionFrames'])},Default,,0,0,0,,{text}")
        (DIR / f"review.{lang}.ass").write_text(header + "\n".join(events) + "\n")
        print(lang, f"{frame/FPS:.1f}s", f"{frame/FPS/60:.2f}min", len(lines), "aligned lines")
        for s in range(1, 9):
            print(" S", s, round(sum(l["duration"] for l in lines if l["scene"] == s) / FPS, 1))
    pic = import_pictures().TEST[0]
    (DIR / "picture.json").write_text(json.dumps({"name": pic[0], "pixels": pic[1], "answer": pic[2]}))
    hashes = {name: hashlib.sha256((ROOT / "scripts/perceptron-race/results" / (name + ".json")).read_bytes()).hexdigest()
              for name in ("perceptron-js", "claude-fable", "astra-low", "qwen-fast")}
    (DOC / "selected-data.json").write_text(json.dumps({"selection": "original full round", "ownerConfirmed": True,
        "noMoreBenchmarkCalls": True, "sha256": hashes, "derived": values,
        "delivery": "one common English-label picture", "defaultLanguage": "en",
        "audio": "Louise/en default; Louise/zh independent; speed 1.1" if narrated else "deferred until review approved; future English default and separate Chinese track",
        "subtitles": "external SRT files only; no embedded subtitle tracks or subtitle band" if revision>=2 else "independent English default and Simplified Chinese tracks"}, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
