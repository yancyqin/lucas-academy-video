"""Each synthetic picture defect must land in its verdict, and the clean shots must pass untouched.

    .venv-align/bin/python scripts/qa/tests/make_picture_cases.py      # once (≈1 min)
    .venv-align/bin/python scripts/qa/tests/test_picture.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import picture  # noqa: E402
import spec as specmod  # noqa: E402

CASES = HERE.parents[2] / "out/qa/_picture_cases"
# case: (findings that must be there as (code, verdict), whether anything else non-pass is allowed)
EXPECT = {
    "clean": ([], False),
    "start_wobble": ([("picture.start_wobble", "fail")], False),
    "glitch": ([("picture.glitch", "fail")], False),
    "drift": ([("picture.drift", "unsure")], False),
    "drift_region": ([("picture.static_moved", "fail")], True),
    "freeze": ([("picture.freeze", "fail")], False),
    "black": ([("picture.black", "fail")], False),
    "black_film": ([("picture.black", "fail")], True),
    "black_planned": ([], False),
    "black_past_plan": ([("picture.black", "fail")], False),
    "hard_cut": ([], False),
    # the same defects in real MiniMax footage (made only when the source film is on this machine)
    "real_clean": ([], False),
    "real_wobble": ([("picture.start_wobble", "fail")], False),
    "real_drift": ([("picture.drift", "unsure")], False),
    "real_glitch": ([("picture.glitch", "fail")], False),
    "real_freeze": ([("picture.freeze", "fail")], False),
}
OPTIONAL = {k for k in EXPECT if k.startswith("real_")}
WHEN = {"start_wobble": 3.0, "glitch": 4.0, "freeze": 3.0, "black": 4.0, "black_past_plan": 4.0,
        "real_wobble": 0.0, "real_glitch": 6.0, "real_freeze": 4.0}


def run(name: str) -> list[str]:
    video = CASES / f"{name}.mp4"
    if not video.exists():
        if name in OPTIONAL:
            print(f"skip {name} (no real footage on this machine)")
            return []
        return [f"{video} missing: run make_picture_cases.py"]
    spec = specmod.normalise(json.loads((CASES / f"{name}.spec.json").read_text()))
    info, found = picture.check(video, spec, None)
    must, others_ok = EXPECT[name]
    errors = []
    got = {(f["code"], f["verdict"]) for f in found}
    for m in must:
        if m not in got:
            errors.append(f"{name}: expected {m}, got {sorted(got) or 'nothing'}")
    if not others_ok:
        extra = [f for f in found if (f["code"], f["verdict"]) not in must]
        if extra:
            errors.append(f"{name}: unexpected " + "; ".join(f"{f['code']}/{f['verdict']} @{f.get('t0')} {f['detail']}" for f in extra))
    if name in WHEN:
        hits = [f for f in found if (f["code"], f["verdict"]) in must]
        if hits and not any(abs(f["t0"] - WHEN[name]) < 0.5 for f in hits):
            errors.append(f"{name}: found at {[f['t0'] for f in hits]}, expected near {WHEN[name]} s")
    print(f"{'ok  ' if not errors else 'FAIL'} {name:<13} " + ", ".join(f"{f['code']}/{f['verdict']}@{f['t0']:.2f}" for f in found)
          + f"   segs={[(s['t'], s.get('shake'), s.get('head_rms')) for s in info['segments']]}", flush=True)
    return errors


def test_all():
    errors = [e for name in EXPECT for e in run(name)]
    assert not errors, "\n".join(errors)


if __name__ == "__main__":
    errs = [e for name in (sys.argv[1:] or EXPECT) for e in run(name)]
    print("\n".join(errs) if errs else "all picture cases behave")
    sys.exit(1 if errs else 0)
