"""格式和字幕: what YouTube gets (resolution, frame rate, codecs, duration) and the two caption files."""
from __future__ import annotations

import re
from pathlib import Path

from common import FAIL, UNSURE, ffprobe, item
from spec import read_srt


def video_format(path: Path, spec: dict) -> tuple[dict, list]:
    p = ffprobe(path)
    v = next((s for s in p["streams"] if s["codec_type"] == "video"), None)
    a = next((s for s in p["streams"] if s["codec_type"] == "audio"), None)
    want = {"width": 1920, "height": 1080, "fps": 30}
    if spec.get("kind") == "short":
        want.update(width=1080, height=1920)
    want.update(spec.get("format") or {})
    found = []

    def bad(code, title, detail=""):
        found.append(item("format", FAIL, code, title, detail, key=code))

    if v is None:
        bad("format.no_video", "没有视频流")
        return {}, found
    num, den = (int(x) for x in v["r_frame_rate"].split("/"))
    fps = num / den
    info = {"width": v["width"], "height": v["height"], "fps": round(fps, 3), "vcodec": v["codec_name"],
            "pix_fmt": v.get("pix_fmt"), "duration": float(p["format"]["duration"]),
            "acodec": a and a["codec_name"], "channels": a and a.get("channels"), "sample_rate": a and a.get("sample_rate"),
            "audio_streams": sum(s["codec_type"] == "audio" for s in p["streams"])}
    if (v["width"], v["height"]) != (want["width"], want["height"]):
        bad("format.size", f"分辨率 {v['width']}×{v['height']}，应为 {want['width']}×{want['height']}")
    if abs(fps - want["fps"]) > 0.01:
        bad("format.fps", f"帧率 {fps:.3f}，应为 {want['fps']}")
    if v["codec_name"] != "h264" or v.get("pix_fmt") != "yuv420p":
        bad("format.codec", f"视频编码 {v['codec_name']}/{v.get('pix_fmt')}，应为 h264/yuv420p",
            f"color_range={v.get('color_range', '?')}（pc = 全范围，YouTube 要 tv）；渲染时加 -pix_fmt yuv420p"
            " -color_range tv -colorspace bt709 -color_primaries bt709 -color_trc bt709")
    if a is None:
        bad("format.no_audio", "没有音轨")
    else:
        if a["codec_name"] != "aac" or int(a.get("sample_rate", 0)) != 48000 or a.get("channels") != 2:
            bad("format.audio", f"音频 {a['codec_name']} {a.get('sample_rate')} Hz {a.get('channels')} 声道，应为 aac 48000 Hz 立体声")
        vd, ad = float(v.get("duration") or 0), float(a.get("duration") or 0)
        if vd and ad and abs(vd - ad) > 1 / want["fps"] + 0.05:
            bad("format.av_length", f"音视频长度差 {abs(vd - ad):.2f} 秒")
    if want.get("duration"):
        tol = want.get("tol", 0.15)
        if abs(info["duration"] - want["duration"]) > tol:
            bad("format.duration", f"时长 {info['duration']:.2f} 秒，时间线是 {want['duration']:.2f} 秒")
    return info, found


def audio_file(path: Path, video_duration: float | None) -> tuple[dict, list]:
    """An extra-language track delivered beside the film (`check --audio`): the same audio rules as the film's own
    track, and as long as the picture."""
    p = ffprobe(path)
    a = next((s for s in p["streams"] if s["codec_type"] == "audio"), None)
    name = Path(path).name
    if a is None:
        return {"file": name}, [item("format", FAIL, "format.alt_no_audio", f"{name} 里没有音轨", key="format.alt_no_audio")]
    info = {"file": name, "acodec": a["codec_name"], "channels": a.get("channels"), "sample_rate": a.get("sample_rate"),
            "duration": float(p["format"]["duration"])}
    found = []
    if a["codec_name"] != "aac" or int(a.get("sample_rate", 0)) != 48000 or a.get("channels") != 2:
        found.append(item("format", FAIL, "format.alt_audio",
                          f"{name}：音频 {a['codec_name']} {a.get('sample_rate')} Hz {a.get('channels')} 声道，应为 aac 48000 Hz 立体声",
                          key="format.alt_audio"))
    if video_duration and abs(info["duration"] - video_duration) > 0.25:
        found.append(item("format", FAIL, "format.alt_length",
                          f"{name} 长 {info['duration']:.2f} 秒，片子长 {video_duration:.2f} 秒", key="format.alt_length"))
    return info, found


def width(s: str) -> float:
    return sum(1 if re.match(r"[^\x00-\x7f]", ch) else 0.5 for ch in s)


def captions(spec: dict, duration: float | None) -> tuple[dict, list]:
    caps = spec.get("captions") or []
    found = []
    if spec.get("kind") == "narrated" and caps:
        langs = {c["lang"] for c in caps}
        for need in ("zh", "en"):
            if need not in langs:
                found.append(item("captions", FAIL, "captions.missing", f"缺少{'中文' if need == 'zh' else '英文'}字幕",
                                  "每部有旁白的片子都要中英两份 SRT", key=f"captions.missing.{need}"))
    info = {}
    for c in caps:
        path, lang = Path(c["path"]), c["lang"]
        name = path.name
        if not path.exists():
            found.append(item("captions", FAIL, "captions.file", f"{name} 不存在", key=f"captions.file.{name}"))
            continue
        blocks = read_srt(path)
        info[name] = len(blocks)
        limit = 22 if lang == "zh" else 42
        problems = []
        prev_end = 0.0
        for k, b in enumerate(blocks, 1):
            if b["index"] is not None and b["index"] != str(k):
                problems.append(f"第 {k} 条编号是 {b['index']}")
            if b["end"] <= b["start"]:
                problems.append(f"第 {k} 条结束不晚于开始")
            if b["start"] < prev_end - 0.001:
                problems.append(f"第 {k} 条和上一条重叠")
            prev_end = b["end"]
            if duration and b["end"] > duration + 0.05:
                problems.append(f"第 {k} 条超出片长")
            if len(b["lines"]) > 2:
                problems.append(f"第 {k} 条有 {len(b['lines'])} 行")
            for row in b["lines"]:
                w = width(row) if lang == "zh" else len(row)
                if w > limit:
                    problems.append(f"第 {k} 条一行太长（{w:g} > {limit}）：{row}")
                if re.search(r"<[^>]+>", row):
                    problems.append(f"第 {k} 条有标签：{row}")
        if problems:
            found.append(item("captions", FAIL, "captions.format", f"{name}：{len(problems)} 处格式问题",
                              "；".join(problems[:12]) + ("…" if len(problems) > 12 else ""), key=f"captions.format.{name}"))
    return info, found
