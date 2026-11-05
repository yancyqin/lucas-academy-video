"""Copy owner curriculum and reconstruct the already-trained model for illustration.

No timing loop and no remote model call. The selected benchmark JSON stays untouched.
"""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
AI = ROOT.parent / "lucas-academy-ai"
OUT = ROOT / "public/family-ai-lab-01"


def main():
    dest = OUT / "curriculum"
    dest.mkdir(parents=True, exist_ok=True)
    inputs = []
    for name in ("heart_photo", "heart_mosaic", "heart_bits", "cat_photo", "cat_mosaic", "cat_bits", "red_apple_3d", "tomato_3d"):
        src = AI / "L1-beginner/media" / (name + ".png")
        shutil.copy2(src, dest / src.name)
        inputs.append(src)
    sheets = AI / "assets/print/how-computers-see"
    for src in sheets.iterdir():
        if src.suffix in (".jpg", ".pdf"):
            shutil.copy2(src, dest / src.name)
            inputs.append(src)
    subprocess.run(["pdftoppm", "-f", "2", "-l", "2", "-scale-to", "1600", "-png", "-singlefile",
                    str(dest / "worksheets.pdf"), str(dest / "worksheet-heart-cat")], check=True)
    # Reconstitute the training state from the existing rule, without running race()/main().
    sys.path.insert(0, str(ROOT / "scripts/perceptron-race"))
    from pictures import many_examples, TEST
    from perceptron_run import train_until_right, predict
    examples = many_examples()
    points = [0] * len(examples[0][0])
    rounds = train_until_right(points, examples)
    original = json.loads((ROOT / "scripts/perceptron-race/results/perceptron-js.json").read_text())
    assert rounds == original["training"]["rounds"]
    assert all(predict(p, points) == yes for p, yes in examples)
    assert sum(predict(p, points) == yes for _, p, yes in TEST) == original["right"]
    (OUT / "trained-model.json").write_text(json.dumps({"points": points, "rounds": rounds,
        "examples": [{"pic": p, "yes": a} for p, a in examples],
        "note": "Training-state restoration for a browser illustration only; not a timed experiment."}))
    commit = subprocess.check_output(["git", "-C", str(AI), "rev-parse", "HEAD"], text=True).strip()
    record = {"repository": str(AI), "commit": commit,
              "inputs": [{"path": str(p.relative_to(AI)), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in inputs]}
    (ROOT / "docs/family-ai-lab-01/curriculum-sources.json").write_text(json.dumps(record, indent=2) + "\n")
    print("Curriculum copied; trained model state restored; no benchmarks or LLM calls.")


if __name__ == "__main__":
    main()
