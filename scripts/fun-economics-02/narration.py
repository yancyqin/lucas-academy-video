"""Narration inputs for Education Economics 2 from docs/fun-economics-02/{zh,en}-edit.md, with Fun Economics 1's rules
(numbers spelled out for the voice, captions keep them; Mary in Eunice's voice; the questions read curious).
  python3 scripts/fun-economics-02/narration.py
"""
from common import DOCS, PUB, base

if __name__ == "__main__":
    n = base("narration")
    n.SRC, n.OUT, n.CUES = DOCS, PUB / "narration", 38
    n.QUESTIONS = {"sc00-04", "sc09-01"}
    # Re-takes after the Whisper check (retake.py): a punctuation change gives a new take; captions keep the script.
    n.RETAKE = {
        "zh": {
            "sc05-01": ("写作业也一样。", "写作业，也一样。"),  # 也 dropped, Mary heard as Nari
            "sc04-04": ("而且拆了，积木一块也没少；", "而且拆了：积木，一块也没少；"),  # 积木 heard as 金木
            "sc06-01": ("拼好的乐高、", "「拼好」的乐高、"),  # 拼好 heard as 平好
        },
        "en": {
            "sc05-06": ("And the wrong steps weren't", "And the wrong steps... weren't"),  # wrong heard as round
            "sc04-02": ("So you try to patch it: a brick here, a detour there, and the more",
                        "So you try to patch it... a brick here, a detour there... and the more"),  # brick heard as break
        },
    }
    n.main()
