"""Join each voice-test variant's ten lines into one listenable MP3, Whisper each line, report pace."""
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
HERE = REPO / "out/leaf-truck"   # takes, voice tests and checks (git-ignored)
RATE = 24000
LINE = re.compile(r"^- (lf0[12]-\d\d) \| (.+)$")


def script(lang):
    return {m[1]: re.sub(r"【[^】]*】", "", m[2]).strip()
            for raw in (REPO / f"docs/leaf-truck/{lang}-draft.md").read_text().splitlines() if (m := LINE.match(raw))}


def load(path):
    pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-ac", "1", "-ar", str(RATE), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    x = np.frombuffer(pcm, np.float32)
    frames = x[:len(x) // 240 * 240].reshape(-1, 240)
    loud = np.flatnonzero(np.sqrt((frames ** 2).mean(axis=1)) > 10 ** (-40 / 20))
    # start at the first 0.1 s run of speech (skips leading clicks), end 0.15 s after the last
    start = next((i for i in loud if all(j in set(loud) for j in range(i, i + 10))), loud[0])
    return x[max(0, start * 240 - 1200):min(len(x), (loud[-1] + 1) * 240 + 3600)]


def main():
    import whisper
    model = whisper.load_model("medium")
    report = {}
    for variant in sorted(p.name for p in (HERE / "voice-test").iterdir() if p.is_dir()):
        lang = variant.split("-")[1]
        text = script(lang)
        parts, rows = [np.zeros(int(.4 * RATE), np.float32)], []
        for key, line in text.items():
            clip = load(HERE / "voice-test" / variant / f"{key}.wav")
            heard = model.transcribe(clip[::1] if RATE == 16000 else np.interp(np.arange(0, len(clip), 1.5), np.arange(len(clip)), clip).astype(np.float32),
                                     language=lang, fp16=False,
                                     initial_prompt="以下是普通话的句子。" if lang == "zh" else None)["text"].strip()
            gap = 1.2 if line.rstrip("」”\"'").endswith(("？", "?")) else (.9 if key.endswith("05") else .45)
            parts += [clip, np.zeros(int(gap * RATE), np.float32)]
            units = len(re.sub(r"[^\w]", "", line)) if lang == "zh" else len(line.split())
            rows.append({"id": key, "seconds": round(len(clip) / RATE, 2), "rate": round(units / (len(clip) / RATE), 2),
                         "script": line, "heard": heard})
            print(variant, key, rows[-1]["rate"], "|", heard, flush=True)
        pcm = np.concatenate(parts)
        pcm = pcm / max(1e-6, np.abs(pcm).max()) * 0.85
        out = HERE / f"voice-test-{variant}.mp3"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(RATE), "-ac", "1", "-i", "-",
                        "-af", "loudnorm=I=-16:TP=-1.5:LRA=9", "-ar", "44100", "-b:a", "160k", str(out)],
                       input=pcm.astype(np.float32).tobytes(), check=True)
        report[variant] = {"seconds": round(len(pcm) / RATE, 1), "median_rate": float(np.median([r["rate"] for r in rows])),
                           "lines": rows}
        print(variant, "->", out.name, report[variant]["seconds"], "s", flush=True)
    (HERE / "voice-test.json").write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n")


if __name__ == "__main__":
    main()
