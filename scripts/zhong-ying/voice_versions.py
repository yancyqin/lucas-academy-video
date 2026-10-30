"""Audition versions of the Chinese reading (owner, 2026-10-27: the AI voices read with too little feeling, Sunny's
recording doesn't sound professional enough — try 2–3 ways in between).

    lucas-academy-media/.conda/bin/python scripts/zhong-ying/voice_versions.py

All on 早发白帝城 (little-boats v01, v02) from Sunny's recording (sunny_voice.py):
  0-original     her clips as recorded
  A-studio       her voice, studio-processed: rumble cut, less mud, more presence and air, gentle compression,
                 de-essing, a touch of room
  B-fangfang-vc  her reading converted to Fangfang's voice (CosyVoice3 voice conversion: her timing, pauses and
                 contour; her timbre)
  C-your-style   a new reading in Fangfang's voice whose LM prompt is SUNNY's reading of 登鹳雀楼, so the model continues
                 in Sunny's style rather than the lesson-reading style of her reference
Writes DATA/narration/versions/<version>/<line>.wav and an audition file <version>.mp3 (both lines, levelled).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from films import DATA, MEDIA, texts  # noqa: E402
from narration import spoken  # noqa: E402
from sunny_voice import STUDIO  # noqa: E402

OWNER = DATA / "narration" / "sunny" / "zh-raw"
OUT = DATA / "narration" / "versions"
LINES = ["little-boats-v01", "little-boats-v02"]
STYLE_FROM = ["climb-higher-v01", "climb-higher-v02"]      # Sunny's 登鹳雀楼: the style prompt for C
ASSISTANT = "You are a helpful assistant.<|endofprompt|>"


def ff(*args):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *map(str, args)], check=True)


def audition(version: str):
    """Both lines with a pause between, at −16 LUFS, as one mp3."""
    parts = [OUT / version / f"{line}.wav" for line in LINES]
    graph = "".join(f"[{i}]aresample=48000,aformat=channel_layouts=mono,apad=pad_dur=0.9[a{i}];" for i in range(len(parts)))
    graph += "".join(f"[a{i}]" for i in range(len(parts))) + f"concat=n={len(parts)}:v=0:a=1,loudnorm=I=-16:TP=-3:LRA=11"
    ff(*sum((["-i", p] for p in parts), []), "-filter_complex", graph, "-codec:a", "libmp3lame", "-b:a", "192k",
       OUT / f"{version}.mp3")


def main():
    zh = {}
    for film in ("climb-higher", "little-boats"):
        zh.update({f"{film}-v{u['n']:02d}": u["spoken_zh"] for u in texts(film)})
    for v in ("0-original", "A-studio", "B-fangfang-vc", "C-your-style"):
        (OUT / v).mkdir(parents=True, exist_ok=True)
    for line in LINES:
        ff("-i", OWNER / f"{line}.wav", OUT / "0-original" / f"{line}.wav")
        ff("-i", OWNER / f"{line}.wav", "-af", STUDIO, OUT / "A-studio" / f"{line}.wav")
    for v in ("0-original", "A-studio"):
        audition(v)
        print(f"{v}: done")

    # CosyVoice (B and C), loaded the way lucas-academy-media's engine does.
    import torch
    import torchaudio

    sys.path.insert(0, str(MEDIA / "src"))
    from lucas_media.cosyvoice_engine import CosyVoiceEngine

    engine = CosyVoiceEngine(MEDIA / "profiles" / "fangfang" / "zh" / "profile.json")
    model, ref = engine.model, str(engine.reference_audio)
    sr = model.sample_rate

    def save(chunks, path):
        torchaudio.save(str(path), torch.concat([c["tts_speech"] for c in chunks], dim=1), sr)

    for line in LINES:
        save(list(model.inference_vc(str(OWNER / f"{line}.wav"), ref)), OUT / "B-fangfang-vc" / f"{line}.wav")
        print(f"B {line}: done")
    audition("B-fangfang-vc")

    style_wav = OUT / "style-prompt.wav"
    ff(*sum((["-i", OWNER / f"{l}.wav"] for l in STYLE_FROM), []), "-filter_complex",
       "".join(f"[{i}]" for i in range(len(STYLE_FROM))) + f"concat=n={len(STYLE_FROM)}:v=0:a=1", "-ar", "24000", style_wav)
    style_text = ASSISTANT + "".join(zh[l] for l in STYLE_FROM)
    voice_text = ASSISTANT + engine.profile.reference_text
    for line in LINES:
        text = spoken(zh[line])
        his = model.frontend.frontend_zero_shot(text, style_text, str(style_wav), sr, "")
        her = model.frontend.frontend_zero_shot(text, voice_text, ref, sr, "")
        # The language model continues SUNNY's reading (prompt text + speech tokens); the flow renders HER timbre.
        mixed = {**his, **{k: her[k] for k in ("flow_prompt_speech_token", "flow_prompt_speech_token_len",
                                               "prompt_speech_feat", "prompt_speech_feat_len", "flow_embedding")}}
        save(list(model.model.tts(**mixed, stream=False, speed=1.0)), OUT / "C-your-style" / f"{line}.wav")
        print(f"C {line}: done")
    audition("C-your-style")
    (OUT / "README.json").write_text(json.dumps({"lines": LINES, "style_from": STYLE_FROM, "studio": STUDIO},
                                                ensure_ascii=False, indent=1))


if __name__ == "__main__":
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    main()
