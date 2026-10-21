"""Re-voice flagged lines in several spellings and keep the take that sounds right (FUN-INFORMATICS-03.md §5.6).

    ../lucas-academy-media/.conda/bin/python scripts/fun-informatics-03/retake.py zh [ns00-02 ...]
    ../lucas-academy-media/.conda/bin/python scripts/fun-informatics-03/retake.py --install zh ns00-02=2

CosyVoice gives the same take for the same text, so each retry is a slightly different spoken text
(punctuation, or a one-reading homophone such as 腰 for 幺; captions never change). Every candidate is
voiced into lucas-academy-media outputs/louise/<lang>/fun-informatics-03-retakes/<id>.v<k>.wav and judged
two ways with Whisper medium:

  - the free transcript against the spoken text (check_narration.analyse): a repeated phrase or extra
    words fail it;
  - forced decoding (force.py): the line as it should sound must beat every wrong reading listed for it
    by a margin, e.g. 腰腰零 against 一一零.

--install copies the chosen candidate over the take in fun-informatics-03-v1 (the replaced take moves to
v1/replaced/) and prints the spoken text, which then goes into narration.py's SPOKEN.
"""
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MEDIA = Path("/Users/yqin/repo/playground/lucas-academy-media")
sys.path.insert(0, str(Path(__file__).parent))
import force  # noqa: E402

REPORT = ROOT / "out/fun-informatics-03/retakes.json"

# id: spoken variants to try, the reading it should have, and the wrong readings it must beat.
RETAKES = {
    "zh": {
        "ns00-02": {
            "variants": [
                "对，一、一、零。可是大人报号码的时候，常常不这么念，而是念「腰腰零」。急救电话呢？「腰二零」。",
                "对，一、一、零。可是大人报号码的时候，常常不这么念，而是念：腰、腰、零。急救电话呢？腰、二、零。",
                "对，一、一、零。可是，大人报号码的时候，常常不这么念，而是念「腰腰零」。急救电话呢？「腰二零」。",
            ],
            "right": "对，一、一、零。可是大人报号码的时候，常常不这么念，而是念腰腰零。急救电话呢？腰二零。",
            "wrong": ["对，一、一、零。可是大人报号码的时候，常常不这么念，而是念一一零。急救电话呢？一二零。"],
        },
        "ns01-03": {
            "variants": [
                "是「一」，还是「七」？嗯……不太好说吧？",
                "是「一」，还是「七」？……嗯，不太好说吧。",
                "是一，还是七？嗯，不太好说吧？",
                "是「一」？还是「七」？嗯……不太好说吧？",
            ],
            "right": "是一，还是七？嗯，不太好说吧？",
            "wrong": ["是一，还是七？不太好说吧。不太好说吧。", "是一，还是七？嗯，不太好说吧？不太好说吧。"],
        },
        "ns02-10": {
            "variants": [
                "多出来的这几笔，就是<strong>冗余</strong>。不是随便多画，是专门画那个能把它跟别的分开的地方。和「腰」、「拐」，是同一个道理。",
                "多出来的这几笔，就是冗余。不是随便多画，是专门画那个能把它跟别的分开的地方。和「腰」，「拐」，是同一个道理。",
                "多出来的这几笔，就是冗余。不是随便多画，是专门画那个，能把它跟别的分开的地方。和腰、拐，是同一个道理。",
                "多出来的这几笔，就是冗余。不是随便多画，是专门画那个能把它跟别的分开的地方。和「腰」、和「拐」，是同一个道理。",
            ],
            "right": "多出来的这几笔就是冗余。不是随便多画，是专门画那个能把它跟别的分开的地方。和腰、拐是同一个道理。",
            "wrong": ["多出来的这几笔就是冗余。不是随便多画，是专门画那个能把它跟别的分开的地方。和妖怪是同一个道理。",
                      "多出来的这几笔就是荣誉。不是随便多画，是专门画那个能把它跟别的分开的地方。和腰、拐是同一个道理。"],
        },
        "ns02-07": {
            "variants": [
                "这一轮，只画十五秒，而且时间到了，猜的人只能猜一次。",
                "这一轮只画十五秒。而且，时间到了，猜的人只能猜一次。",
                "这一轮只画十五秒；而且时间到了，猜的人，只能猜一次。",
            ],
            "right": "这一轮只画十五秒，而且时间到了，猜的人只能猜一次。",
            "wrong": ["这一轮只花十五秒，而且时间到了，猜的人只能猜一次。"],
        },
        "ns02-05": {
            # Louise's Chinese voice reads "Cashew" as Cashier or Cash; 卡舒 (kǎ shū) says it the way the children do.
            "variants": [
                "下一张也一样：「三角形？」「羊？」「一只狗？」对，是一只狗！朋友家的柯基，卡舒！",
                "下一张也一样：「三角形？」「羊？」「一只狗？」对，是一只狗，朋友家的柯基，卡舒！",
                "下一张也一样：「三角形？」「羊？」「一只狗？」对，是一只狗！朋友家的柯基：卡舒！",
            ],
            "right": "下一张也一样：三角形？羊？一只狗？对，是一只狗，朋友家的柯基，卡舒！",
            "wrong": ["下一张也一样：三角形？羊？一只狗？对，是一只狗，朋友家的科技，卡舒！"],
        },
    },
    "en": {
        "ns02-05": {
            "variants": [
                'Same with the next one: "A triangle?" "A sheep?" "A dog?" Yes, a dog: our friend\'s corgi... Cashew!',
                'Same with the next one: "A triangle?" "A sheep?" "A dog?" Yes, a dog: our friend\'s corgi, Cashew!',
                'Same with the next one: "A triangle?" "A sheep?" "A dog?" Yes, a dog. Our friend\'s corgi... Cashew!',
            ],
            "right": "Same with the next one. A triangle? A sheep? A dog? Yes, a dog. Our friend's corgi, Cashew!",
            "wrong": ["Same with the next one. A triangle? A sheep? A dog? Yes, a dog. Our friend's quirky Cashew!"],
        },
        "ns02-06": {
            "variants": [
                "Round two: twin cards! Each card has two things that look alike, like umbrella and mushroom. Everyone can see both words. The person drawing flips a coin, in secret, to pick one.",
                "Round two: twin cards. Each card has two things that look alike, like umbrella and mushroom. Everyone can see both words; the person drawing flips a coin in secret to pick one.",
                "Round two: twin cards. Each card has two things that look alike: like umbrella and mushroom. Everyone can see both words. The person drawing... flips a coin in secret to pick one.",
            ],
            "right": "Round two, twin cards. Each card has two things that look alike, like umbrella and mushroom. Everyone can see both words. The person drawing flips a coin in secret to pick one.",
            "wrong": ["Round two, twin cards. Each card has two things that look alike, like umbrella and mushroom. Everyone can see both words. The person drawn flips a coin in secret to pick one."],
        },
        "ns02-09": {
            "variants": [
                'But the drawers learned fast. Give the umbrella a thin handle, and it\'s guessed at once! Add a few tiny stars and streaks of light around the star, and everyone changes their mind: "Oh, it\'s a star in the sky!"',
                'But the drawers learned fast: give the umbrella a thin handle, and it\'s guessed, at once. Add a few tiny stars and streaks of light around the star, and everyone changes their mind: "Oh, it\'s a star in the sky!"',
                'But the drawers learned fast. Give the umbrella a thin handle and it\'s guessed at once. Add a few tiny stars, and streaks of light, around the star, and everyone changes their mind: "Oh, it\'s a star in the sky!"',
            ],
            "right": "But the drawers learned fast. Give the umbrella a thin handle, and it's guessed at once. Add a few tiny stars and streaks of light around the star, and everyone changes their mind. Oh, it's a star in the sky!",
            "wrong": ["But the drawers learned fast. Give the umbrella a thin handle, and it's gassed at once. Add a few tiny stars and streaks of light around the star, and everyone changes their mind. Oh, it's a star in the sky!"],
        },
        "ns00-02": {
            "variants": [
                'Not bee. They say Bravo. D is Delta. T is Tango.',
                'Not "bee"! They say "Bravo". D is "Delta", T is "Tango".',
                'Not "bee". They say "Bravo." "D" is "Delta." "T" is "Tango."',
                'Not "bee"... They say "Bravo." D is "Delta." T is "Tango."',
            ],
            "right": "Not bee. They say Bravo. D is Delta. T is Tango.",
            "wrong": ["Not bean. They say Bravo. D is Delta. T is Tango.", "Not bee. They say Bravo. T is Delta. T is Tango."],
        },
        "ns01-03": {
            "variants": [
                "Bee? Dee? Maybe E? Hmm… hard to tell, isn't it?",
                "B?... D?... Maybe E? Hmm… hard to tell, isn't it?",
                "B? D? Maybe E? Hmm... Hard to tell, isn't it?",
                "\"B\"? \"D\"? Maybe \"E\"? Hmm… hard to tell, isn't it?",
            ],
            "right": "B? D? Maybe E? Hmm... hard to tell, isn't it?",
            "wrong": ["P? D? Maybe E? Hmm... hard to tell, isn't it?", "B? T? Maybe E? Hmm... hard to tell, isn't it?"],
        },
        "ns01-06": {
            "variants": [
                "Listen again! Same crackle, different word.",
                "Listen, again. Same crackle; different word.",
                "Listen again... Same crackle, different word.",
            ],
            "right": "Listen again. Same crackle, different word.",
            "wrong": ["This and again. Same crackle, different word."],
        },
    },
}

PROMPT = {"zh": "以下是普通话科普旁白。", "en": "English educational narration."}


def voice(lang, cid, text, out):
    data = json.loads((ROOT / f"public/fun-informatics-03/narration/{lang}.json").read_text())
    line = next(l for l in data["lines"] if l["id"] == cid)
    with tempfile.TemporaryDirectory() as tmp:
        one = Path(tmp) / f"{lang}.json"
        one.write_text(json.dumps({**data, "lines": [{**line, "text": text}]}, ensure_ascii=False))
        subprocess.run([str(MEDIA / ".conda/bin/lucas-narrate"), str(one), "--profile", f"louise/{lang}", "--language", lang,
                        "--speed", "1.0", "--output-dir", tmp, "--only", cid, "--force"],
                       cwd=MEDIA, check=True, capture_output=True)
        shutil.move(Path(tmp) / f"{cid}.wav", out)


def judge(model, analyse, lang, cid, spec, path, text):
    r = analyse(model, path, text, lang, PROMPT[lang])
    ranked = force.scores(lang, path, [spec["right"], *spec["wrong"]])
    right = next(lp for lp, t in ranked if t == spec["right"])
    margin = right - max(lp for lp, t in ranked if t != spec["right"])
    ok = r["score"] >= 0.85 and not r["extra"] and margin >= 1.0
    return {"text": text, "heard": r["heard"], "score": r["score"], "extra": r["extra"], "margin": round(margin, 2), "ok": ok}


def install(lang, choice):
    cid, k = choice.split("=")
    takes = MEDIA / f"outputs/louise/{lang}/fun-informatics-03-v1"
    src = MEDIA / f"outputs/louise/{lang}/fun-informatics-03-retakes/{cid}.v{k}.wav"
    (takes / "replaced").mkdir(exist_ok=True)
    if not (takes / "replaced" / f"{cid}.wav").exists():
        shutil.copy(takes / f"{cid}.wav", takes / "replaced" / f"{cid}.wav")
    shutil.copy(src, takes / f"{cid}.wav")
    text = RETAKES[lang][cid]["variants"][int(k) - 1]
    print(f"{lang} {cid}: installed v{k}; SPOKEN = {text}")


def main():
    args = sys.argv[1:]
    if args[0] == "--install":
        for choice in args[2:]:
            install(args[1], choice)
        return
    lang, ids = args[0], args[1:] or list(RETAKES[args[0]])
    spec_check = importlib.util.spec_from_file_location("fi03_check", ROOT / "scripts/fun-informatics-03/check.py")
    check = importlib.util.module_from_spec(spec_check)
    spec_check.loader.exec_module(check)
    check.base.LANG = lang
    check.base.shared.units = check.base.units
    import whisper
    model = whisper.load_model("medium", device="cpu")
    force._model = model
    if lang == "zh":
        model = check.base.JoinedLatinWords(model)
    folder = MEDIA / f"outputs/louise/{lang}/fun-informatics-03-retakes"
    folder.mkdir(parents=True, exist_ok=True)
    for cid in ids:
        spec = RETAKES[lang][cid]
        original = MEDIA / f"outputs/louise/{lang}/fun-informatics-03-v1/{cid}.wav"
        original_text = next(l["text"] for l in json.loads((ROOT / f"public/fun-informatics-03/narration/{lang}.json").read_text())["lines"] if l["id"] == cid)
        candidates = [judge(model, check.base.shared.analyse, lang, cid, spec, original, original_text) | {"take": "original"}]
        for k, text in enumerate(spec["variants"], 1):
            path = folder / f"{cid}.v{k}.wav"
            if not path.exists():
                voice(lang, cid, text, path)
            candidates.append(judge(model, check.base.shared.analyse, lang, cid, spec, path, text) | {"take": f"v{k}"})
            c = candidates[-1]
            print(f"{lang} {cid} v{k}: {'OK ' if c['ok'] else 'BAD'} margin {c['margin']:+.2f} score {c['score']:.2f} | {c['heard']}", flush=True)
        # The other language may be retaking at the same time: merge into what is on disk now.
        report = json.loads(REPORT.read_text()) if REPORT.exists() else {}
        report.setdefault(lang, {})[cid] = {"candidates": candidates}
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        c = candidates[0]
        print(f"{lang} {cid} original: margin {c['margin']:+.2f} score {c['score']:.2f}", flush=True)


if __name__ == "__main__":
    main()
