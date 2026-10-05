"""Re-voice single lines until Whisper hears the words that matter.

Run from lucas-academy-media with its env:
  .conda/bin/python ../lucas-academy-video/scripts/whole-person-01/retake.py zh 'wp02-05=这里&工作' 'wp01-12=mat+h|mathieu'

Each job is ID=CHECK, where CHECK is regexes joined by '&' (all must match the
lower-cased transcript). Up to TRIES fresh takes; the first that passes replaces
the line's WAV, otherwise the existing take is kept and reported.
"""
import re
import shutil
import sys
from pathlib import Path

import whisper

sys.path.insert(0, "src")
sys.path.insert(0, str(Path(__file__).parent))
import narrate  # noqa: E402  (OUT, SCRIPT, SPOKEN, ZH_SUBSTITUTIONS)
from lucas_media.cosyvoice_engine import CosyVoiceEngine  # noqa: E402
from lucas_media.joke import DEFAULT_PEAK_DBFS, add_peak_headroom, save_wav  # noqa: E402

TRIES = 6
PROMPT = {"zh": "以下是普通话的句子，使用简体中文。", "en": None}


def main(lang: str, jobs: list[str]) -> None:
    import json
    script = json.load(open(narrate.SCRIPT.format(lang=lang)))
    text = {l["id"]: l["text"] for l in script["lines"]}
    out = Path(narrate.OUT[lang])
    model = whisper.load_model("small", device="cpu")
    engine = CosyVoiceEngine(script["voice"])
    kwargs = {"mode": script["mode"], "instruction": script["instruction"]} if "mode" in script else {}

    def heard(path: Path) -> str:
        return model.transcribe(str(path), language=lang, initial_prompt=PROMPT[lang], fp16=False)["text"]

    for job in jobs:
        line_id, check = job.split("=", 1)
        patterns = [re.compile(p, re.I) for p in check.split("&")]
        ok = lambda h: all(p.search(h) for p in patterns)  # noqa: E731
        current = out / f"{line_id}.wav"
        if current.exists() and ok(h := heard(current)):
            print(f"fine {line_id}: {h}", flush=True)
            continue
        spoken = narrate.SPOKEN[lang].get(line_id, text[line_id])
        if lang == "zh":
            for a, b in narrate.ZH_SUBSTITUTIONS.items():
                spoken = spoken.replace(a, b)
        for k in range(TRIES):
            speech, rate, _ = engine.synthesize(spoken, target_language=lang, speed=script.get("speed", 1.0), **kwargs)
            tmp = out / f"{line_id}.try.wav"
            save_wav(tmp, add_peak_headroom(speech, peak_dbfs=DEFAULT_PEAK_DBFS), rate)
            h = heard(tmp)
            print(f"try {k} {line_id}: {h}", flush=True)
            if ok(h):
                shutil.move(tmp, current)
                print(f"kept {line_id}", flush=True)
                break
            tmp.unlink()
        else:
            print(f"KEEP-ORIGINAL {line_id}", flush=True)
    print(f"[{lang}] retakes done", flush=True)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:])
