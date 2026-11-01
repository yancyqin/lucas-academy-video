"""Which prompt gets CosyVoice3 to read with full feeling (owner, 2026-10-28: 感情饱满, 研究研究提示词)?

    lucas-academy-media/.conda/bin/python scripts/zhong-ying/emotion_lab.py lab          # one take per setup, measured
    lucas-academy-media/.conda/bin/python scripts/zhong-ying/emotion_lab.py voice A B …   # full texts with setups A, B …
    lucas-academy-media/.conda/bin/python scripts/zhong-ying/emotion_lab.py sunny         # full texts in Sunny's voice

What CosyVoice3 can be told (vendor/CosyVoice/cosyvoice/utils/common.py `instruct_list`, the instructions it was
trained on): dialects, loud / soft, slow / fast, and exactly three emotions — 「请非常开心地说一句话。」「…伤心…」「…生气…」.
Free-form descriptions such as 「有感情的语气」 are outside that list and barely move it (README "Narration voices",
memory: zero-shot-instruct keeps the reference's prosody). In zero-shot the reading copies the REFERENCE recording's
prosody, and Fangfang's reference is a calm lesson intro — the main reason the reading sounds flat.

Setups, all Fangfang at speed 1.0:
  0  series style: zero-shot-instruct, the free-form instruction (narration.py STYLE)
  1  trained emotion in the system slot: zero-shot-instruct 「请非常开心地说一句话。」 (reference prosody kept)
  2  trained emotion, instruct2 mode (reference prosody dropped, timbre kept; it drifts from her voice)
  3  expressive reference: zero-shot whose prompt is Fangfang's own most expressive verse take (narration/verses,
     Whisper-clean, widest pitch range), so the model copies an expressive Fangfang instead of the calm intro
  4  3 + the trained emotion in the system slot
  5  3 + [breath] before each line, as the model's own examples do for natural phrasing
Measured per take: pitch spread (sd and 5–95 % range, semitones), loudness movement (dB sd), similarity to her
reference voice (CAM++ embedding cosine), Whisper by sound. Writes DATA/narration/emotion-lab/.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from films import DATA, MEDIA  # noqa: E402
from narration import STYLE, heard_right  # noqa: E402

OUT = DATA / "narration" / "emotion-lab"
ASSISTANT = "You are a helpful assistant.<|endofprompt|>"
HAPPY = "请非常开心地说一句话。"
TEXTS = {   # owner, 2026-10-28: 杜甫《春夜喜雨》 and 传道书 3:11
    "chunye": "好雨知时节，当春乃发生。随风潜入夜，润物细无声。野径云俱黑，江船火独明。晓看红湿处，花重锦官城。",
    "chuandao": "神造万物，各按其时成为美好；又将永生安置在世人心里。然而神从始至终的作为，人不能参透。",
}
LAB_TEXTS = {"chunye": "好雨知时节，当春乃发生。随风潜入夜，润物细无声。",
             "chuandao": "神造万物，各按其时成为美好；又将永生安置在世人心里。"}
SPOKEN = {"花重": "花[zh][òng]"}               # 重 zhòng, heavy with rain
SETUPS = {"0": "series style", "1": "happy, hybrid", "2": "happy, instruct2", "3": "expressive reference",
          "4": "expressive reference + happy", "5": "expressive reference + [breath]"}


def ff(*args):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *map(str, args)], check=True)


def say(text: str, breath: bool = False) -> str:
    for plain, voiced in SPOKEN.items():
        text = text.replace(plain, voiced)
    if breath:   # a breath before each line (after every 。；), as the model's own examples phrase speech
        text = "[breath]" + re.sub(r"([。；])(?=.)", r"\1[breath]", text)
    return text


def pitch_stats(path):
    import librosa
    import numpy as np

    y, sr = librosa.load(str(path), sr=16000)
    f0, _, _ = librosa.pyin(y, fmin=70, fmax=500, sr=sr)
    f = f0[~np.isnan(f0)]
    st = 12 * np.log2(f / np.median(f))
    rms = librosa.feature.rms(y=y, frame_length=1024, hop_length=256)[0]
    db = 20 * np.log10(rms[rms > rms.max() * 0.05] + 1e-9)
    return {"pitch_sd": round(float(st.std()), 2), "pitch_range": round(float(np.percentile(st, 95) - np.percentile(st, 5)), 1),
            "loud_sd": round(float(db.std()), 1), "seconds": round(len(y) / sr, 2)}


def expressive_reference(asr):
    """Fangfang's most expressive verse take that Whisper heard right: the widest pitch spread."""
    import soundfile  # noqa: F401  (librosa backend)

    takes = sorted((DATA / "narration" / "verses" / "zh").glob("*-?.wav"))
    lines = {l["id"]: l["text"] for l in json.loads((DATA / "narration" / "verses" / "zh-check.json").read_text())["lines"]}
    best = None
    for path in takes:
        text = lines.get(path.stem)
        if not text:
            continue
        heard = asr.transcribe(str(path), language="zh", initial_prompt="以下是普通话的句子，使用简体中文。")["text"]
        if heard_right(text, heard, "zh") < 0.94:
            continue
        s = pitch_stats(path)
        if 4 <= s["seconds"] <= 14 and (best is None or s["pitch_sd"] > best[0]["pitch_sd"]):
            best = (s, path, text)
    return best


def main():
    mode = sys.argv[1]
    OUT.mkdir(parents=True, exist_ok=True)
    if mode == "sunny":
        return sunny(tuple(sys.argv[2:]))
    import torch
    import torchaudio
    import whisper

    sys.path.insert(0, str(MEDIA / "src"))
    from lucas_media.cosyvoice_engine import CosyVoiceEngine

    engine = CosyVoiceEngine(MEDIA / "profiles" / "fangfang" / "zh" / "profile.json")
    model, ref, sr = engine.model, str(engine.reference_audio), engine.model.sample_rate
    asr = whisper.load_model("medium")
    exp = json.loads((OUT / "reference.json").read_text()) if (OUT / "reference.json").exists() else None
    if exp is None:
        s, path, text = expressive_reference(asr)
        exp = {"wav": str(path), "text": text, **s}
        (OUT / "reference.json").write_text(json.dumps(exp, ensure_ascii=False, indent=1))
    print(f"expressive reference: {Path(exp['wav']).name} pitch sd {exp['pitch_sd']} st — {exp['text']}", flush=True)
    calm = engine.profile.reference_text
    ref_emb = model.frontend._extract_spk_embedding(ref)

    def system(instruction=""):
        return f"You are a helpful assistant. {instruction}<|endofprompt|>" if instruction else ASSISTANT

    def synth(setup, text, path):
        if setup == "0":
            g = model.inference_zero_shot(say(text), system(STYLE["zh"]["instruct"]) + calm, ref, stream=False, speed=1.0)
        elif setup == "1":
            g = model.inference_zero_shot(say(text), system(HAPPY) + calm, ref, stream=False, speed=1.0)
        elif setup == "2":
            g = model.inference_instruct2(say(text), system(HAPPY), ref, stream=False, speed=1.0)
        elif setup == "3":
            g = model.inference_zero_shot(say(text), ASSISTANT + exp["text"], exp["wav"], stream=False, speed=1.0)
        elif setup == "4":
            g = model.inference_zero_shot(say(text), system(HAPPY) + exp["text"], exp["wav"], stream=False, speed=1.0)
        else:
            g = model.inference_zero_shot(say(text, breath=True), ASSISTANT + exp["text"], exp["wav"], stream=False, speed=1.0)
        torchaudio.save(str(path), torch.concat([c["tts_speech"] for c in g], dim=1), sr)

    def measure(path, text):
        heard = asr.transcribe(str(path), language="zh", initial_prompt="以下是普通话的句子，使用简体中文。")["text"]
        emb = model.frontend._extract_spk_embedding(str(path))
        sim = float(torch.nn.functional.cosine_similarity(emb, ref_emb).item())
        return {**pitch_stats(path), "similarity": round(sim, 3), "heard_right": round(heard_right(text, heard, "zh"), 3), "heard": heard}

    if mode == "lab":
        rows = {}
        for tid, text in LAB_TEXTS.items():
            for setup, label in SETUPS.items():
                path = OUT / f"lab-{tid}-{setup}.wav"
                synth(setup, text, path)
                rows[f"{tid}/{setup}"] = {"setup": label, **measure(path, text)}
                r = rows[f"{tid}/{setup}"]
                print(f"{tid} {setup} {label:30s} pitch sd {r['pitch_sd']:4.2f} st, range {r['pitch_range']:4.1f} st, "
                      f"loud sd {r['loud_sd']:4.1f} dB, similarity {r['similarity']:.3f}, heard {r['heard_right']:.3f}", flush=True)
        (OUT / "lab.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1))
        return

    setups, takes = sys.argv[2:], 2
    picks = {}
    for setup in setups:
        for tid, text in TEXTS.items():
            best = None
            for k in range(takes):
                path = OUT / f"{setup}-{tid}-{k + 1}.wav"
                synth(setup, text, path)
                m = measure(path, text)
                print(f"{setup} {tid} take {k + 1}: heard {m['heard_right']:.3f}, pitch sd {m['pitch_sd']}, similarity {m['similarity']}", flush=True)
                key = (m["heard_right"] >= 0.94, m["pitch_sd"])
                if best is None or key > best[0]:
                    best = (key, path, m)
            picks[f"{setup}/{tid}"] = {"take": best[1].name, **best[2]}
        parts = [OUT / picks[f"{setup}/{tid}"]["take"] for tid in TEXTS]
        graph = "".join(f"[{i}]aresample=48000,aformat=channel_layouts=mono,apad=pad_dur=1.5[a{i}];" for i in range(len(parts)))
        graph += "".join(f"[a{i}]" for i in range(len(parts))) + f"concat=n={len(parts)}:v=0:a=1,loudnorm=I=-16:TP=-3:LRA=11"
        ff(*sum((["-i", p] for p in parts), []), "-filter_complex", graph, "-codec:a", "libmp3lame", "-b:a", "192k",
           OUT / f"voice-{setup}.mp3")
    (OUT / "voice.json").write_text(json.dumps(picks, ensure_ascii=False, indent=1))


# Sunny (owner, 2026-10-28: Windchime 18 and 19 are SUNNY's voice samples — never anyone else's). She reads a Tang poem
# and scripture there with feeling, so each text copies her own reading of the same kind: the poem her 登鹳雀楼, the
# scripture her 诗篇 121 (sunny_voice.py cut them into narration/sunny/zh-raw). Not too fast
# (owner): every take is held to her own pace in that reading, and a faster take is voiced again, slower.
SUNNY = {
    "chunye": (["climb-higher-v01", "climb-higher-v02"], "白日依山尽，黄河入海流。欲穷千里目，更上一层楼。"),
    "chuandao": (["climb-higher-v07", "climb-higher-v08"], "我要向山举目；我的帮助从何而来？我的帮助从造天地的耶和华而来。"),
}


PACE_CAP = 2.1        # syllables per second, pauses included: "朗读速度不要太快" (owner, 2026-10-28)


def sunny(only=(), takes: int = 3):
    import numpy as np
    import torch
    import torchaudio
    import whisper

    sys.path.insert(0, str(MEDIA / "src"))
    from lucas_media.cosyvoice_engine import CosyVoiceEngine

    from sunny_voice import STUDIO

    out = OUT / "sunny"
    out.mkdir(parents=True, exist_ok=True)
    engine = CosyVoiceEngine(MEDIA / "profiles" / "sunny" / "zh" / "profile.json")
    model, sr = engine.model, engine.model.sample_rate
    asr = whisper.load_model("medium")
    her = model.frontend._extract_spk_embedding(str(engine.reference_audio))
    raw = DATA / "narration" / "sunny" / "zh-raw"

    def rate(path, text):        # syllables per second over the whole reading, pauses included
        import soundfile as sf
        x, r = sf.read(path)
        env = np.convolve(np.abs(x), np.ones(r // 50) / (r // 50), "same")
        on = np.nonzero(env > 0.05 * env.max())[0]
        return len(re.findall(r"[一-鿿]", text)) / ((on[-1] - on[0]) / r)

    picks = json.loads((out / "picks.json").read_text()) if (out / "picks.json").exists() else {}
    for tid, text in TEXTS.items():
        if only and tid not in only:
            continue
        clips, ref_text = SUNNY[tid]
        ref = out / f"reference-{tid}.wav"
        ff(*sum((["-i", raw / f"{c}.wav"] for c in clips), []), "-filter_complex",
           "".join(f"[{i}]" for i in range(len(clips))) + f"concat=n={len(clips)}:v=0:a=1", "-ar", "24000", ref)
        target = min(PACE_CAP, rate(ref, ref_text))      # her own pace reading this kind of text, never faster than the cap
        best = None
        for k in range(takes):
            speed, path = 1.0, out / f"{tid}-{k + 1 + 10 * bool(only)}.wav"
            for _ in range(3):                            # held to her pace: slower if the take ran faster
                g = model.inference_zero_shot(say(text), ASSISTANT + ref_text, str(ref), stream=False, speed=speed)
                torchaudio.save(str(path), torch.concat([c["tts_speech"] for c in g], dim=1), sr)
                pace = rate(path, text)
                if pace <= target * 1.05 or speed <= 0.8:
                    break
                speed = max(0.8, round(speed * target / pace, 2))
            heard = asr.transcribe(str(path), language="zh", initial_prompt="以下是普通话的句子，使用简体中文。")["text"]
            sim = float(torch.nn.functional.cosine_similarity(model.frontend._extract_spk_embedding(str(path)), her).item())
            m = {**pitch_stats(path), "pace": round(pace, 2), "her_pace": round(target, 2), "speed": speed,
                 "similarity": round(sim, 3), "heard_right": round(heard_right(text, heard, "zh"), 3), "heard": heard}
            print(f"sunny {tid} take {k + 1}: speed {speed}, pace {m['pace']} (hers {m['her_pace']}) syll/s, pitch sd "
                  f"{m['pitch_sd']} st, similarity {m['similarity']}, heard {m['heard_right']}", flush=True)
            key = (m["heard_right"] >= 0.94, m["pitch_sd"])
            if best is None or key > best[0]:
                best = (key, path, m)
        picks[tid] = {"take": best[1].name, **best[2]}
    for label, chain in (("Sunny", None), ("Sunny-录音室处理", STUDIO)):
        parts = [out / picks[tid]["take"] for tid in TEXTS]
        graph = "".join(f"[{i}]aresample=48000,aformat=channel_layouts=mono{',' + chain if chain else ''},apad=pad_dur=1.5[a{i}];"
                        for i in range(len(parts)))
        graph += "".join(f"[a{i}]" for i in range(len(parts))) + f"concat=n={len(parts)}:v=0:a=1,loudnorm=I=-16:TP=-3:LRA=11"
        ff(*sum((["-i", p] for p in parts), []), "-filter_complex", graph, "-codec:a", "libmp3lame", "-b:a", "192k",
           out / f"{label}.mp3")
    (out / "picks.json").write_text(json.dumps(picks, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    main()
