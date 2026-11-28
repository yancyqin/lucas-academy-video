"""Delivery check and upload text for "We Build A BlackHole with AI" (BLACK-HOLE-AI.md "Delivery and QA").

Never uploads and moves nothing out of the repo: everything lands in out/black-hole-ai/delivery/.
  delivery-check.json   the film (1920×1080, 30 fps, English then Chinese AAC, length = timeline), the Chinese M4A
                        (same length), both SRTs, -16 LUFS ±0.5 and true peak <= -1.0 dBTP for every track
  upload.en.txt / upload.zh.txt
                        scripts/youtube_text.py: each description STARTS with the full chapter list from 0:00
                        (AGENTS.md "YouTube description order"), then the text, sources, credits and hashtags
It then asks the global QA gate (scripts/qa/qa.py require) about the film and the Chinese track and says plainly if
they have not passed: the package is not ready to hand over until they do (AGENTS.md "Mandatory global QA").

  python3 scripts/black-hole-ai/package.py [--qa DIR_WITH_qa.py]
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PUB = ROOT / "public/black-hole-ai"
OUT = ROOT / "out/black-hole-ai"
DELIVERY = OUT / "delivery"
FILM = "black-hole-ai"
sys.path.insert(0, str(ROOT / "scripts"))
from youtube_text import upload_text  # noqa: E402

TITLE = "We Build A BlackHole with AI"
SITE = "https://is.lucasacademy.org"
TOPICS = ["blackhole", "physics", "astronomy", "space", "raytracing", "generalrelativity", "ai", "coding", "黑洞"]
REFERENCES = """NASA Goddard Scientific Visualization Studio — SVS 13326 (J. Schnittman): the colours of our gas.
O. James, E. von Tunzelmann, P. Franklin, K. S. Thorne (2015), "Gravitational lensing by spinning black holes in astrophysics, and in the movie Interstellar", Class. Quantum Grav. 32, 065001.
NASA Goddard visualization, 2024 — a plunge into a black hole (SVS 14576)."""
MUSIC = "Frédéric Chopin, Nocturne in C-sharp minor, B. 49 — Frank Lévy, piano (Musopen, public domain)."


def probe(path: Path) -> dict:
    return json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)],
                                     capture_output=True, text=True, check=True).stdout)


def loudness(path: Path, stream: str = "a:0") -> tuple[float, float]:
    err = subprocess.run(["ffmpeg", "-nostats", "-hide_banner", "-i", str(path), "-map", f"0:{stream}", "-af", "ebur128=peak=true",
                          "-f", "null", "-"], capture_output=True, text=True).stderr
    summary = err[err.rfind("Summary:"):]
    return float(re.search(r"I:\s+(-?[\d.]+) LUFS", summary)[1]), float(re.search(r"Peak:\s+(-?[\d.]+|-inf) dBFS", summary)[1])


def check(tl: dict) -> dict:
    film, m4a = DELIVERY / f"{FILM}.mp4", DELIVERY / f"{FILM}.zh.m4a"
    p, q = probe(film), probe(m4a)
    v = next(s for s in p["streams"] if s["codec_type"] == "video")
    audio = [s for s in p["streams"] if s["codec_type"] == "audio"]
    report = {"film": {"file": film.name, "bytes": film.stat().st_size, "seconds": round(float(p["format"]["duration"]), 3),
                       "video": f"{v['codec_name']} {v.get('pix_fmt')} {v['width']}x{v['height']} {v['r_frame_rate']}",
                       "audio": [f"{s['codec_name']} {s.get('sample_rate')} Hz {s.get('channels')} ch {s.get('tags', {}).get('language')}"
                                 + (" default" if s.get("disposition", {}).get("default") else "") for s in audio]},
              "zh_m4a": {"file": m4a.name, "bytes": m4a.stat().st_size, "seconds": round(float(q["format"]["duration"]), 3)},
              "timelineSeconds": tl["durationSeconds"], "deliverable_timeline": tl["deliverable"], "misfits": tl["misfits"]}
    problems = []
    for i, lang in enumerate(("en", "zh")):
        lufs, tp = loudness(film, f"a:{i}")
        report["film"][f"a:{i} {lang}"] = {"lufs": lufs, "true_peak_dbtp": tp}
    lufs, tp = loudness(m4a)
    report["zh_m4a"].update(lufs=lufs, true_peak_dbtp=tp)
    for name, r in [("film a:0 en", report["film"]["a:0 en"]), ("film a:1 zh", report["film"]["a:1 zh"]), ("zh.m4a", report["zh_m4a"])]:
        if abs(r["lufs"] + 16) > 0.5:
            problems.append(f"{name}: {r['lufs']} LUFS (want -16 ±0.5)")
        if r["true_peak_dbtp"] > -1.0:
            problems.append(f"{name}: true peak {r['true_peak_dbtp']} dBTP (want <= -1.0)")
    if (v["width"], v["height"], v["r_frame_rate"]) != (1920, 1080, "30/1"):
        problems.append("picture is not 1920x1080 at 30 fps")
    if [s.get("tags", {}).get("language") for s in audio] != ["eng", "chi"]:
        problems.append("audio streams are not English then Chinese")
    if abs(report["film"]["seconds"] - tl["durationSeconds"]) > 0.1 or abs(report["zh_m4a"]["seconds"] - report["film"]["seconds"]) > 0.1:
        problems.append("lengths differ (film, timeline, Chinese track)")
    for name in (f"{FILM}.en.srt", f"{FILM}.zh-Hans.srt"):
        if not (DELIVERY / name).is_file():
            problems.append(f"{name} missing")
    if not tl["deliverable"]:
        problems.append("the timeline is not deliverable: " + "; ".join(m["id"] + " " + m["problem"] for m in tl["misfits"]))
    report["problems"] = problems
    return report


def chapters(tl: dict, lang: str) -> list[tuple[float, str]]:
    return [(s["start"], s[lang]) for s in tl["sections"]]


def texts(tl: dict, report: dict) -> dict:
    stamp = f"{int(report['film']['seconds'] // 60)}:{int(report['film']['seconds'] % 60):02d}"
    en_body = [
        "This black hole is not a movie effect: every pixel is a ray of light, traced backwards through Einstein's "
        "equations. We built it with AI: the shape of space around a spinning black hole (the Kerr metric), a careful "
        "step-by-step solver for every ray, a camera that can fall, glowing gas with its colour and Doppler shift, all on "
        "the graphics card, one ray per pixel. Then we checked it against a slow, exact CPU version, and against the math. "
        "Finally, we fall in: the last fifteen seconds play in real time, as they would for Sagittarius A*.",
        f"Fly it yourself: {SITE} — in The Manifold, open the Teleport Orb and choose Black Hole Journey.",
        "中文配音：在音轨设置里选「中文」。",
        "References (text only; no NASA or paper imagery is shown):\n" + REFERENCES,
        "Music: " + MUSIC + " Its quiet opening returns under the end.",
        "By Lucas Academy Team. The narration is AI-generated with Louise's licensed voices (English, and a Chinese audio "
        "track). Every picture comes from Lucas Academy's online museum and its black-hole study page.",
    ]
    zh_body = [
        "这个黑洞不是电影特效：你看到的每一个像素，都是一束光，沿着爱因斯坦的方程倒着追踪回去。我们和 AI 一起做出了它："
        "旋转黑洞周围空间的形状（克尔度规）、给每一束光的逐步求解器、一台能掉进去的相机、发光的气体和它的颜色与多普勒频移，"
        "全部在显卡上运行，每个像素一束光。我们还把它和一个又慢又精确的 CPU 版本对照，并用数学检验。"
        "最后我们掉进去：最后十五秒按真实时间播放，就像掉进银河系中心的人马座 A* 那样。",
        f"你自己来飞：{SITE} —— 在 Manifold 房间打开传送球，选择 Black Hole Journey。",
        "参考资料（只列文字，画面里没有使用 NASA 或论文的图像）：\n" + REFERENCES,
        "背景音乐：肖邦《升 c 小调夜曲》B. 49，Frank Lévy 演奏（Musopen，公有领域）。片尾回到它安静的开头。",
        "作者 Lucas Academy Team。配音为 AI 合成，使用 Louise 的授权声线（英文原声，另有中文音轨）。画面全部来自 Lucas Academy 的线上博物馆和它的黑洞调试页面。",
    ]
    settings = [
        f"Video: {FILM}.mp4 (1920×1080, 30 fps, {stamp}; first audio stream English, second Chinese)",
        f"Chinese audio track: {FILM}.zh.m4a (same length; Studio → Languages → Add audio track → Chinese)",
        f"Captions: {FILM}.en.srt (English), {FILM}.zh-Hans.srt (中文)",
        "Video language: English · Category: Education · Altered or synthetic content: yes (synthetic narration)",
        "Visibility: Unlisted unless the owner says otherwise (docs/PRODUCTION-CHECKLIST.md)",
        "Chinese title: not decided by the owner yet (the film's title is English only)",
    ]
    duration = report["film"]["seconds"]
    return {
        "en": upload_text(title=TITLE, chapters=chapters(tl, "en"), duration=duration, body=en_body, own_tags=TOPICS,
                          settings=settings, lang="en"),
        "zh": upload_text(title=TITLE, chapters=chapters(tl, "zh"), duration=duration, body=zh_body, own_tags=TOPICS,
                          settings=settings, lang="zh"),
    }


def gate(qa_dir: Path | None) -> list[str]:
    """What the global gate says about the delivered film and the Chinese track (nothing is forced or recorded)."""
    cands = [qa_dir] if qa_dir else [ROOT / "scripts/qa"]
    qa = next((c for c in cands if c and (c / "qa.py").is_file() and "music_source" in (c / "spec.py").read_text()), None)
    if qa is None:
        return ["global QA (with music-ducking rules) not found: run qa.py check/gate by hand"]
    out = []
    py = next((p / ".venv-align/bin/python" for p in [ROOT, *ROOT.parents] if (p / ".venv-align/bin/python").is_file()), Path(sys.executable))
    for track, extra in (("film", []), ("zh-track", ["--audio", str(DELIVERY / f"{FILM}.zh.m4a")])):
        r = subprocess.run([str(py), "-B", str(qa / "qa.py"), "gate", str(DELIVERY / f"{FILM}.mp4"), *extra, "--out", str(OUT / "qa" / track)],
                           capture_output=True, text=True)
        out.append(f"{track}: exit {r.returncode}: {(r.stdout + r.stderr).strip()}")
    return out


def main() -> None:
    qa_dir = Path(sys.argv[sys.argv.index("--qa") + 1]) if "--qa" in sys.argv else None
    tl = json.loads((PUB / "timeline.json").read_text())
    report = check(tl)
    for lang, text in texts(tl, report).items():
        (DELIVERY / f"upload.{lang}.txt").write_text(text, encoding="utf-8")
    report["gate"] = gate(qa_dir)
    (OUT / "delivery-check.json").write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=1))
    if report["problems"] or any("exit 0" not in g for g in report["gate"]):
        print("\nNOT READY TO HAND OVER: see problems and gate above.")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
