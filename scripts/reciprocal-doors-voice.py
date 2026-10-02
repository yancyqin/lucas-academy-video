"""Keep the Language Bridge voice script, the film script and the narration in step.

    python3 scripts/reciprocal-doors-voice.py md         # json -> docs/…VOICE-SCRIPT.md (the review copy)
    python3 scripts/reciprocal-doors-voice.py apply-md   # edited md -> json (spoken text, tone, speed, pause)
    python3 scripts/reciprocal-doors-voice.py narration  # json -> lucas-academy-media scripts, drop stale wavs

Subtitles always come from the approved `zh` / `en` text. What is *spoken* is
`say` (the same words, plus <strong> emphasis and punctuation), read at
`speed` in `tone`, after `pause` seconds of silence.

`narration` compares each line's text, instruct, mode and speed with the script
it wrote last time and deletes only the narration files whose line changed, so
the next lucas-narrate run regenerates exactly those lines.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "src/scripts/reciprocal-doors.json"
VOICE_MD = ROOT / "docs/RECIPROCAL-DOORS-VOICE-SCRIPT.md"
# Chinese speeds from reciprocal-doors-pace.py: each line near the film's median
# speaking rate (applied on top of the one film style).
PACE = ROOT / "src/scripts/reciprocal-doors.pace.zh.json"
MEDIA = ROOT.parent / "lucas-academy-media"

HAPPY = "请非常开心地说一句话。"
# tone label -> how CosyVoice is asked for it
TONES: dict[str, dict] = {
    "默认": {},
    # Tone lab, 2026-09-30 (three lines per language, CAM++ similarity + pitch sd):
    # zh: the instruction in the zero-shot system slot kept fangfang's voice
    #     (0.70–0.83) and moved the pitch at least as much as text alone;
    # en: the same trick made louise *flatter* (pitch sd 2.5–3.2 vs 3.5–4.5 for
    #     text alone), so English brightness comes from punctuation and emphasis only.
    "亮": {"zh": {"instruct": HAPPY, "mode": "zero-shot-instruct"}, "en": {}},
    # instruct2: stronger, but loses the speaker's prosody (similarity ~0.6).
    "开心": {"instruct": HAPPY, "mode": "instruct"},
    "轻柔": {"instruct": "Please say a sentence in a very soft voice.", "mode": "instruct"},
}
DEFAULT_SPEED = 0.9
# English is read in ONE style for the whole film -- the Van Gogh video's
# (lucas-academy-media/data/scripts/vg-why-paint-them/en-edit.md): the owner
# asked for it on 2026-10-01. It replaces the per-line English speeds and tones;
# taught phrases (demo parts) keep their slow, plain reading.
EN_FILM_STYLE = {
    "instruct": "Please speak in a lively, warm voice, like telling a story to children.",
    "mode": "zero-shot-instruct",
    "speed": 1.0,
}
# Chinese likewise, once the films were separate (owner, 2026-10-01: per-line
# speeds fitted to the English and nine instructed lines made the Chinese
# "忽快忽慢"). The Van Gogh video's Chinese style, one reading for the whole film.
ZH_FILM_STYLE = {
    "instruct": "请用活泼、亲切的语气，像给孩子讲故事一样说。",
    "mode": "zero-shot-instruct",
    "speed": 1.0,
}
FILM_STYLE = {"zh": ZH_FILM_STYLE, "en": EN_FILM_STYLE}
# Pronunciation fixes, spoken text only (subtitles keep the characters): CosyVoice3
# takes pinyin tokens in place of a character, e.g. [d][ǎo]. In the lively style
# 杯子倒了 kept coming out dào ("到了"), four takes in a row.
PRONOUNCE = {
    ("zh", "rd06-01"): {"倒": "[d][ǎo]"},
    ("zh", "rd09-02"): {"讲": "[j][iǎng]"},  # came out 扬 / 念 four takes in a row
}
# (track, spoken language) -> (media script, narration folder)
OUTPUTS = {
    ("zh", "zh"): ("reciprocal-doors-zh", "fangfang/zh"),
    ("zh", "en"): ("reciprocal-doors-zh-demo-en", "fangfang/zh"),
    ("en", "en"): ("reciprocal-doors-en", "louise/en"),
    ("en", "zh"): ("reciprocal-doors-en-demo-zh", "louise/en"),
}
TITLES = {
    "rd01": "听懂了，读起来却很难", "rd02": "多开一个入口", "rd03": "我们想到双语课堂",
    "rd04": "两个孩子，两扇门", "rd05": "共同的渠道：先一起看见", "rd06": "一次互教，可以怎样发生？",
    "rd07": "文字、声音、图画，各有用处", "rd08": "学新的，也让原来的继续长",
    "rd09": "这条渠道，也可以连接两代人", "rd10": "结尾",
}


def load() -> dict:
    return json.loads(SOURCE.read_text(encoding="utf-8"))


def save(source: dict) -> None:
    SOURCE.write_text(json.dumps(source, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def words(text: str, lang: str) -> str:
    text = re.sub(r"</?strong>", "", text).replace("’", "'")
    if lang == "zh":
        return re.sub(r"[^一-鿿A-Za-z']", "", text)
    return " ".join(re.sub(r"[^a-z' ]", " ", text.lower()).split())


def write_md() -> None:
    source = load()
    lines = [
        "# 语言的桥 · 配音演绎稿（中英）",
        "",
        "这是**怎么读**的稿子；字幕永远用 issue 里确认的原文，这里的改动不会动字幕。",
        "改完告诉我，我运行 `apply-md` 同步，只重新生成改过的句子。",
        "",
        "- `<strong>词</strong>`：强调。已确认会作为特殊标记送进模型；效果偏细微，所以只放在真正的对比词、关键词上。",
        "- 只能加标点、不能改字：`……` 停一下、`！` 提气、`？` 上扬、加 `，` 断句。脚本会逐句核对读的字和字幕一致。",
        "- `语气`：`默认`＝本人原来的朗读语调；`亮`＝更有起伏、更有精神的高点句（中文用混合做法，保留本人语调，声纹相似度 0.70–0.83；"
        "英文实测混合做法反而更平，所以英文的“亮”只靠 `!`、`...` 和重音）；"
        "`开心`／`轻柔`＝instruct 模式，效果更强，但声音不太像本人（相似度约 0.6），不建议使用。",
        "- `语速`：0.82 开场和最重的句子 · 0.85 分量重 · 0.9 基准 · 0.95 轻快。",
        "- `停顿`：这句之前留几秒安静（默认句间 0.45 秒，场景开头 0.7 秒）。",
        "- 每句先写中文，下一行 `en |` 是对应的英文，重音跟中文对齐。",
        f"- **两支片子都是全片一种读法**（同梵高那期，2026-10-01 定）：中文 `{ZH_FILM_STYLE['mode']}`「{ZH_FILM_STYLE['instruct']}」语速 {ZH_FILM_STYLE['speed']:g}；"
        f"英文「{EN_FILM_STYLE['instruct']}」语速 {EN_FILM_STYLE['speed']:g}。"
        "下面每句的 `语气` / `语速` 标注已不再使用（逐句切换会忽快忽慢）；强调和标点照样生效。示范句（我来帮你 / Let me help you）保持慢速、平读。",
        "- 两支独立视频：中文版用中文时间轴，英文版用英文时间轴（停顿设置两版相同）。",
        "",
    ]
    for segment in source["segments"]:
        lines += [f"## {segment['id'].upper()} · {TITLES[segment['id']]}", ""]
        for chunk in segment["chunks"]:
            attrs = []
            if chunk.get("tone"):
                attrs.append(f"语气 {chunk['tone']}")
            if "parts" not in chunk:
                attrs.append(f"语速 {chunk.get('speed', DEFAULT_SPEED):g}")
            if chunk.get("pause") is not None:
                attrs.append(f"停顿 {chunk['pause']:g}")
            tail = "".join(f" ｜{a}" for a in attrs)
            if "parts" in chunk:
                show = lambda track: " ＋ ".join(("[示范·慢] " if p.get("demo") else "") + p["text"] for p in chunk["parts"][track])
                lines.append(f"{chunk['id']} | {show('zh')}{tail}　（分段朗读，此行只读不改）")
                lines.append(f"     en | {show('en')}")
            else:
                say = chunk.get("say", {})
                lines.append(f"{chunk['id']} | {say.get('zh', chunk['zh'])}{tail}")
                lines.append(f"     en | {say.get('en', chunk['en'])}")
        lines.append("")
    VOICE_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {VOICE_MD.relative_to(ROOT)}")


def apply_md() -> None:
    source = load()
    chunks = {c["id"]: c for s in source["segments"] for c in s["chunks"]}
    seen: set[str] = set()
    current = None
    for raw in VOICE_MD.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if m := re.match(r"^(rd\d\d-\d\d)\s*\|\s*(.+)$", line):
            cid, rest = m.groups()
            if cid not in chunks:
                raise SystemExit(f"Unknown line id {cid}")
            seen.add(cid)
            chunk = chunks[cid]
            current = None if "parts" in chunk else chunk
            fields = [f.strip() for f in rest.split("｜")]
            spoken, attrs = fields[0], fields[1:]
            for attr in attrs:
                attr = re.sub(r"　（.*?）$", "", attr)
                key, _, value = attr.partition(" ")
                if key == "语气":
                    if value not in TONES:
                        raise SystemExit(f"{cid}: unknown tone {value!r}; use {', '.join(TONES)}")
                    chunk.pop("tone", None) if value == "默认" else chunk.__setitem__("tone", value)
                elif key == "语速":
                    chunk["speed"] = float(value)
                elif key == "停顿":
                    chunk["pause"] = float(value)
                else:
                    raise SystemExit(f"{cid}: unknown field {attr!r}")
            if current is not None:
                check(cid, spoken, chunk["zh"], "zh")
                chunk.setdefault("say", {})["zh"] = spoken
        elif m := re.match(r"^en\s*\|\s*(.+)$", line):
            if current is not None:
                check(current["id"], m.group(1).strip(), current["en"], "en")
                current.setdefault("say", {})["en"] = m.group(1).strip()
    missing = set(chunks) - seen
    if missing:
        raise SystemExit(f"Voice script is missing lines: {', '.join(sorted(missing))}")
    save(source)
    print(f"Applied {len(seen)} lines to {SOURCE.relative_to(ROOT)}")


def check(cid: str, spoken: str, subtitle: str, lang: str) -> None:
    if words(spoken, lang) != words(subtitle, lang):
        raise SystemExit(
            f"{cid} {lang}: spoken words must match the subtitle (only tags/punctuation may differ)\n"
            f"  spoken:   {words(spoken, lang)}\n  subtitle: {words(subtitle, lang)}"
        )


def narration() -> None:
    source = load()
    paced = (json.loads(PACE.read_text(encoding="utf-8")) if PACE.exists() else {}).get("speeds", {})
    out: dict[tuple[str, str], list[dict]] = {key: [] for key in OUTPUTS}
    for segment in source["segments"]:
        for chunk in segment["chunks"]:
            tone = TONES[chunk.get("tone", "默认")]
            for track in ("zh", "en"):
                style = tone.get(track, {}) if ("zh" in tone or "en" in tone) else tone
                parts = chunk.get("parts", {}).get(track) or [
                    {"text": chunk.get("say", {}).get(track, chunk[track]), "lang": track, "speed": chunk.get("speed", DEFAULT_SPEED)}
                ]
                for index, part in enumerate(parts, start=1):
                    line = {
                        "id": chunk["id"] if len(parts) == 1 else f"{chunk['id']}-p{index}",
                        "text": part["text"],
                        "speed": part.get("speed", DEFAULT_SPEED),
                    }
                    # A taught phrase keeps its plain, slow reading; tone is for narration.
                    if style and not part.get("demo"):
                        line.update(style)
                    # One reading per film: it replaces per-line tones and speeds.
                    if part["lang"] == track and not part.get("demo"):
                        line.update(FILM_STYLE[track])
                        if track == "zh" and line["id"] in paced:
                            line["speed"] = paced[line["id"]]
                    for char, tokens in PRONOUNCE.get((track, line["id"]), {}).items():
                        # `check` is what Whisper should hear: the text before the fix.
                        line.setdefault("check", line["text"])
                        line["text"] = line["text"].replace(char, tokens)
                    out[(track, part["lang"])].append(line)

    signature = lambda l: (l["text"], l.get("instruct", ""), l.get("mode", ""), l.get("speed"))
    stale = 0
    for key, lines in out.items():
        name, folder = OUTPUTS[key]
        path = MEDIA / "data/scripts" / f"{name}.json"
        before = {}
        if path.exists():
            # Scripts written before per-line speed carried none: demos were read at 0.75.
            old_speed = 0.75 if "demo" in name else DEFAULT_SPEED
            before = {l["id"]: signature({"speed": old_speed, **l}) for l in json.loads(path.read_text())["lines"]}
        for line in lines:
            if before.get(line["id"]) not in (None, signature(line)):
                wav = MEDIA / "outputs" / folder / "reciprocal-doors" / f"{line['id']}.wav"
                if wav.exists():
                    wav.unlink()
                    stale += 1
        path.write_text(json.dumps({"source": source["source"], "lines": lines}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Narration scripts written; {stale} stale narration files removed")


if __name__ == "__main__":
    {"md": write_md, "apply-md": apply_md, "narration": narration}[sys.argv[1]]()
