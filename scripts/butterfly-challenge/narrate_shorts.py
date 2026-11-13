"""Voice the two lines only the vertical shorts need (docs/butterfly-challenge/shorts.md), in Louise's zh and en voices.

  ../lucas-academy-media/.conda/bin/python scripts/butterfly-challenge/narrate_shorts.py --lang zh|en [--force]

Same settings as the film (narrate.py: zero-shot-instruct, 1.1, the base delivery). Every other line in the shorts is
the film's own take. Takes go next to the film's: outputs/louise/<lang>/butterfly-challenge-v1/s1.10/<id>.wav.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import narrate  # noqa: E402

# id: (caption, what the voice reads) per language; measure-word 只 read as 枝 (narrate.py's rule), no digits
LINES = {
    "sh-intro": {"zh": ("一只是真的，一只是 AI 画的。你来猜：哪只是真的？", "一枝是<strong>真的</strong>，一枝是 <strong>AI</strong> 画的。你来猜……哪枝是真的？"),
                 "en": ("One is real, one was drawn by AI. Your turn: which one is real?",
                        "One is real, one was drawn by AI. Your turn: which one is real?")},
    "sh04-01": {"zh": ("两个 AI 都选错了！AI 这张每个细节都清清楚楚，Fable 反倒嫌真的这只身子糊成一团。",
                       # take 1: 这 too weak (这只 over 只只 by 0.9 nats) → commas around 「真的这枝」
                       "两个 AI，都选错了！AI 这张每个细节都<strong>清清楚楚</strong>，Fable 反倒嫌，<strong>真的这枝</strong>，身子糊成一团。"),
                "en": ("Both AIs got it wrong! Every detail of the AI one is crisp, and Fable even said the real one's body was a smeared blob.",
                       "Both AIs got it wrong! Every detail of the AI one is crisp, and Fable even said the real one's body was a smeared blob.")},
}
VOICE, SPEED = "louise", 1.1


def take(lid: str, lang: str):
    return narrate.takes_dir(VOICE, lang) / f"s{SPEED:.2f}" / f"{lid}.wav"


if __name__ == "__main__":
    args = sys.argv[1:]
    lang = narrate.opt(args, "--lang", "zh")
    todo = [lid for lid in LINES if "--force" in args or not take(lid, lang).exists()]
    if not todo:
        raise SystemExit("nothing to voice")
    os.chdir(narrate.MEDIA)
    sys.path.insert(0, str(narrate.MEDIA / "src"))
    import torch  # noqa: E402

    torch.set_num_threads(int(os.environ.get("NARRATE_THREADS", "4")))
    from lucas_media.cosyvoice_engine import CosyVoiceEngine  # noqa: E402
    from lucas_media.joke import DEFAULT_PEAK_DBFS, add_peak_headroom, save_wav  # noqa: E402

    engine = CosyVoiceEngine(narrate.MEDIA / f"profiles/{VOICE}/{lang}/profile.json")
    tone = narrate.TONE["基准" if lang == "zh" else "base"]
    for lid in todo:
        speech, rate, _ = engine.synthesize(LINES[lid][lang][1], target_language=lang, mode="zero-shot-instruct",
                                            instruction=tone, speed=SPEED)
        path = take(lid, lang)
        save_wav(path, add_peak_headroom(speech, peak_dbfs=DEFAULT_PEAK_DBFS), rate)
        print(f"{lid} {lang} {speech.shape[1] / rate:.2f}s -> {path.name}", flush=True)
