"""Voice test for 一片落叶: LF01 + LF02 (the first minute) in four voices.

usage: voice_test.py zh|en
  zh: yancy/zh zero-shot-instruct (statements 1.2, questions 1.1) and louise/zh zero-shot-instruct 1.1
  en: yancy cross-lingual from the yancy/zh profile (1.1 / 1.0) and louise/en zero-shot-instruct 1.1
Same delivery instruction as 「你爱听 AI 说是的吗」 (基准). Takes: voice-test/<variant>/<id>.wav; existing ones are kept.
"""
import os
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
HERE = REPO / "out/leaf-truck"   # takes, voice tests and checks (git-ignored)
MEDIA = Path("/Users/yqin/repo/playground/lucas-academy-media")
lang = sys.argv[1]
LINE = re.compile(r"^- (lf0[12]-\d\d) \| (.+)$")
lines = [(m[1], re.sub(r"【[^】]*】", "", m[2]).strip())
         for raw in (REPO / f"docs/leaf-truck/{lang}-draft.md").read_text().splitlines() if (m := LINE.match(raw))]
assert len(lines) == 10, lines
for _, text in lines:
    assert not re.search(r"\d|〇", text), text
INSTRUCT = {"zh": "请用真诚、温暖、有感情的语气，像跟朋友、跟家长聊天那样说。",
            "en": "Speak in a sincere, warm, heartfelt voice, like talking with friends and parents about something you care about. Natural pace."}
question = lambda t: t.rstrip("」”\"'").endswith(("？", "?"))

os.chdir(MEDIA)
sys.path.insert(0, str(MEDIA / "src"))
import torch  # noqa: E402
torch.set_num_threads(3)
torch.set_num_interop_threads(2)
from lucas_media.cosyvoice_engine import CosyVoiceEngine  # noqa: E402
from lucas_media.joke import DEFAULT_PEAK_DBFS, add_peak_headroom, save_wav  # noqa: E402

variants = ([("yancy-zh", "yancy", 1.2, 1.1), ("louise-zh", "louise", 1.1, 1.1)] if lang == "zh"
            else [("yancy-en", "yancy", 1.1, 1.0), ("louise-en", "louise", 1.1, 1.1)])
for name, voice, speed, qspeed in variants:
    profile = MEDIA / f"profiles/{voice}/{'zh' if voice == 'yancy' else lang}/profile.json"
    engine = CosyVoiceEngine(profile)
    out = HERE / "voice-test" / name
    out.mkdir(parents=True, exist_ok=True)
    for key, text in lines:
        path = out / f"{key}.wav"
        if path.exists():
            continue
        s = qspeed if question(text) else speed
        if name == "yancy-en":
            gen = engine.model.inference_cross_lingual(f"You are a helpful assistant. {INSTRUCT['en']}<|endofprompt|>" + text,
                                                       str(engine.reference_audio), stream=False, speed=s)
            speech, rate = torch.cat([x["tts_speech"].cpu() for x in gen], dim=1), engine.model.sample_rate
        else:
            speech, rate, _ = engine.synthesize(text, target_language=lang, mode="zero-shot-instruct",
                                                instruction=INSTRUCT[lang], speed=s)
        save_wav(path, add_peak_headroom(speech, peak_dbfs=DEFAULT_PEAK_DBFS), rate)
        print(name, key, f"{speech.shape[1] / rate:.2f}s", flush=True)
    del engine
