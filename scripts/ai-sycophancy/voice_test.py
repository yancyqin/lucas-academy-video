"""Voice the 試音 lines of docs/ai-sycophancy/voice-test.md in one voice, then join them into one preview.

Run with lucas-academy-media's Python, one voice per process (memory budget: at most two at once):
  ../lucas-academy-media/.conda/bin/python scripts/ai-sycophancy/voice_test.py fangfang 1.3
  ../lucas-academy-media/.conda/bin/python scripts/ai-sycophancy/voice_test.py yancy 1.2

Takes: lucas-academy-media/outputs/<voice>/zh/ai-sycophancy-test/s<speed>/<id>.wav (existing ones are kept).
Preview: out/ai-sycophancy/voice-test/<voice>-<speed>.wav, the lines in order with 0.8 s between them.
"""
import os
import re
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parents[2]
for parent in ROOT.parents:
    if (parent / "lucas-academy-media").is_dir():
        MEDIA = parent / "lucas-academy-media"
        break
else:
    raise SystemExit("Cannot find lucas-academy-media")

TONE = {
    "基准": "请用真诚、温暖、有感情的语气，像跟朋友、跟家长聊天那样说。",
    "凝重": "请用真诚、凝重一点的语气，像在讲一段让人心疼的往事。",
    "温和": "请用温和、真诚、带着希望的语气。",
}
voice, speed = sys.argv[1], float(sys.argv[2])

lines = []
for raw in (ROOT / "docs/ai-sycophancy/voice-test.md").read_text().splitlines():
    if m := re.match(r"^(sc\d\d-\d\d) ｜(\S+)｜", raw):
        lines.append({"id": m[1], "tone": m[2]})
    elif (m := re.match(r"^\s+读 \| (.+)$", raw)) and lines:
        lines[-1]["spoken"] = m[1].strip()
assert all("spoken" in l for l in lines) and lines

out = MEDIA / f"outputs/{voice}/zh/ai-sycophancy-test/s{speed:.2f}"
out.mkdir(parents=True, exist_ok=True)
todo = [l for l in lines if not (out / f"{l['id']}.wav").exists()]
if todo:
    os.chdir(MEDIA)
    sys.path.insert(0, str(MEDIA / "src"))
    import torch  # noqa: E402

    torch.set_num_threads(int(os.environ.get("NARRATE_THREADS", "4")))
    torch.set_num_interop_threads(2)
    from lucas_media.cosyvoice_engine import CosyVoiceEngine  # noqa: E402
    from lucas_media.joke import DEFAULT_PEAK_DBFS, add_peak_headroom, save_wav  # noqa: E402

    engine = CosyVoiceEngine(MEDIA / f"profiles/{voice}/zh/profile.json")
    for n, l in enumerate(todo, 1):
        speech, rate, _ = engine.synthesize(l["spoken"], target_language="zh", mode="zero-shot-instruct",
                                            instruction=TONE[l["tone"]], speed=speed)
        save_wav(out / f"{l['id']}.wav", add_peak_headroom(speech, peak_dbfs=DEFAULT_PEAK_DBFS), rate)
        print(f"[{n}/{len(todo)}] {voice} {l['id']} {speech.shape[1] / rate:.2f}s", flush=True)

parts, rate = [], None
for l in lines:
    audio, rate = sf.read(out / f"{l['id']}.wav", dtype="float32")
    parts += [audio, np.zeros(int(0.8 * rate), dtype="float32")]
preview = ROOT / f"out/ai-sycophancy/voice-test/{voice}-{speed:.1f}.wav"
preview.parent.mkdir(parents=True, exist_ok=True)
sf.write(preview, np.concatenate(parts), rate)
print("preview", preview)
