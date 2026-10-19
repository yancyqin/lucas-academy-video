"""Re-voice lines the Whisper check doubts, in a few spellings, and keep the take that sounds right.

    ../lucas-academy-media/.conda/bin/python scripts/fun-economics-02/retake.py zh [sc05-01 ...]
    ../lucas-academy-media/.conda/bin/python scripts/fun-economics-02/retake.py --install zh sc05-01=2

CosyVoice gives the same take for the same text, so each candidate is the spoken text with different punctuation
(captions never change). All candidates are voiced in one run into lucas-academy-media
outputs/<voice>/<lang>/fun-economics-02-retakes/<id>-v<k>.wav (lucas-narrate turns the dot of <id>.v<k> into a dash) and judged with Whisper medium: the free transcript
against the line, and forced decoding (episode 3's force.py), where the line as it should sound must beat each
wrong reading by RIGHT_MARGIN nats. The original take is judged the same way, as v0.
--install copies the chosen take over the one in fun-economics-02-v1 (the old one moves to v1/replaced/) and prints
the RETAKE entry for narration.py, so the cue's spoken text matches the take.
"""
import difflib
import json
import os
import shutil
import subprocess
import sys
import tempfile

from common import FILM, OUT, PUB, ROOT, VOICES, base, media

sys.path.insert(0, str(ROOT / "scripts/fun-informatics-03"))
import force  # noqa: E402

RIGHT_MARGIN = 1.0
REPORT = OUT / "retakes.json"
# id: punctuation variants of the spoken text, the line as it should sound, and readings it must beat.
RETAKES = {
    "zh": {
        "sc05-01": {  # 也 dropped and Mary heard as Nari, by both models
            "variants": [
                "写作业，也一样。Mary的数学作业：一盒铅笔有八支，七盒平均分给十四个同学，每人分到几支？",
                "写作业也一样！Mary的数学作业：一盒铅笔有八支，七盒平均分给十四个同学，每人分到几支？",
                "写作业也一样。Mary 的数学作业，一盒铅笔有八支，七盒平均分给十四个同学，每人分到几支？",
            ],
            "right": "写作业也一样。Mary的数学作业，一盒铅笔有八支，七盒平均分给十四个同学，每人分到几支？",
            "wrong": ["写作业一样。Mary的数学作业，一盒铅笔有八支，七盒平均分给十四个同学，每人分到几支？",
                      "写作业也一样。Nari的数学作业，一盒铅笔有八支，七盒平均分给十四个同学，每人分到几支？"],
        },
        "sc04-04": {  # 积木 heard as 金木 / 筋目
            "variants": [
                "而且，拆了，积木一块也没少；第二次拼，还会快很多，因为你已经知道怎么拼了。",
                "而且拆了：积木，一块也没少；第二次拼，还会快很多，因为你已经知道怎么拼了。",
                "而且拆了，积木一块也没少。第二次拼，还会快很多；因为你已经知道怎么拼了。",
            ],
            "right": "而且拆了，积木一块也没少，第二次拼，还会快很多，因为你已经知道怎么拼了。",
            "wrong": ["而且拆了，金木一块也没少，第二次拼，还会快很多，因为你已经知道怎么拼了。"],
        },
        "sc06-01": {  # 拼好 heard as 平好 by both models
            "variants": [
                "拼好的乐高，写了一半的作业，为什么这么舍不得？",
                "拼好的乐高；写了一半的作业：为什么，这么舍不得？",
                "「拼好」的乐高、写了一半的作业，为什么这么舍不得？",
            ],
            "right": "拼好的乐高，写了一半的作业，为什么这么舍不得？",
            "wrong": ["平好的乐高，写了一半的作业，为什么这么舍不得？"],
        },
    },
    "en": {
        "sc03-03": {  # "won't move" heard as "will move" (the meaning flips): the script now says "will not"
            "variants": [
                "Three years of fees and time: keep learning, and you don't get them back; stop, and you don't get them back either. They weigh the same on both paths, like equal weights on both sides of a scale; the scale will not move an inch because of them. So they cannot help us choose.",
                "Three years of fees and time: keep learning, and you don't get them back; stop, and you don't get them back either. They weigh the same on both paths, like equal weights on both sides of a scale. The scale will not move an inch because of them. So they cannot help us choose.",
                "Three years of fees and time: keep learning, and you don't get them back; stop, and you don't get them back either. They weigh the same on both paths, like equal weights on both sides of a scale; the scale will NOT move an inch, because of them. So they cannot help us choose.",
            ],
            "right": "Three years of fees and time: keep learning, and you don't get them back; stop, and you don't get them back either. They weigh the same on both paths, like equal weights on both sides of a scale; the scale will not move an inch because of them. So they cannot help us choose.",
            "wrong": ["Three years of fees and time: keep learning, and you don't get them back; stop, and you don't get them back either. They weigh the same on both paths, like equal weights on both sides of a scale; the scale will move an inch because of them. So they cannot help us choose."],
        },
        "sc05-06": {  # "wrong steps" heard as "round steps"
            "variants": [
                "And the wrong steps weren't wasted, either. Next time, Mary will think the first step through.",
                "And the wrong steps... weren't wasted either: next time, Mary will think the first step through.",
                "And the wrong steps weren't wasted either! Next time, Mary will think the first step through.",
            ],
            "right": "And the wrong steps weren't wasted either: next time, Mary will think the first step through.",
            "wrong": ["And the round steps weren't wasted either: next time, Mary will think the first step through."],
        },
        "sc04-02": {  # "detour" close to "deter", "brick" heard as "break" by medium
            "variants": [
                "Take it apart and rebuild? No way, that's a whole afternoon of building. So you try to patch it: a brick here; a detour there; and the more you patch, the harder it gets.",
                "Take it apart and rebuild? No way: that's a whole afternoon of building! So you try to patch it. A brick here, a detour there, and the more you patch, the harder it gets.",
                "Take it apart and rebuild? No way, that's a whole afternoon of building. So you try to patch it... a brick here, a detour there... and the more you patch, the harder it gets.",
            ],
            "right": "Take it apart and rebuild? No way, that's a whole afternoon of building. So you try to patch it: a brick here, a detour there, and the more you patch, the harder it gets.",
            "wrong": ["Take it apart and rebuild? No way, that's a whole afternoon of building. So you try to patch it: a brick here, a deter there, and the more you patch, the harder it gets.",
                      "Take it apart and rebuild? No way, that's a whole afternoon of building. So you try to patch it: a break here, a detour there, and the more you patch, the harder it gets."],
        },
        "sc08-02": {  # the small model stops at the pause; "gain to me" heard as "gained to me"
            "variants": [
                'Yet in one letter he wrote, "I consider those things that were gain to me as a loss for Christ."',
                'Yet, in one letter, he wrote: "I consider those things that were gain, to me, as a loss for Christ."',
                'Yet in one letter he wrote: "I consider those things that were gain to me... as a loss for Christ."',
            ],
            "right": "Yet in one letter he wrote: I consider those things that were gain to me as a loss for Christ.",
            "wrong": ["Yet in one letter he wrote: I consider those things that were gained to me as a loss for Christ."],
        },
    },
}
VOICE = {"narrator": ("louise", "1.0"), "mary": ("eunice", "1.05")}
PROMPT = {"zh": "以下是普通话的句子。", "en": None}  # as check.py: simplified characters


def spoken(lang: str, cid: str) -> dict:
    cue = next(c for c in json.loads((PUB / f"narration/cues.{lang}.json").read_text()) if c["id"] == cid)
    name = lang if cue["speaker"] == "narrator" else f"mary-{lang}"
    line = next(l for l in json.loads((PUB / f"narration/{name}.json").read_text())["lines"] if l["id"] == cid)
    return {**cue, "line": line}


def retake_dir(lang: str, speaker: str):
    return media() / f"outputs/{VOICE[speaker][0]}/{lang}/{FILM}-retakes"


def voice(lang: str, ids: list) -> None:
    """Every variant of every id in one run, so the model loads once."""
    by_speaker = {}
    for cid in ids:
        cue = spoken(lang, cid)
        for k, text in enumerate(RETAKES[lang][cid]["variants"], 1):
            if not (retake_dir(lang, cue["speaker"]) / f"{cid}-v{k}.wav").exists():
                by_speaker.setdefault(cue["speaker"], []).append({**cue["line"], "id": f"{cid}.v{k}", "text": text})
    for speaker, lines in by_speaker.items():
        out = retake_dir(lang, speaker)
        out.mkdir(parents=True, exist_ok=True)
        profile = f"{VOICE[speaker][0]}/{'en' if speaker == 'mary' else lang}"
        with tempfile.TemporaryDirectory() as tmp:
            batch = os.path.join(tmp, "retakes.json")
            with open(batch, "w") as f:
                json.dump({"voice": profile, "language": lang, "lines": lines}, f, ensure_ascii=False)
            env = {**os.environ, "OMP_NUM_THREADS": os.environ.get("NARRATE_THREADS", "4")}
            subprocess.run([str(media() / ".conda/bin/lucas-narrate"), batch, "--profile", profile, "--language", lang,
                            "--speed", VOICE[speaker][1], "--output-dir", str(out)], cwd=media(), env=env, check=True)


def main() -> None:
    args = sys.argv[1:]
    if args[0] == "--install":
        lang = args[1]
        for choice in args[2:]:
            cid, k = choice.split("=")
            cue = spoken(lang, cid)
            takes = VOICES[lang][cue["speaker"]]
            (takes / "replaced").mkdir(exist_ok=True)
            if not (takes / "replaced" / f"{cid}.wav").exists():
                shutil.copy(takes / f"{cid}.wav", takes / "replaced" / f"{cid}.wav")
            shutil.copy(retake_dir(lang, cue["speaker"]) / f"{cid}-v{k}.wav", takes / f"{cid}.wav")
            new = RETAKES[lang][cid]["variants"][int(k) - 1]
            print(f'{lang} {cid}: installed v{k}. narration.py RETAKE["{lang}"]["{cid}"] = ({cue["line"]["text"]!r}, {new!r})')
        return
    lang, ids = args[0], args[1:] or list(RETAKES[args[0]])
    voice(lang, ids)
    check = base("check")
    check.LANG = lang
    import whisper
    model = whisper.load_model("medium", device="cpu")
    force._model = model
    report = json.loads(REPORT.read_text()) if REPORT.exists() else {}
    for cid in ids:
        spec = RETAKES[lang][cid]
        cue = spoken(lang, cid)
        candidates = [(0, VOICES[lang][cue["speaker"]] / f"{cid}.wav", cue["line"]["text"])]
        candidates += [(k, retake_dir(lang, cue["speaker"]) / f"{cid}-v{k}.wav", t) for k, t in enumerate(spec["variants"], 1)]
        results = []
        for k, path, text in candidates:
            heard = model.transcribe(str(path), language=lang, initial_prompt=PROMPT[lang], condition_on_previous_text=False)["text"].strip()
            score = difflib.SequenceMatcher(None, check.norm(spec["right"]), check.norm(heard)).ratio()
            ranked = force.scores(lang, path, [spec["right"], *spec["wrong"]])
            right = next(lp for lp, t in ranked if t == spec["right"])
            margin = right - max(lp for lp, t in ranked if t != spec["right"])
            ok = score >= 0.85 and margin >= RIGHT_MARGIN
            results.append({"v": k, "text": text, "heard": heard, "score": round(score, 3), "margin": round(margin, 2), "ok": ok})
            print(f"{cid} v{k} {'OK ' if ok else '   '}score {score:.2f} margin {margin:+.2f}  {heard}", flush=True)
        report.setdefault(lang, {})[cid] = results
        on_disk = json.loads(REPORT.read_text()) if REPORT.exists() else {}
        on_disk.setdefault(lang, {})[cid] = results
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(json.dumps(on_disk, ensure_ascii=False, indent=1) + "\n")


if __name__ == "__main__":
    main()
