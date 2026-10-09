"""Build separate Louise narration inputs; English examples are adapted for the English film."""
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
    en, en_tone = shared.parse(ROOT / "docs/fun-informatics-02/en-edit.md")
    assert list(zh) == list(en) and len(zh) == 84
    lines, cues = [], []
    for cid, cue in zh.items():
        text = cue["text"]
        instruct = tone
        if cid in {"cl01-02", "cl04-12", "cl05-05"}:
            instruct += "每个字读清楚，句末停住。"
        text = re.sub(r"\b(18|19|20)\d{2}\b", lambda m: "".join("〇一二三四五六七八九"[int(d)] for d in m[0]), text)
        if cid == "cl01-02":
            text = text.replace("比特量出了信息", "比特，梁出了信息")
            instruct += "在“他用比特”之后稍停，“梁出了信息”连续读。"
        if cid == "cl04-12":
            text = re.sub(r"二〇一七\s*年", "二零一七年", text)
            instruct += "年份“二零一七年”连续读，数字之间不停顿。"
        if cid == "cl03-14":
            text = "研究表明，汉字的顺序并不一定能影响阅读。"
        assert not re.search(r"\d", text), (cid, text)
        lines.append({"id": cid, "text": text, "instruct": instruct, "mode": "zero-shot-instruct", "speed": 1.0})
        cues.append({"id": cid, "section": cue["section"], "zh": shared.plain(cue["text"]), "en": shared.plain(en[cid]["text"])})
    assert "比特，梁出了信息" in next(line["text"] for line in lines if line["id"] == "cl01-02")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "zh.json").write_text(json.dumps({"voice": "louise/zh", "language": "zh", "lines": lines}, ensure_ascii=False, indent=2) + "\n")
    spoken = {
        "cl01-01": en["cl01-01"]["text"].replace("1840", "eighteen forty"),
        "cl01-04": en["cl01-04"]["text"].replace("1916", "nineteen sixteen"),
        "cl02-04": en["cl02-04"]["text"].replace("1872", "eighteen seventy-two"),
        "cl03-04": en["cl03-04"]["text"].replace("first L, then D", "first ell, then dee"),
        "cl03-14": "The little dog ran around the garden.",
        "cl03-18": en["cl03-18"]["text"].replace("1948", "nineteen forty-eight"),
        "cl04-12": en["cl04-12"]["text"].replace("2017", "twenty seventeen"),
        "cl04-17": en["cl04-17"]["text"].replace("1840", "eighteen forty"),
        "cl06-02": en["cl06-02"]["text"].replace("1862", "eighteen sixty-two").replace("Clair de Lune", "Clair de lune"),
        "cl06-05": en["cl06-05"]["text"].replace("1916", "nineteen sixteen").replace("1918", "nineteen eighteen"),
    }
    english = [{"id": cid, "text": shared.plain(spoken.get(cid, cue["text"])), **shared.line_settings("louise/en", en_tone)} for cid, cue in en.items()]
    assert all(not re.search(r"\d", line["text"]) for line in english)
    (OUT / "en.json").write_text(json.dumps({"voice": "louise/en", "language": "en", "lines": english}, ensure_ascii=False, indent=2) + "\n")
    translations = {}
    current = None
    for raw in (ROOT / "docs/fun-informatics-02/en-edit.md").read_text().splitlines():
        if m := shared.LINE.match(raw.strip()): current = m[1]
        elif raw.strip().startswith("> ") and current: translations[current] = shared.plain(raw.strip()[2:])
    assert len(translations) == 84
    chinese_film_english = json.loads((ROOT / "docs/fun-informatics-02/zh-film-en-captions.json").read_text())
    for cue in cues:
        cue["enZh"] = translations[cue["id"]]
        cue["zhEn"] = chinese_film_english[cue["id"]]
    (OUT / "cues.json").write_text(json.dumps(cues, ensure_ascii=False, indent=2) + "\n")
    print(f"{len(cues)} cues per language; English adaptations ready -> {OUT}")


if __name__ == "__main__":
    main()
