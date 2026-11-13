"""Voice every line of 一片落叶 in Louise (zh/en 1.1, 基准 instruction); LF01-LF02 reuse the approved voice-test takes.

usage: narrate.py zh|en [id ...]   (takes/<lang>/<id>.wav; existing takes are kept; delete one to redo it)
"""
import json
import os
import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
HERE = REPO / "out/leaf-truck"   # takes, voice tests and checks (git-ignored)
MEDIA = Path("/Users/yqin/repo/playground/lucas-academy-media")
lang, only = sys.argv[1], set(sys.argv[2:])
LINE = re.compile(r"^- (lf\d\d-\d\d) \| (.+)$")
SPOKEN = {"zh": {"lf07-02": ("下落", "下洛")},
          "en": {"lf04-06": ("lidar", "lie-dar"), "lf06-04": ("lidar", "lie-dar")}}
# punctuation-only retakes (same characters as the caption), 2026-11-12
RESPOKEN = {"zh": {
    "lf06-03": "所以要先想清楚，最后要做到什么——落叶，可以不管；托盘、行人，一个都不能漏。再从这个目标往回想，车要分清哪些东西。",
    "lf06-04": "同一个项目里，工程师提出的办法，也不只一个：让系统把树叶、树枝这些软东西，当作「不是障碍」；再加上摄像头，帮激光雷达，看清低矮的东西。",
    "lf07-04": "钥匙找不到？——先想想，上次是什么时候用的？",
    "lf07-05": "我觉得，再前沿的工程，也是把大问题拆开——让几种思维方式，互相补充。"}, "en": {}}
INSTRUCT = {"zh": "请用真诚、温暖、有感情的语气，像跟朋友、跟家长聊天那样说。",
            "en": "Speak in a sincere, warm, heartfelt voice, like talking with friends and parents about something you care about. Natural pace."}
SPEED = 1.1


def lines():
    out = []
    for raw in (REPO / f"docs/leaf-truck/{lang}-draft.md").read_text().splitlines():
        if m := LINE.match(raw):
            text = re.sub(r"【[^】]*】", "", m[2]).strip()
            spoken = text
            if m[1] in RESPOKEN[lang]:
                spoken = RESPOKEN[lang][m[1]]
                assert re.sub(r"[^\w]", "", spoken) == re.sub(r"[^\w]", "", text) or m[1] in SPOKEN[lang], (m[1], "punctuation only")
            elif m[1] in SPOKEN[lang]:
                a, b = SPOKEN[lang][m[1]]
                assert a in spoken, (m[1], a)
                spoken = spoken.replace(a, b)
            assert not re.search(r"\d|〇", spoken), spoken
            out.append({"id": m[1], "text": text, "spoken": spoken})
    return out


def main():
    rows = lines()
    dest = HERE / "takes" / lang
    dest.mkdir(parents=True, exist_ok=True)
    (HERE / "takes" / f"{lang}.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1) + "\n")
    todo = []
    for r in rows:
        if only and r["id"] not in only:
            continue
        wav = dest / f"{r['id']}.wav"
        test = HERE / "voice-test" / f"louise-{lang}" / f"{r['id']}.wav"
        if not wav.exists() and test.exists() and not only:
            shutil.copy2(test, wav)
            print("reuse", r["id"], flush=True)
        if not wav.exists():
            todo.append(r)
    if not todo:
        return
    os.chdir(MEDIA)
    sys.path.insert(0, str(MEDIA / "src"))
    import torch
    torch.set_num_threads(3)
    torch.set_num_interop_threads(2)
    from lucas_media.cosyvoice_engine import CosyVoiceEngine
    from lucas_media.joke import DEFAULT_PEAK_DBFS, add_peak_headroom, save_wav
    engine = CosyVoiceEngine(MEDIA / f"profiles/louise/{lang}/profile.json")
    for r in todo:
        speech, rate, _ = engine.synthesize(r["spoken"], target_language=lang, mode="zero-shot-instruct",
                                            instruction=INSTRUCT[lang], speed=SPEED)
        seconds = speech.shape[1] / rate
        if seconds < max(.4, len(r["spoken"].split()) / 4.8 if lang == "en" else len(r["spoken"]) / 9):
            print("TRUNCATED", r["id"], f"{seconds:.2f}s", flush=True)
            continue
        save_wav(dest / f"{r['id']}.wav", add_peak_headroom(speech, peak_dbfs=DEFAULT_PEAK_DBFS), rate)
        print(r["id"], f"{seconds:.2f}s", flush=True)


if __name__ == "__main__":
    main()
