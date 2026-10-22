"""好奇新世界: the narration scripts for lucas-narrate, one per language, from docs/weekly/<ep>/zh-edit.md.

Chinese is Fangfang, English is Louise, each with the project default delivery (scripts/voice_defaults.py). The
voices read SPOKEN's respellings (shots.py); captions keep the script's words.

  python3 scripts/weekly/narration.py 001
  then: NARRATE_THREADS=8 ../lucas-academy-media/.conda/bin/python scripts/weekly/narrate.py 001 zh   (and en)
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from assets import ROOT, load_shots  # noqa: E402
from build_timeline import parse_script  # noqa: E402
from voice_defaults import line_settings  # noqa: E402

VOICE = {"zh": "fangfang/zh", "en": "louise/en"}


def main(ep: str) -> None:
    cues = parse_script(ep)
    spoken = getattr(load_shots(ep), "SPOKEN", {})
    out = ROOT / "public/weekly" / ep / "narration"
    out.mkdir(parents=True, exist_ok=True)
    for lang in ("zh", "en"):
        lines = []
        for cid, cue in cues.items():
            text = cue[lang]
            for old, new in spoken.get(lang, {}).items():
                text = text.replace(old, new)
            lines.append({"id": cid, "text": text, **line_settings(VOICE[lang])})
        path = out / f"script.{lang}.json"
        path.write_text(json.dumps({"voice": VOICE[lang], "language": lang, "lines": lines}, ensure_ascii=False, indent=1) + "\n")
        print(f"{lang}: {len(lines)} lines -> {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main(sys.argv[1])
