"""Listening page for the real animal sounds of 「动物想什么？AI 知道吗？」 (Yancy 2026-11-11: 「有没有真实的动物声音样本可以试听呢？」).

Reads docs/ai-animal-mind/sound-sources.json (the candidates: source, licence, best windows), edit.json's `sounds`
and the built timeline, and writes one local page, lucas-academy-video-data/ai-animal-mind/sounds/listen.html (open
it in a browser). On top: each place in the film as it sounds there in both tracks, cut from
out/ai-animal-mind/mix.{en,zh}.wav from the line before the recording to just after it (voice, recording, music).
Below: every candidate with its best windows, its whole file, its licence and its source page. Cuts go to
sounds/listen/. Run it after build_timeline.py has built both tracks.

    python3 scripts/ai-animal-mind/sounds_page.py
"""
import html
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = next(p / "lucas-academy-video-data" for p in ROOT.parents if (p / "lucas-academy-video-data").is_dir())
SND = DATA / "ai-animal-mind/sounds"
SRC = json.loads((ROOT / "docs/ai-animal-mind/sound-sources.json").read_text())
EDIT = json.loads((ROOT / "scripts/ai-animal-mind/edit.json").read_text())
TL = json.loads((ROOT / "public/ai-animal-mind/timeline.json").read_text())
CAP = {lang: {m[0]: m[1] for m in (l[2:].split(" | ", 1) for l in (ROOT / f"docs/ai-animal-mind/{lang}-draft.md")
                                   .read_text().splitlines() if l.startswith("- am"))} for lang in ("en", "zh")}
SOUND_NAMES = {1: "海豚 · Dolphins", 2: "抹香鲸 · Sperm whales", 3: "大象 · Elephants", 4: "座头鲸 · Humpback whales",
               5: "猪 · Pigs", 6: "猴子 · Monkeys"}


def cut(src: Path, a: float, b: float, out: Path) -> None:
    if not out.is_file():
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{a}", "-t", f"{b - a}", "-i", str(src), "-ac", "1",
                        "-af", "loudnorm=I=-20:TP=-2,afade=t=in:d=0.05,afade=t=out:st=" + f"{max(0.0, b - a - 0.3)}:d=0.3",
                        "-c:a", "libmp3lame", "-q:a", "3", str(out)], check=True)


def film_rows() -> list:
    """Each place in the film: from the start of the line before the recording to 0.8 s after the last one."""
    rows = ["<h2>片中的效果（旁白 + 录音 + 音乐）</h2>"]
    groups = {}
    for e, s in zip(EDIT.get("sounds", []), TL.get("sounds", [])):
        groups.setdefault(e["after"], []).append((e, s))
    for lid, items in groups.items():
        a, b = TL["lines"][lid]["start"], items[-1][1]["end"] + 0.8
        names = "；".join(html.escape(e["name"]) for e, _ in items)
        players = []
        for lang in ("zh", "en"):
            out = SND / "listen" / f"film-{lang}-{lid}.mp3"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{a}", "-t", f"{b - a}", "-i",
                            str(ROOT / f"out/ai-animal-mind/mix.{lang}.wav"), "-c:a", "libmp3lame", "-q:a", "2", str(out)],
                           check=True)
            players.append(f"<div>{html.escape(CAP[lang].get(lid, ''))}<br>"
                           f"<audio controls preload=none src='listen/{out.name}'></audio></div>")
        rows.append(f"<section><p><b>{lid}</b> <span class=n>{names}</span></p>{''.join(players)}</section>")
    return rows


def main() -> None:
    (SND / "listen").mkdir(parents=True, exist_ok=True)
    used = {(e["src"], round(e.get("in", 0.0), 2)): e["after"] for e in EDIT.get("sounds", [])}
    rows = film_rows() + ["<h2>候选录音</h2>"]
    for sound in sorted({c["sound"] for c in SRC}, key=lambda s: int(str(s)[0])):
        rows.append(f"<h3 class=s>{html.escape(SOUND_NAMES.get(int(str(sound)[0]), str(sound)))}</h3>")
        for c in [c for c in SRC if c["sound"] == sound]:
            path = Path(c["local_path"])
            if not path.is_file():
                continue
            rel = path.relative_to(SND).as_posix()
            src_rel = str(path.relative_to(SND / "raw"))
            clips = []
            for a, b in c.get("best_windows", []):
                out = SND / "listen" / f"{c['id']}-{a:.1f}-{b:.1f}.mp3"
                cut(path, a, b, out)
                pick = used.get((src_rel, round(a, 2)))
                tag = f" <b>← 片中用在 {pick} 之后</b>" if pick else ""
                clips.append(f"<div>{a:.1f}–{b:.1f} s{tag}<br><audio controls preload=none src='listen/{out.name}'></audio></div>")
            rows.append(
                f"<section><h4>{html.escape(c['what'])}</h4>"
                f"<p>{html.escape(c.get('species', ''))} · {html.escape(c.get('recordist_or_source', ''))} · "
                f"<b>{html.escape(c['licence'])}</b> · <a href='{html.escape(c['page_url'])}'>来源</a></p>"
                + "".join(clips)
                + f"<details><summary>整段（{c.get('duration_s', 0):.0f} 秒）</summary><audio controls preload=none src='{rel}'></audio></details>"
                + (f"<p class=n>{html.escape(c['notes'])}</p>" if c.get("notes") else "") + "</section>")
    page = ("<!doctype html><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'>"
            "<title>动物声音试听</title><style>body{font:15px/1.5 -apple-system,sans-serif;max-width:860px;margin:24px auto;"
            "padding:0 16px;background:#fbfaf7;color:#222}section{border-top:1px solid #ddd;padding:10px 0}"
            "audio{width:100%;max-width:520px}div{margin:6px 0}.n{color:#666;font-size:13px}h2{margin-top:32px}h3.s{margin-top:28px;font-size:20px}</style>"
            "<h1>动物想什么？AI 知道吗？· 真实的动物声音</h1>"
            "<p>上面是片子里现在的样子；下面是每种动物的候选录音，先听推荐的几秒（已统一音量），需要时再听整段。标了「片中用在…之后」的就是现在用的那一段。</p>"
            + "".join(rows))
    (SND / "listen.html").write_text(page)
    print(SND / "listen.html")


if __name__ == "__main__":
    main()
