"""View saved original results for a genuine terminal recording. Makes no calls."""
import json
from pathlib import Path
import time

DATA = Path(__file__).resolve().parents[1] / "perceptron-race/results"
print("\033[2J\033[HORIGINAL EXPERIMENT / 2026-11-04", flush=True)
print("Saved JSON records. No benchmarks or model calls are running.\n", flush=True)
for name, command, key in [
    ("perceptron-js", "node perceptron_js.mjs", "median_seconds"),
    ("claude-fable", "claude -p / Fable 5.1", "median_model"),
    ("astra-low", "codex exec / Astra, low", "median_model"),
    ("qwen-fast", "Ollama / Qwen3 8B", "median_model"),
]:
    d = json.loads((DATA / f"{name}.json").read_text())
    print(f"{command:<28}  {d['right']:2}/{d['n']}  {d[key]:.10f} s", flush=True)
    time.sleep(0.35)
print("\nSame 10 held-out pictures / medians / original full round", flush=True)
print("Source: scripts/perceptron-race/results/*.json", flush=True)
