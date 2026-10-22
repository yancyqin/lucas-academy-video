"""Voice one language of 「法国人走上街头，出路在哪里？」 in Yancy's voice, one WAV per line; existing takes are kept.

Run with lucas-academy-media's Python:
  ../lucas-academy-media/.conda/bin/python scripts/news-education-01/narrate.py zh|en [--only id,id] [--take N]

zh: zero-shot-instruct (the reference recording's rhythm plus the section's delivery).
en: cross-lingual with the delivery instruction in CosyVoice's system slot (lucas-narrate has no such mode): the owner
picked Yancy's own voice reading English (option A, 2026-10-20) and asked for a graver opening than the first test.
"""
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for parent in ROOT.parents:
    if (parent / "lucas-academy-media").is_dir():
        MEDIA = parent / "lucas-academy-media"
        break
else:
    raise SystemExit("Cannot find lucas-academy-media")

lang = sys.argv[1]
args = sys.argv[2:]
only = set(args[args.index("--only") + 1].split(",")) if "--only" in args else None
take = args[args.index("--take") + 1] if "--take" in args else ""
OUT = MEDIA / f"outputs/yancy/{lang}/news-education-01-v1"
os.chdir(MEDIA)
sys.path.insert(0, str(MEDIA / "src"))
import torch  # noqa: E402

torch.set_num_threads(int(os.environ.get("NARRATE_THREADS", "4")))
torch.set_num_interop_threads(2)
from lucas_media.cosyvoice_engine import CosyVoiceEngine  # noqa: E402
from lucas_media.joke import DEFAULT_PEAK_DBFS, add_peak_headroom, save_wav  # noqa: E402

script = json.loads((ROOT / f"public/news-education-01/narration/{lang}.json").read_text())
OUT.mkdir(parents=True, exist_ok=True)
todo = [l for l in script["lines"] if (only is None or l["id"] in only)]
todo = [l for l in todo if take or not (OUT / f"{l['id']}.wav").exists()]
if not todo:
    print(f"[{lang}] nothing to voice")
    raise SystemExit
engine = CosyVoiceEngine(MEDIA / "profiles/yancy/zh/profile.json")
for n, line in enumerate(todo, 1):
    if lang == "zh":
        speech, rate, _ = engine.synthesize(line["text"], target_language="zh", mode="zero-shot-instruct",
                                            instruction=line["instruct"], speed=line["speed"])
    else:
        gen = engine.model.inference_cross_lingual(f"You are a helpful assistant. {line['instruct']}<|endofprompt|>" + line["text"],
                                                   str(engine.reference_audio), stream=False, speed=line["speed"])
        speech, rate = torch.cat([x["tts_speech"].cpu() for x in gen], dim=1), engine.model.sample_rate
    path = OUT / (f"{line['id']}.take{take}.wav" if take else f"{line['id']}.wav")
    save_wav(path, add_peak_headroom(speech, peak_dbfs=DEFAULT_PEAK_DBFS), rate)
    print(f"[{lang} {n}/{len(todo)}] {line['id']} {speech.shape[1] / rate:.2f}s -> {path.name}", flush=True)
(OUT / "texts.json").write_text(json.dumps({l["id"]: l["text"] for l in script["lines"]}, ensure_ascii=False, indent=1))
print(f"[{lang}] voiced", flush=True)
