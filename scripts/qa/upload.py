"""最后输出的规范: the Desktop 「<片名>-上传」 folder, checked before Yancy is told it is ready.

    python3 scripts/qa/qa.py upload ~/Desktop/<片名>-上传

What a folder must hold (README "Automatic checks", "YouTube tags", memory: upload folder only uploads):
- only upload files: the mp4(s), youtube-description*.txt, the cover(s), the SRTs, an extra-language m4a;
- every mp4 passed the automatic checks (`qa.py gate`: same sha256, nothing failed, every 拿不准 decided);
- a narrated film's two caption files, zh-Hans and en;
- covers 1280×720, under 2 MB (YouTube's limit);
- each description file laid out 【标题】【简介】【标签】【上传设置】, where
  · 简介 STARTS with the chapters (owner, 2026-11-20: 「简介最开始就是分章节」): first line `0:00 …`, at least three,
    in order, each at least 10 s, all inside the film — YouTube's own chapter rules;
  · 简介 ends with the hashtag line, the default tags first, all lowercase, at most 60;
  · 【标签】 is there (「要带tags」): `#tag #tag`, lowercase, no spaces inside a tag, the defaults included,
    at most 500 characters;
  · no < or > (YouTube rejects them), at most 5000 characters; a title of at most 100 characters.
Shorts (vertical) have no chapters.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from common import FAIL, UNSURE, ffprobe, item

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from youtube_tags import DEFAULT, MAX_HASHTAGS, MAX_TAGS_CHARS  # noqa: E402

UPLOAD_EXT = {".mp4", ".txt", ".jpg", ".jpeg", ".png", ".srt", ".m4a"}
SECTION = re.compile(r"^【([^】/]+?)\s*(?:/\s*[^】]*)?】(.*)$")
CHAPTER = re.compile(r"^\s*((?:\d+:)?\d{1,2}:\d{2})\s+(\S.*)$")
TAG = re.compile(r"#[^\s#]+")


def seconds(stamp: str) -> int:
    parts = [int(p) for p in stamp.split(":")]
    return sum(p * 60 ** k for k, p in enumerate(reversed(parts)))


def sections(text: str) -> dict[str, str]:
    out, cur = {}, None
    for row in text.splitlines():
        m = SECTION.match(row.strip())
        if m:
            cur = m[1].strip()
            out[cur] = ""
            continue
        if cur:
            out[cur] += row + "\n"
    return {k: v.strip("\n") for k, v in out.items()}


def check_description(path: Path, duration: float | None, short: bool) -> list[dict]:
    """One file may hold several videos (a shorts package: blocks between ━━━━ name ━━━━ lines); each block with a
    【标题】 is checked on its own, and 【上传设置】 may be shared."""
    text = path.read_text(encoding="utf-8")
    blocks = re.split(r"(?m)^━+\s*(.*?)\s*━+\s*$", text)
    found = []
    if "上传设置" not in sections(text):
        found.append(item("upload", FAIL, "upload.section.上传设置", f"{path.name}：缺少【上传设置】",
                          "上传说明的格式：【标题】【简介】【标签】【上传设置】", key=f"upload.section.上传设置.{path.name}"))
    if len(blocks) == 1:
        return found + check_block(sections(text), path.name, duration, short)
    named = [(blocks[k], blocks[k + 1]) for k in range(1, len(blocks) - 1, 2)]
    for label, body in named:
        sec = sections(body)
        if "标题" in sec:
            found += check_block(sec, f"{path.name}「{label}」", None, short)
    return found


def check_block(sec: dict, name: str, duration: float | None, short: bool) -> list[dict]:
    found = []

    def bad(code, title, detail="", verdict=FAIL):
        found.append(item("upload", verdict, code, f"{name}：{title}", detail, key=f"{code}.{name}"))

    for need in ("标题", "简介", "标签"):
        if need not in sec:
            bad(f"upload.section.{need}", f"缺少【{need}】", "上传说明的格式：【标题】【简介】【标签】【上传设置】")
    title = sec.get("标题", "").strip()
    if "标题" in sec and not (0 < len(title) <= 100):
        bad("upload.title", f"标题有 {len(title)} 个字符（YouTube 上限 100）", title[:120])
    desc = sec.get("简介", "")
    if desc:
        if len(desc) > 5000:
            bad("upload.desc_length", f"简介有 {len(desc)} 个字符（YouTube 上限 5000）")
        if re.search(r"[<>]", desc):
            bad("upload.desc_brackets", "简介里有 < 或 >，YouTube 不接受", "、".join(sorted(set(re.findall(r"[<>]", desc)))))
        rows = [r for r in desc.splitlines()]
        first = next((r for r in rows if r.strip()), "")
        if not short:
            chapters = []
            for r in rows:
                if not r.strip():
                    if chapters:
                        break
                    continue
                m = CHAPTER.match(r)
                if not m:
                    break
                chapters.append((seconds(m[1]), m[2].strip(), r.strip()))
            if not CHAPTER.match(first) or seconds(CHAPTER.match(first)[1]) != 0:
                bad("upload.chapters_first", "简介开头不是章节", f"第一行应是「0:00 …」，现在是：{first[:60]}")
            elif len(chapters) < 3:
                bad("upload.chapters_count", f"只有 {len(chapters)} 个章节（YouTube 至少要 3 个）")
            else:
                times = [c[0] for c in chapters]
                short_ch = [c[2] for a, c in zip(chapters, chapters[1:]) if c[0] - a[0] < 10]
                if any(b <= a for a, b in zip(times, times[1:])):
                    bad("upload.chapters_order", "章节时间没有按顺序递增", " / ".join(c[2] for c in chapters))
                if short_ch:
                    bad("upload.chapters_short", "有章节不到 10 秒（YouTube 要求每章至少 10 秒）", "、".join(short_ch))
                if duration and (times[-1] > duration - 10):
                    bad("upload.chapters_end", f"最后一章 {chapters[-1][2]} 超出片长或不到 10 秒", f"片长 {duration:.0f} 秒")
            other = [r.strip() for r in rows[len(chapters) + 1:] if CHAPTER.match(r)]
            if other and chapters:
                bad("upload.chapters_split", "简介后面还有时间点，章节要连成一块放在最前面", "、".join(other[:5]), UNSURE)
        last = next((r for r in reversed(rows) if r.strip()), "")
        tags_line = TAG.findall(last)
        if not tags_line or len(" ".join(tags_line)) < len(last.strip()) * 0.8:
            bad("upload.hashtags", "简介最后一行不是 hashtag 行", last[:80])
        else:
            want_head = [f"#{t}" for t in DEFAULT[:3]]
            if short and tags_line[:1] == ["#shorts"]:
                tags_line = tags_line[1:]
            if tags_line[:3] != want_head:
                bad("upload.hashtags_head", "hashtag 行要以默认标签开头（YouTube 在标题上方显示前三个）",
                    f"应以 {' '.join(want_head)} 开头")
            if len(tags_line) > MAX_HASHTAGS:
                bad("upload.hashtags_many", f"{len(tags_line)} 个 hashtag（超过 {MAX_HASHTAGS} 个 YouTube 会全部忽略）")
            upper = [t for t in tags_line if t != t.lower()]
            if upper:
                bad("upload.hashtags_case", "hashtag 要全部小写", " ".join(upper[:8]))
        if "Louise Yang" in desc and "voice" not in desc.split("Louise Yang")[0][-40:]:
            bad("upload.byline", "作者行有 Louise Yang（默认只写 Yancy Qin）", "", UNSURE)
    tags = sec.get("标签", "").strip()
    if "标签" in sec:
        toks = tags.split()
        if not toks:
            bad("upload.tags_empty", "【标签】是空的")
        else:
            wrong = [t for t in toks if not re.fullmatch(r"#[^\s#,，]+", t)]
            if wrong or "," in tags or "，" in tags:
                bad("upload.tags_format", "标签要写成 #tag #tag（# 加空格分隔，标签里面没有空格和逗号）",
                    " ".join(wrong[:8]) or tags[:80])
            upper = [t for t in toks if t != t.lower()]
            if upper:
                bad("upload.tags_case", "标签要全部小写", " ".join(upper[:8]))
            missing = [f"#{d}" for d in DEFAULT if f"#{d}" not in toks]
            if missing:
                bad("upload.tags_defaults", "缺少默认标签", " ".join(missing))
            if len(tags) > MAX_TAGS_CHARS:
                bad("upload.tags_length", f"标签有 {len(tags)} 个字符（上限 {MAX_TAGS_CHARS}）")
    return found


def check_folder(folder: Path, require_gate, narrated: bool | None = None) -> tuple[dict, list]:
    """require_gate(path) raises SystemExit with the reason when an mp4 has not passed."""
    folder = Path(folder).expanduser().resolve()
    found = []
    if not folder.is_dir():
        return {}, [item("upload", FAIL, "upload.folder", f"{folder} 不是文件夹", key="upload.folder")]
    files = sorted(p for p in folder.iterdir() if not p.name.startswith("."))
    stray = [p.name for p in files if p.is_dir() or p.suffix.lower() not in UPLOAD_EXT]
    if stray:
        found.append(item("upload", FAIL, "upload.stray", "上传文件夹里只放上传用的文件",
                          "多出来的：" + "、".join(stray), key="upload.stray"))
    mp4s = [p for p in files if p.suffix.lower() == ".mp4"]
    if not mp4s:
        found.append(item("upload", FAIL, "upload.no_video", "文件夹里没有 mp4", key="upload.no_video"))
    vertical, durations = True, {}
    for p in mp4s:
        info = ffprobe(p)
        v = next((s for s in info["streams"] if s["codec_type"] == "video"), {})
        vertical &= v.get("height", 0) > v.get("width", 1)
        durations[p.name] = float(info["format"]["duration"])
        try:
            require_gate(p)
        except SystemExit as e:
            found.append(item("upload", FAIL, "upload.gate", f"{p.name} 没通过自动检测", str(e).splitlines()[0],
                              key=f"upload.gate.{p.name}"))
    short = bool(mp4s) and vertical
    descs = [p for p in files if p.name.startswith("youtube-description") and p.suffix == ".txt"]
    if not descs:
        found.append(item("upload", FAIL, "upload.no_description", "缺少上传说明 youtube-description*.txt",
                          key="upload.no_description"))
    duration = next(iter(durations.values())) if len(durations) == 1 else None
    for d in descs:
        found += check_description(d, duration, short)
    covers = [p for p in files if p.suffix.lower() in (".jpg", ".jpeg", ".png")]
    if not covers and not short:
        found.append(item("upload", FAIL, "upload.no_cover", "缺少封面", key="upload.no_cover"))
    for c in covers:
        v = next(s for s in ffprobe(c)["streams"] if s["codec_type"] == "video")
        if (v["width"], v["height"]) != (1280, 720) and not short:
            found.append(item("upload", FAIL, "upload.cover_size", f"{c.name} 是 {v['width']}×{v['height']}，封面要 1280×720",
                              key=f"upload.cover_size.{c.name}"))
        if c.stat().st_size > 2 * 1024 * 1024:
            found.append(item("upload", FAIL, "upload.cover_bytes", f"{c.name} 超过 2 MB（YouTube 上限）",
                              key=f"upload.cover_bytes.{c.name}"))
    srts = [p.name for p in files if p.suffix.lower() == ".srt"]
    if (narrated or srts) and not short:
        for lang, pat in (("中文", r"\.zh(-hans|-cn)?\.srt$"), ("英文", r"\.en\.srt$")):
            if not any(re.search(pat, s, re.I) for s in srts):
                found.append(item("upload", FAIL, "upload.srt", f"缺少{lang}字幕 SRT", "每部有旁白的片子都要中英两份字幕",
                                  key=f"upload.srt.{lang}"))
    info = {"folder": str(folder), "videos": durations, "short": short, "descriptions": [d.name for d in descs],
            "covers": [c.name for c in covers], "srts": srts}
    return info, found
