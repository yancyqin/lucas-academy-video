"""The project's default narration voices (owner, 2026-10-07; README "Narration voices").

A voice is a lucas-academy-media profile plus the one delivery chosen for it. A film's narration script
writes these settings into every line, as lucas-narrate's per-line "instruct", "mode" and "speed", so a
finished film stays reproducible even if a default changes later. A film can still override the
instruction with its own (an edit file's `整体语气` / `Overall tone`).

    sys.path.insert(0, str(ROOT / "scripts"))
    from voice_defaults import VOICES, line_settings
"""
from __future__ import annotations

VOICES: dict[str, dict] = {
    # 「你可以用剪刀画画吗？」 (Matisse, 2026-10-05): plain zero-shot cloning, no instruction; the tone is
    # the reference recording's. Also lucas-narrate's own default for Chinese.
    "fangfang/zh": {"mode": "zero-shot", "instruction": "", "speed": 1.15},
    # Fun Informatics 1 (2026-10-07): the reference voice and its rhythm, steered toward curious discovery.
    "louise/zh": {"mode": "zero-shot-instruct", "instruction": "请用好奇、慢慢探索的语气，像带着孩子一起发现一样说。", "speed": 1.0},
    # Fun Informatics 1 (2026-10-07): the reference voice and its rhythm, curious and unhurried. The Van Gogh
    # House delivery (instruct, "lively, warm educational adventure guide") was the default for a day and came
    # out too lively and too fast for a whole film (owner, 2026-10-08).
    "louise/en": {"mode": "zero-shot-instruct",
                  "instruction": "Please speak in a curious, unhurried voice, like discovering something together with a child.",
                  "speed": 1.0},
}


def line_settings(voice: str, instruction: str = "") -> dict:
    """lucas-narrate's per-line fields for `voice`; a non-empty `instruction` replaces the default one.

    Plain zero-shot writes neither "instruct" nor "mode": lucas-narrate's auto mode is zero-shot cloning.
    An instruction given to a zero-shot voice keeps its reference rhythm (zero-shot-instruct).
    """
    v = VOICES[voice]
    text = instruction or v["instruction"]
    if not text:
        return {"speed": v["speed"]}
    mode = "zero-shot-instruct" if v["mode"] == "zero-shot" else v["mode"]
    return {"instruct": text, "mode": mode, "speed": v["speed"]}
