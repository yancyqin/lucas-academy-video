"""List every shot and the music in the film with source and licence -> DATA/CREDITS.md"""
import json
import pathlib

HERE = pathlib.Path(__file__).parent
EDIT = json.loads((HERE / "edit.json").read_text())
DATA = pathlib.Path(EDIT["data"])
JOURNEY = pathlib.Path(EDIT["journey"])


def records():
    recs = {}
    for root, base in (("jesu", DATA / "footage"), ("journey", JOURNEY / "footage")):
        for f in base.glob("*/sources.json"):
            for r in json.loads(f.read_text()):
                recs.setdefault(f"{root}:{f.parent.name}/{r['file']}", r)
    return recs


def main():
    recs = records()
    rows, attrib = [], []
    for s in EDIT["shots"]:
        r = recs.get(s["src"], {})
        lic = r.get("license", "?")
        who = r.get("credit") or r.get("author") or ""
        title = r.get("title", s["src"])
        rows.append(f"| {int(s['at']) // 60}:{int(s['at']) % 60:02d} | {s['id']} | {title} | {lic} | {who} | {r.get('source_page_url', '')} |")
        if "CC BY" in lic.upper().replace("-", " "):
            attrib.append(f"- {title} — {who} — {lic} — {r.get('source_page_url', '')}")
    out = ["# 耶稣，世人仰望的喜悦 — credits and licences", "",
           "## Music", "",
           "- J. S. Bach, *Jesus bleibet meine Freude*, BWV 147/10 — Orchestra Gli Armonici — CC0 "
           "(Musopen, via https://commons.wikimedia.org/wiki/File:Bach,_BWV_147,_10._Jesus_bleibet_meine_Freude.ogg). "
           "Choir removed with demucs (htdemucs_ft).", "",
           "## Scripture", "", "- 和合本 (Chinese Union Version, 1919), public domain.", "",
           "## Font", "", "- Noto Serif SC (思源宋体), SIL Open Font License 1.1.", "",
           "## Picture", "", "| at | shot | source | licence | author / credit | page |",
           "|---|---|---|---|---|---|", *rows, "",
           "## Needs attribution (CC BY / CC BY-SA)", "", *attrib, ""]
    (DATA / "CREDITS.md").write_text("\n".join(out))
    print(f"{len(rows)} shots, {len(attrib)} need attribution")


if __name__ == "__main__":
    main()
