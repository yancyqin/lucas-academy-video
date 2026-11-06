"""Owner-authorized Louise narration, English default and independent Chinese.

Run with ../lucas-academy-media/.conda/bin/python. At most two synthesis processes.
Existing valid takes are reused only when text and voice settings match exactly.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
MEDIA = ROOT.parent / "lucas-academy-media"
sys.path.insert(0, str(Path(__file__).parent))
from build import numbers

TONE = {
    "en": "Please speak in a warm, curious voice, like discovering something interesting together with parents and children. Clear, natural and conversational.",
    "zh": "请用亲切、好奇的语气，像和家长、孩子一起发现一件有意思的事那样说。自然聊天，清楚，不用播报腔。",
}
OPENING_TONE = {
    'en': 'Please speak with bright, playful energy and curious excitement, as if inviting a family on a time-travel adventure. Smile in your voice. Keep the words connected and natural.',
    'zh': '请用活泼、带着笑意的语气，像邀请家长和孩子一起出发探险。轻快、有好奇心，字句自然连贯，不用播报腔。',
}
EN_NUMBERS = {"0.37":"zero point three seven", "5.1":"five point one", "1957":"nineteen fifty seven", "1958":"nineteen fifty eight", "1969":"nineteen sixty nine", "1986":"nineteen eighty six", "2012":"twenty twelve", "2017":"twenty seventeen", "1949":"nineteen forty nine", "419":"four hundred and nineteen", "400":"four hundred", "10":"ten", "3":"three"}
ZH_NUMBERS = {"0.37":"零点三七", "5.1":"五点一", "1000":"一千", "419":"四百一十九", "400":"四百", "300":"三百"}


def spoken_text(text, lang):
    if lang == "en":
        text = text.replace("GPT-6-Astra", "GPT six Astra").replace("Mark I", "Mark one")
        text = re.sub(r"\bX\b", "X", text)
        for value, words in sorted(EN_NUMBERS.items(), key=lambda item: -len(item[0])):
            text = re.sub(r"(?<!\d)"+re.escape(value)+r"(?!\d)", words, text)
    else:
        for value, words in sorted(ZH_NUMBERS.items(), key=lambda item: -len(item[0])):
            text = text.replace(value, words)
        text = text.replace("GPT-6-Astra", "GPT六，Astra").replace('Claude', '克劳德')
        text = text.replace("Qwen", "千问").replace("Mark I", "马克一号")
        text = text.replace("Run one round", "运行一轮").replace("points", "分数")
        text = text.replace("X", "艾克斯")
    if re.search(r"\d", text):
        raise ValueError("Digits left in speech: " + text)
    return text


def plan(lang, speed=1.1):
    source = json.loads((ROOT / "scripts/family-ai-lab-01/script.json").read_text())
    vals = numbers()
    override_file = ROOT / 'docs/family-ai-lab-01/voice-overrides.json'
    overrides = json.loads(override_file.read_text()) if override_file.exists() else {}
    counts, result = {}, []
    for scene, visual, zh, en in source["lines"]:
        counts[scene] = counts.get(scene, 0) + 1
        caption = (en if lang == "en" else zh).format(**vals)
        line = {"id":f"fa01-{scene:02}-{counts[scene]:02}","caption":caption,"spoken":spoken_text(caption, lang),
                "voice":f"louise/{lang}","mode":"zero-shot-instruct","instruction":OPENING_TONE[lang] if source.get('revision',1)>=2 and scene<=2 else TONE[lang],"speed":speed,
                'revision':source.get('revision',1),'scene':scene}
        override = overrides.get(f'{lang}/{line["id"]}')
        if override:
            line['spoken'] = override['spoken']
            line['readingNote'] = override['reason']
        line["settingsSha256"] = hashlib.sha256(json.dumps(line, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        result.append(line)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--lang", choices=["en","zh"], required=True)
    parser.add_argument("--speed", type=float, default=1.1)
    parser.add_argument("--only")
    parser.add_argument("--take", default="")
    parser.add_argument("--plan", action="store_true")
    args = parser.parse_args()
    lines = plan(args.lang, args.speed)
    dest = MEDIA / f"outputs/louise/{args.lang}/family-ai-lab-01-v{lines[0]['revision']}/s{args.speed:.2f}"
    dest.mkdir(parents=True, exist_ok=True)
    (ROOT / f"docs/family-ai-lab-01/voice.{args.lang}.json").write_text(json.dumps(lines, ensure_ascii=False, indent=2)+"\n")
    selected = set(args.only.split(",")) if args.only else None
    todo = []
    for line in lines:
        if selected and line["id"] not in selected:
            continue
        name = line["id"] + (f".take{args.take}" if args.take else "")
        wav, meta = dest / (name+".wav"), dest / (name+".json")
        if wav.exists() and meta.exists():
            old = json.loads(meta.read_text())
            if old["settingsSha256"] != line["settingsSha256"]:
                raise RuntimeError("Changed line requires a new --take: " + name)
            continue
        todo.append((line, wav, meta))
    if args.plan:
        print(args.lang, len(todo), "takes planned:", dest)
        return
    if not todo:
        print("All takes already exist:", dest)
        return
    os.chdir(MEDIA)
    sys.path.insert(0, str(MEDIA / "src"))
    import torch
    torch.set_num_threads(int(os.environ.get("NARRATE_THREADS", "3")))
    torch.set_num_interop_threads(2)
    # The required English/Chinese FSTs are already installed. Avoid fetching
    # unrelated languages whenever the upstream normalizer repository changes.
    from modelscope import snapshot_download
    normalizer_dir = Path(snapshot_download('pengzhendong/wetext', local_files_only=True))
    for language in ('en', 'zh'):
        for filename in ('tagger.fst', 'verbalizer.fst'):
            if not (normalizer_dir / language / 'tn' / filename).is_file():
                raise FileNotFoundError(f'Missing cached text normalizer: {language}/{filename}')
    import wetext.wetext as text_frontend
    text_frontend.snapshot_download = lambda model: str(normalizer_dir)
    from lucas_media.cosyvoice_engine import CosyVoiceEngine
    from lucas_media.joke import DEFAULT_PEAK_DBFS, add_peak_headroom, save_wav
    engine = CosyVoiceEngine(MEDIA / f"profiles/louise/{args.lang}/profile.json")
    for i, (line, wav, meta) in enumerate(todo, 1):
        speech, rate, _ = engine.synthesize(line["spoken"], target_language=args.lang, mode=line["mode"],
                                           instruction=line["instruction"], speed=line["speed"])
        secs = speech.shape[1] / rate
        if secs < .5:
            raise RuntimeError("Empty or truncated synthesis: " + line["id"])
        save_wav(wav, add_peak_headroom(speech, peak_dbfs=DEFAULT_PEAK_DBFS), rate)
        meta.write_text(json.dumps({**line,"durationSeconds":secs,"sampleRate":rate},ensure_ascii=False,indent=2)+"\n")
        print(f"[{i}/{len(todo)}] {args.lang} {line['id']} {secs:.2f}s -> {wav.name}",flush=True)


if __name__ == "__main__":
    main()
