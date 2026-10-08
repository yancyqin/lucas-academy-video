"""Build the approved episode 2 Chinese narration; English synthesis is on hold."""
import importlib.util
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "public/fun-informatics-02/narration"
spec = importlib.util.spec_from_file_location("fi01_narration", ROOT / "scripts/fun-informatics-01/narration.py")
shared = importlib.util.module_from_spec(spec)
spec.loader.exec_module(shared)
shared.SECTION = re.compile(r"^## (CL\d\d)\b")
shared.LINE = re.compile(r"^- (cl\d\d-\d\d) \| (.+)$")


def main():
    zh, tone = shared.parse(ROOT / "docs/fun-informatics-02/zh-edit.md")
    en, _ = shared.parse(ROOT / "docs/fun-informatics-02/en-edit.md")
    assert list(zh) == list(en) and len(zh) == 84
    lines, cues = [], []
    for cid, cue in zh.items():
        text = cue["text"]
        text = re.sub(r"\b(18|19|20)\d{2}\b", lambda m: "".join("〇一二三四五六七八九"[int(d)] for d in m[0]), text)
        if cid == "cl01-02":
            text = text.replace("比特量出了信息", "比特梁出了信息")
        if cid == "cl03-14":
            text = "研究表明，汉字的顺序并不一定能影响阅读。"
        assert not re.search(r"\d", text), (cid, text)
        lines.append({"id": cid, "text": text, "instruct": tone, "mode": shared.MODE, "speed": 1.0})
        cues.append({"id": cid, "section": cue["section"], "zh": shared.plain(cue["text"]), "en": shared.plain(en[cid]["text"])})
    assert "比特梁" in next(line["text"] for line in lines if line["id"] == "cl01-02")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "zh.json").write_text(json.dumps({"voice": "louise/zh", "language": "zh", "lines": lines}, ensure_ascii=False, indent=2) + "\n")
    (OUT / "cues.json").write_text(json.dumps(cues, ensure_ascii=False, indent=2) + "\n")
    print(f"{len(cues)} approved cues; Chinese synthesis only -> {OUT}")


if __name__ == "__main__":
    main()
