"""Automatic checks every video must pass before Yancy sees it (README "Automatic checks").

    PY=.venv-align/bin/python                     # Whisper + numpy + pypinyin
    $PY scripts/qa/qa.py spec zhongying public/zhong-ying/who-woke-you/timeline.json -o out/qa/who-woke-you/qa-spec.json
    $PY scripts/qa/qa.py spec srt film.zh-Hans.srt:zh [film.en.srt:en] --kind narrated --music -o qa-spec.json
    $PY scripts/qa/qa.py lint qa-spec.json        # before voicing: spellings the voices get wrong
    $PY scripts/qa/qa.py check FILM.mp4 --spec qa-spec.json [--audio en.m4a] [--out DIR]
    $PY scripts/qa/qa.py serve DIR                # the listening page; 通过 / 重配 are saved to DIR/decisions.json
    $PY scripts/qa/qa.py decide DIR --from pasted.json   # the same, from the page's 复制 button (page opened as a file)
    $PY scripts/qa/qa.py gate FILM.mp4 [--audio en.m4a]  # exit 0 only when these exact files passed, every 拿不准 decided
    $PY scripts/qa/qa.py upload ~/Desktop/<片名>-上传   # the upload folder: chapters first, tags, covers, SRTs, gates

`check` writes DIR/report.json (keyed to the sha256 of the film and, with --audio, of that audio file) and
DIR/review.html. Exit status: 0 everything passed or was approved, 1 拿不准 items wait for Yancy, 2 something failed.
A film's package script calls `require(path)` — and `require(path, audio=m4a)` for an extra-language track — before
it moves anything to the Desktop; nothing is sent for review without a passing gate either.

The film's own track and an extra track are two checks with two reports: `check FILM.mp4` vouches for the mp4 as it
plays, `check FILM.mp4 --audio X.m4a` for that m4a (against the same picture). Neither passes the other's gate.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import FAIL, LABEL, OUT, PASS, RANK, UNSURE, decode_audio, sha256  # noqa: E402
import decisions as store  # noqa: E402
import spec as specmod  # noqa: E402


def out_dir_for(video: Path, spec: dict | None, given: str | None, audio: Path | None = None) -> Path:
    if given:
        return Path(given).resolve()
    name = (spec or {}).get("film") or video.stem
    # an extra track gets its own folder: its report must not overwrite the report on the film's own track
    return OUT / (name if audio is None else f"{name}+{audio.stem}")


def status(report: dict, decisions: dict) -> dict:
    """A decision counts only while it still holds (decisions.holds: a line's approval is for one recording)."""
    fails = [i for i in report["items"] if i["verdict"] == FAIL]
    unsure = [i for i in report["items"] if i["verdict"] == UNSURE]
    said = {i["key"]: store.decision_for(i, decisions) for i in unsure}
    waiting = [i for i in unsure if said[i["key"]] is None]
    redo = [i for i in unsure if said[i["key"]] == "redo"]
    incomplete = report.get("incomplete", [])
    ok = not fails and not waiting and not redo and not incomplete
    return {"ok": ok, "incomplete": len(incomplete), "fail": len(fails), "unsure": len(unsure), "waiting": len(waiting), "redo": len(redo),
            "approved": len(unsure) - len(waiting) - len(redo)}


def cmd_check(args) -> int:
    video = Path(args.video).resolve()
    audio = Path(args.audio).resolve() if args.audio else None
    spec = specmod.load(Path(args.spec)) if args.spec else specmod.normalise({"film": video.stem})
    out = out_dir_for(video, spec, args.out, audio)
    out.mkdir(parents=True, exist_ok=True)
    print(f"检查 {video.name}" + (f" + {audio.name}" if audio else "") + f" → {out}", flush=True)
    digest, audio_digest = sha256(video), sha256(audio) if audio else None
    items, skipped, sections = [], [], {}
    played = decode_audio(audio or video)

    import fmt
    info, found = fmt.video_format(video, spec)
    sections["format"] = info
    items += found
    if audio:
        info, found = fmt.audio_file(audio, sections["format"].get("duration"))
        sections["audio_file"] = info
        items += found
    info, found = fmt.captions(spec, sections["format"].get("duration"))
    sections["captions"] = info
    items += found
    if not spec.get("captions"):
        skipped.append("字幕（spec 里没有 captions）")

    import mix
    info, found = mix.loudness(audio or video, spec)
    sections["loudness"] = info
    items += found
    info, found = mix.ducking(played, spec)
    sections["ducking"] = info
    items += found
    if info.get("skipped"):
        skipped.append("音乐压低（" + info["skipped"] + "）")

    if spec["lines"] and not args.no_narration:
        import narration
        voice = decode_audio(Path(spec["voice_audio"])) if spec.get("voice_audio") else None
        if voice is None:
            skipped.append("咔哒声和句子音量（spec 里没有单独的人声音轨 voice_audio）")
        listener = narration.Listener(out / "asr-cache.json")
        items += narration.lint(spec) if args.lint else []
        try:
            results, found = narration.check(spec, played, voice, listener)
        finally:
            listener.save()
        sections["narration"] = results
        items += found
    elif not spec["lines"]:
        skipped.append("配音校对（spec 里没有 lines）")

    if not args.no_picture:
        try:
            import picture
        except ImportError:
            picture = None
        if picture is not None:
            info, found = picture.check(video, spec, out)
            sections["picture"] = info
            items += found
        else:
            skipped.append("画面检查（还没装 picture.py）")

    # A report only counts for the gate when every check that applies to this film ran.
    ran = [k for k in ("format", "captions", "loudness", "ducking", "narration", "picture") if k in sections]
    incomplete = []
    if not args.spec:
        incomplete.append("没有 spec（qa-spec.json）：不知道片子该有什么")
    if "picture" not in sections:
        incomplete.append("画面检查没跑")
    if spec["kind"] in ("narrated",) and not spec["lines"]:
        incomplete.append("这是有旁白的片子，但 spec 里没有台词（lines）")
    if spec["lines"] and "narration" not in sections:
        incomplete.append("配音校对没跑")
    if not spec.get("_music_declared"):
        incomplete.append("spec 没写有没有背景音乐（music: true / false）")
    seen = set()
    items = [i for i in items if not (i["key"] in seen or seen.add(i["key"]))]
    items.sort(key=lambda i: (-RANK[i["verdict"]], i.get("t0", -1)))
    report = {"video": str(video), "audio": str(audio) if audio else None,
              "sha256": digest, "audio_sha256": audio_digest, "spec": str(Path(args.spec).resolve()) if args.spec else None,
              "film": spec.get("film"), "created": dt.datetime.now().isoformat(timespec="seconds"),
              "items": items, "skipped": skipped, "ran": ran, "incomplete": incomplete, "sections": sections}
    (out / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    for gone in store.prune(out, report):
        print(f"  之前的决定作废（这一句换了录音，要重新听）：{gone.get('title') or gone['key']}")
    import page
    page.build(out, report, video, audio)
    st = status(report, store.load(out))
    print(summary(report, st, out))
    return 0 if st["ok"] else (2 if st["fail"] or st["redo"] else 1)


def summary(report: dict, st: dict, out: Path) -> str:
    name = Path(report["video"]).name + (f" + {Path(report['audio']).name}" if report.get("audio") else "")
    lines = [f"\n{name}: 不通过 {st['fail']} · 拿不准 {st['unsure']}"
             f"（已通过 {st['approved']}，要重配 {st['redo']}，等你听 {st['waiting']}）"]
    decisions = store.load(out)
    for i in report["items"]:
        if i["verdict"] != PASS:
            d = decisions.get(i["key"]) if i["verdict"] == UNSURE else None
            d = d if store.holds(i, d) else {}
            tag = LABEL[i["verdict"]] + {"pass": "·已通过", "redo": "·要重配"}.get(d.get("decision"), "")
            note = f"（备注：{d['note']}）" if d.get("note") else ""
            lines.append(f"  [{tag}] {i['title']}{note}" + (f" — {i['detail'][:90]}" if i["detail"] else ""))
    auto = [i for i in report["items"] if i["code"] == "narration.second_pass"]
    if auto:
        lines.append(f"  [自动放过] {len(auto)} 句：medium 听错、small 听对（试听页底部可以听）："
                     + "、".join(i["line"] for i in auto))
    for s in report.get("incomplete", []):
        lines.append(f"  [没跑全] {s}")
    for s in report["skipped"]:
        lines.append(f"  [跳过] {s}")
    lines.append(f"报告：{out / 'report.json'}\n试听页：python3 scripts/qa/qa.py serve {out}")
    return "\n".join(lines)


def find_report(video: Path, out: str | None, audio: Path | None = None) -> tuple[Path | None, dict | None, str]:
    """The report of a check of exactly these bytes: this film and, for an extra track, this audio file. Without
    `audio` only a check of the film's own track counts — a run with --audio never listened to it."""
    digest, audio_digest = sha256(video), sha256(audio) if audio else None
    dirs = [Path(out)] if out else sorted(OUT.glob("*/"), key=lambda p: -p.stat().st_mtime)
    for d in dirs:
        p = d / "report.json"
        if p.exists():
            r = json.loads(p.read_text(encoding="utf-8"))
            if r.get("sha256") == digest and bool(r.get("audio")) == bool(audio) and r.get("audio_sha256") == audio_digest:
                return d, r, digest
    return None, None, digest


def require(video, out: str | None = None, audio=None) -> None:
    """For package/preview scripts: stop unless this exact file passed (and Yancy decided every 拿不准). With
    `audio` (an extra-language m4a): stop unless that exact audio file passed against this exact film."""
    video, audio = Path(video).resolve(), Path(audio).resolve() if audio else None
    d, r, digest = find_report(video, out, audio)
    if r is None:
        what = f"{video.name} + {audio.name}" if audio else video.name
        hint = f"qa.py check {video}" + (f" --audio {audio}" if audio else "") + " --spec …"
        others = [x for x in (OUT.glob("*/report.json") if not out else Path(out).glob("report.json"))
                  if json.loads(x.read_text(encoding="utf-8")).get("sha256") == digest]
        why = ("这个音频文件没查过，或者查过之后文件变了" if audio else
               "只查过外挂音轨，片子自带的音轨还没查过" if others else "自动检测没跑过这个文件")
        raise SystemExit(f"{what}：{why}（视频 sha256 {digest[:12]}…）：先运行 {hint}")
    st = status(r, store.load(d))
    if not st["ok"]:
        raise SystemExit(summary(r, st, d) + "\n自动检测没通过，不能打包或发送。")


def cmd_gate(args) -> int:
    try:
        require(args.video, args.out, args.audio)
    except SystemExit as e:
        print(e)
        return 1
    print(f"{Path(args.video).name}" + (f" + {Path(args.audio).name}" if args.audio else "") + "：自动检测通过。")
    return 0


def cmd_decide(args) -> int:
    """Decisions without the listening server: one key, or the JSON the page's 复制 button gives."""
    folder = Path(args.dir).resolve()
    report = json.loads((folder / "report.json").read_text(encoding="utf-8"))
    if args.file:
        pasted = json.loads(Path(args.file).read_text(encoding="utf-8"))
        if pasted.get("report") != store.report_id(report):
            raise SystemExit("这份选择是在另一次检查的试听页上做的（片子后来重新检查过）：请打开现在的 review.html 再听一遍。")
        todo = [(k, d.get("decision"), d.get("note", "")) for k, d in pasted["decisions"].items()]
    elif args.key and args.decision:
        todo = [(args.key, None if args.decision == "clear" else args.decision, args.note or "")]
    else:
        raise SystemExit("用法：qa.py decide DIR KEY pass|redo|clear [--note …]，或 qa.py decide DIR --from 复制出来的.json")
    for key, decision, note in todo:
        try:
            store.record(folder, key, decision, note)
        except KeyError:
            print(f"  跳过 {key}：现在的报告里没有这一条（片子重新检查过了，请在新的试听页上决定）")
    st = status(report, store.load(folder))
    print(summary(report, st, folder))
    return 0 if st["ok"] else (2 if st["fail"] or st["redo"] else 1)


def cmd_spec(args) -> int:
    if args.adapter == "zhongying":
        s = specmod.from_zhongying(Path(args.source[0]))
    else:
        lines, caps = [], []
        for src in args.source:
            path, _, lang = src.rpartition(":")
            lines += specmod.from_srt(Path(path), lang)
            caps.append({"path": str(Path(path).resolve()), "lang": lang})
        s = specmod.normalise({"film": args.film or Path(args.source[0].rpartition(":")[0]).stem.split(".")[0],
                               "kind": args.kind, "music": args.music, "lines": lines, "captions": caps})
        if len(caps) > 1:
            print("注意：多份字幕时，只有片子实际在说的那种语言该进 lines；请删掉另一种语言的 lines。")
    out = Path(args.o)
    out.parent.mkdir(parents=True, exist_ok=True)
    specmod.save(s, out)
    print(f"{out}: {len(s['lines'])} 句")
    return 0


def cmd_lint(args) -> int:
    import narration
    found = narration.lint(specmod.load(Path(args.spec)))
    for i in found:
        print(f"[{LABEL[i['verdict']]}] {i['title']}\n    {i['detail']}")
    print(f"{len(found)} 处要改" if found else "稿子没有已知的易错写法。")
    return 1 if found else 0


def cmd_upload(args) -> int:
    import upload
    from common import LABEL as L
    info, found = upload.check_folder(Path(args.folder), require, narrated=args.narrated or None)
    for i in found:
        print(f"[{L[i['verdict']]}] {i['title']}" + (f"\n    {i['detail']}" if i["detail"] else ""))
    fails = [i for i in found if i["verdict"] == FAIL]
    print(f"\n{Path(args.folder).name}：" + ("上传包符合规范。" if not found else
          f"{len(fails)} 处不通过，{len(found) - len(fails)} 处要看一下。"))
    return 2 if fails else (1 if found else 0)


def cmd_serve(args) -> int:
    import serve
    serve.run(Path(args.dir).resolve(), args.port)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check")
    c.add_argument("video")
    c.add_argument("--spec")
    c.add_argument("--audio", help="check this audio instead of the video's own track (e.g. the en m4a)")
    c.add_argument("--out")
    c.add_argument("--lint", action="store_true", help="also flag known pitfall spellings in the spoken text")
    c.add_argument("--no-narration", action="store_true")
    c.add_argument("--no-picture", action="store_true")
    c.set_defaults(fn=cmd_check)
    g = sub.add_parser("gate")
    g.add_argument("video")
    g.add_argument("--audio", help="gate this extra-language audio file (checked with `check --audio`) with the film")
    g.add_argument("--out")
    g.set_defaults(fn=cmd_gate)
    d = sub.add_parser("decide", help="save 通过 / 重配 without the listening server")
    d.add_argument("dir")
    d.add_argument("key", nargs="?")
    d.add_argument("decision", nargs="?", choices=["pass", "redo", "clear"])
    d.add_argument("--note")
    d.add_argument("--from", dest="file", help="the JSON copied from the listening page")
    d.set_defaults(fn=cmd_decide)
    s = sub.add_parser("spec")
    s.add_argument("adapter", choices=["zhongying", "srt"])
    s.add_argument("source", nargs="+", help="timeline.json, or SRT files as path:lang")
    s.add_argument("-o", required=True)
    s.add_argument("--film")
    s.add_argument("--kind", default="narrated", choices=["narrated", "music", "short"])
    s.add_argument("--music", action="store_true", help="the film has a music bed under the voices")
    s.set_defaults(fn=cmd_spec)
    l = sub.add_parser("lint")
    l.add_argument("spec")
    l.set_defaults(fn=cmd_lint)
    u = sub.add_parser("upload", help="check a Desktop 「<片名>-上传」 folder before it is handed over")
    u.add_argument("folder")
    u.add_argument("--narrated", action="store_true", help="require both SRTs even if none are in the folder")
    u.set_defaults(fn=cmd_upload)
    v = sub.add_parser("serve")
    v.add_argument("dir")
    v.add_argument("--port", type=int, default=8766)
    v.set_defaults(fn=cmd_serve)
    args = ap.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
