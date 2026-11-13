#!/usr/bin/env python3
"""Render a centred, reversible Moonlit Night loop and upload hashtags.

Only existing owner-approved Muse footage and the approved piano recording are
used. The forward half eases from source 0 to 8 seconds; its reverse completes
the loop with zero camera velocity at both turns. Music joins the first theme
to its repetition, using a short cyclic overlap rather than fading to silence.

Run through job.py for persistent logs and success/failure markers:
    python -u scripts/blue-wave/job.py shorts
    python -u scripts/blue-wave/job.py shorts --audio-only
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

import cv2
import numpy as np
from PIL import Image, ImageDraw
from scipy.io import wavfile

import walk

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from youtube_tags import hashtags, tags

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "debussy-impressions"))
from normalize import ebur128, render as normalize_audio

DATA = Path(walk.DATA)
OUT = DATA / "shorts"
DESKTOP = Path(os.environ.get("BLUE_WAVE_SHORTS_UPLOAD", "/Users/yqin/Desktop/月夜-短视频-上传"))
NAME = "月夜-循环短视频"
TITLE = "月夜 | 肖邦 夜曲 Op. 9, No. 2"
TITLE_EN = "Moonlit Night | Chopin Nocturne Op. 9, No. 2"
W, H, FPS = 1080, 1920, 30
HALF_FRAMES = 421
FRAMES = HALF_FRAMES * 2
DURATION = FRAMES / FPS
SOURCE_END = 8.0
# The delivered cycle starts 0.24 s later, just before the full 2.009 s
# downbeat. Joining in the preceding sustain preserves its complete attack.
AUDIO_START = 1.7
AUDIO_OVERLAP = .24
SR = 48000

FILM_TAGS = ["蓝色浪潮", "肖邦", "夜曲", "chopin", "nocturne", "op9no2", "piano",
             "classicalmusic", "古典音乐", "名画", "油画", "artinmotion", "hokusai",
             "monet", "degas", "vangogh", "kramskoi", "waterhouse", "whistler",
             "delacroix", "caspar david friedrich"]
SHORT_TAGS = ["月夜", "肖邦", "夜曲", "蓝色浪潮", "chopin", "nocturne", "op9no2",
              "piano", "classicalmusic", "kramskoi", "moonlitnight", "名画", "油画",
              "artinmotion", "loop", "shorts"]


def run(args, **kwargs):
    return subprocess.run([str(x) for x in args], check=True, **kwargs)


def probe(path):
    return json.loads(run(["ffprobe", "-v", "error", "-show_streams", "-show_format",
                           "-of", "json", path], capture_output=True, text=True).stdout)


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def hash_file(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(4 * 1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def keyword_text(title, title_en, own):
    return (title + "\n" + title_en + "\n\n说明末尾 #关键词：\n" + hashtags(own)
            + "\n\n上传关键词：\n" + tags(own) + "\n")


def make_audio():
    """Overlap a repeated phrase, then normalize in a periodic filter context."""
    n, x = round(DURATION * SR), round(AUDIO_OVERLAP * SR)
    result = run(["ffmpeg", "-v", "error", "-ss", AUDIO_START, "-i",
                  DATA / "music/normalized/levy.wav", "-t", (n + x) / SR,
                  "-ar", SR, "-ac", "2", "-f", "f32le", "-"], capture_output=True)
    samples = np.frombuffer(result.stdout, np.float32).reshape(-1, 2)
    if len(samples) != n + x:
        raise RuntimeError(f"Audio excerpt is short: {len(samples)} != {n+x}")
    u = np.linspace(0, 1, x, dtype=np.float32)
    weight = (u * u * (3 - 2 * u))[:, None]
    join = samples[n:n+x] * (1 - weight) + samples[:x] * weight
    loop = np.concatenate([samples[x:n], join])
    assert len(loop) == n
    # Padding with whole cycles gives resampling/limiting the same context at
    # either side of the delivered cycle, including the gain-reduction state.
    raw = OUT / "moonlit-audio-three-cycles.wav"
    normalized = OUT / "moonlit-audio-three-cycles-normalized.wav"
    audio = OUT / "moonlit-loop.wav"
    wavfile.write(raw, SR, np.tile(loop, (3, 1)))
    before, _, peak = ebur128(str(raw))
    gain = -18 - before
    limit = -1.5 if peak + gain > -1.3 else None
    for _ in range(3):
        normalize_audio(str(raw), str(normalized), gain, limit)
        run(["ffmpeg", "-v", "error", "-y", "-i", normalized, "-af",
             f"atrim=start_sample={n}:end_sample={2*n},asetpts=PTS-STARTPTS",
             "-c:a", "pcm_s24le", audio])
        loudness, _, true_peak = ebur128(str(audio))
        if abs(loudness + 18) <= .2 and true_peak <= -1.1:
            break
        gain += -18 - loudness
        if true_peak > -1.1:
            limit = (limit if limit is not None else -1.3) - (true_peak + 1.1) - .1
    if abs(loudness + 18) > .2 or true_peak > -1.1:
        raise RuntimeError(f"Audio normalization failed: {loudness}, {true_peak}")
    raw.unlink()
    normalized.unlink()
    return audio, {"source": str(DATA / "music/normalized/levy.wav"),
                   "excerpt_start_s": AUDIO_START,
                   "excerpt_end_s": AUDIO_START + DURATION + AUDIO_OVERLAP,
                   "overlap_s": AUDIO_OVERLAP, "samples": n,
                   "loop_starts_at_source_s": AUDIO_START + AUDIO_OVERLAP,
                   "gain_db": gain, "limiter_ceiling_dbtp": limit,
                   "lufs": loudness, "true_peak_dbtp": true_peak}


def render_half(source):
    half = OUT / "moonlit-forward-half.mp4"
    sw, sh, _ = walk.probe(source)
    x, y, fw, fh = walk.contain_bounds(sw, sh, W, H)
    assert x == 0 and y == H - y - fh, "Portrait must be centred"
    # Native aspect scales exactly to 1080x1530, retaining the whole source.
    cache = walk.interpolated(source, 0, SOURCE_END, (fw, fh))
    reader = walk.Reader(cache, fw, fh)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo",
                            "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                            "-i", "-", "-an", "-c:v", "libx264", "-threads", "3",
                            "-crf", "12", "-preset", "fast", "-pix_fmt", "yuv420p",
                            str(half)], stdin=subprocess.PIPE)
    try:
        for k in range(HALF_FRAMES):
            u = k / (HALF_FRAMES - 1)
            source_time = SOURCE_END * (1 - np.cos(np.pi * u)) / 2
            frame = walk.portrait(reader.frame(source_time * walk.IFPS), (W, H))
            enc.stdin.write(frame.tobytes())
            if k % 60 == 0:
                write_json(OUT / "progress.json", {"stage": "forward_half", "frame": k,
                           "frames": HALF_FRAMES, "source_time": source_time})
                print(f"forward half: {k}/{HALF_FRAMES}, source {source_time:.3f}s", flush=True)
        enc.stdin.close()
        if enc.wait():
            raise RuntimeError("Forward half encoding failed")
    finally:
        reader.close()
        if enc.poll() is None:
            enc.stdin.close()
            enc.terminate()
            enc.wait()
    meta = probe(half)
    vs = next(s for s in meta["streams"] if s["codec_type"] == "video")
    if int(vs["nb_frames"]) != HALF_FRAMES:
        raise RuntimeError("Incomplete forward half")
    return half, {"source": str(source), "source_range_s": [0, SOURCE_END],
                  "source_size": [sw, sh], "foreground_bounds": [x, y, fw, fh],
                  "camera": "cosine forward, then reverse", "half_frames": HALF_FRAMES,
                  "interpolation_fps": walk.IFPS, "cache": cache}


def verify(path):
    meta = probe(path)
    vs = next(s for s in meta["streams"] if s["codec_type"] == "video")
    aud = next(s for s in meta["streams"] if s["codec_type"] == "audio")
    assert (vs["width"], vs["height"]) == (W, H)
    assert vs["r_frame_rate"] == "30/1" and int(vs["nb_frames"]) == FRAMES
    assert abs(float(vs["duration"]) - DURATION) < .001
    assert abs(float(aud["duration"]) - DURATION) < .002
    cap = cv2.VideoCapture(str(path))
    first = previous = last = None
    steps, means, frames, thumbs = [], [], 0, []
    targets = {0, 90, 180, 300, HALF_FRAMES-1, 540, 660, FRAMES-31, FRAMES-1}
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        small = cv2.resize(frame, (270, 480), interpolation=cv2.INTER_AREA).astype(np.float32)
        if first is None:
            first = small.copy()
        if previous is not None:
            steps.append(float(np.abs(small - previous).mean()))
        means.append(float(small.mean()))
        if frames in targets:
            im = Image.fromarray(cv2.cvtColor(small.astype(np.uint8), cv2.COLOR_BGR2RGB))
            cell = Image.new("RGB", (270, 504), "#181a1c")
            cell.paste(im, (0, 0))
            ImageDraw.Draw(cell).text((8, 484), f"{frames/FPS:.2f}s", fill="white")
            thumbs.append(cell)
        previous = last = small
        frames += 1
    cap.release()
    if frames != FRAMES:
        raise RuntimeError(f"Decoded {frames}, expected {FRAMES}")
    seam = float(np.abs(first - last).mean())
    if seam > 1.0 or min(means) < 3 or max(steps) > 5:
        raise RuntimeError(f"Visual loop check failed: seam={seam}, brightness={min(means)}, step={max(steps)}")
    sheet = Image.new("RGB", (810, 1512), "#181a1c")
    for i, im in enumerate(thumbs):
        sheet.paste(im, ((i % 3) * 270, (i // 3) * 504))
    sheet.save(OUT / "check/contact.jpg", quality=94)
    pcm = np.frombuffer(run(["ffmpeg", "-v", "error", "-i", path, "-vn", "-t", DURATION,
                             "-f", "f32le", "-ar", SR, "-ac", "2", "-"],
                            capture_output=True).stdout, np.float32).reshape(-1, 2)
    if len(pcm) != round(SR * DURATION):
        raise RuntimeError("Decoded audio sample count mismatch")
    typical = float(np.percentile(np.abs(np.diff(pcm, axis=0)), 99))
    audio_seam = float(np.max(np.abs(pcm[0] - pcm[-1])))
    # A wrap may contain a normal waveform slope, but must not introduce a click.
    if audio_seam > max(.002, 3 * typical):
        raise RuntimeError(f"Audio seam too large: {audio_seam} / p99 {typical}")
    loudness, lra, peak = ebur128(str(path))
    if abs(loudness + 18) > .3 or peak > -1:
        raise RuntimeError(f"AAC loudness or peak failed: {loudness}, {peak}")
    report = {"decoded_frames": frames, "duration_s": DURATION, "resolution": [W, H],
              "fps": FPS, "loop_pixel_mae_0_255": seam, "max_frame_step": max(steps),
              "median_frame_step": float(np.median(steps)), "min_frame_mean": min(means),
              "decoded_audio_samples": len(pcm), "audio_wrap_step": audio_seam,
              "audio_sample_step_p99": typical, "lufs": loudness, "lra": lra,
              "true_peak_dbtp": peak, "ffprobe": meta}
    write_json(OUT / "check/validation.json", report)
    return report


def main():
    started = time.time()
    (OUT / "check").mkdir(parents=True, exist_ok=True)
    DESKTOP.mkdir(parents=True, exist_ok=True)
    walk.W, walk.H = W, H
    source = DATA / "footage/muse/sharp/04-kramskoi-moonlit.mp4"
    film_keywords = keyword_text("蓝色浪潮 | 肖邦 夜曲 Op. 9, No. 2",
                                 "Blue Wave | Chopin Nocturne Op. 9, No. 2", FILM_TAGS)
    (DATA / "film/关键词.txt").write_text(film_keywords)
    (DESKTOP / "蓝色浪潮-长片关键词.txt").write_text(film_keywords)
    (DESKTOP / "月夜-片名与关键词.txt").write_text(keyword_text(TITLE, TITLE_EN, SHORT_TAGS))
    print("Preparing periodic piano audio", flush=True)
    audio, audio_report = make_audio()
    write_json(OUT / "audio.json", audio_report)
    temp = OUT / (NAME + ".part.mp4")
    final = OUT / (NAME + ".mp4")
    audio_only = "--audio-only" in sys.argv[1:]
    if audio_only:
        print("Keeping the verified picture and replacing piano audio", flush=True)
        existing = json.loads((OUT / "delivery.json").read_text())
        meta = probe(final)
        vs = next(s for s in meta["streams"] if s["codec_type"] == "video")
        if (vs["width"], vs["height"], int(vs["nb_frames"])) != (W, H, FRAMES):
            raise RuntimeError("Existing picture does not match the short")
        motion = existing["motion"]
        video_args = ["-i", final, "-i", audio, "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy"]
    else:
        print("Preparing centred portrait motion", flush=True)
        half, motion = render_half(source)
        write_json(OUT / "progress.json", {"stage": "reverse_and_mux"})
        print("Encoding the reverse half and muxing the loop", flush=True)
        video_args = ["-threads", "2", "-i", half, "-i", audio,
                      "-filter_complex_threads", "2", "-filter_complex",
                      "[0:v]split=2[f][r];[r]reverse[back];[f][back]concat=n=2:v=1:a=0[v]",
                      "-map", "[v]", "-map", "1:a:0", "-c:v", "libx264", "-threads", "4",
                      "-crf", "16", "-preset", "medium", "-pix_fmt", "yuv420p", "-r", FPS,
                      "-frames:v", FRAMES]
    run(["ffmpeg", "-v", "error", "-y", *video_args,
         "-c:a", "aac", "-b:a", "256k", "-ar", SR, "-ac", "2", "-t", DURATION,
         "-metadata", "title=" + TITLE, "-movflags", "+faststart", temp])
    print("Decoding and checking both loop boundaries", flush=True)
    validation = verify(temp)
    temp.replace(final)
    validation["ffprobe"]["format"]["filename"] = str(final)
    write_json(OUT / "check/validation.json", validation)
    dest = DESKTOP / final.name
    shutil.copy2(final, dest)
    digest = hash_file(final)
    if hash_file(dest) != digest:
        raise RuntimeError("Desktop copy hash mismatch")
    report = {"file": str(final), "desktop_path": str(dest), "bytes": final.stat().st_size,
              "sha256": digest, "duration_s": DURATION, "frames": FRAMES,
              "title": TITLE, "title_en": TITLE_EN, "motion": motion, "audio": audio_report,
              "validation": str(OUT / "check/validation.json"),
              "wall_seconds": time.time() - started}
    write_json(OUT / "delivery.json", report)
    (OUT / "NOTES.txt").write_text(
        f"《月夜》循环短视频\n{W}×{H} / {FPS} fps / {DURATION:.3f} 秒 / {FRAMES} 帧\n\n"
        "画面：现有 Muse 锐化素材的 0–8 秒，缓慢推近，再沿同一路径拉回。\n"
        "使用余弦速度曲线，首尾和折返点的运镜速度归零。全幅居中保留，双手完整，"
        "同帧模糊背景上下对称填满；没有另加蓝色滤镜或文字。\n"
        "音乐：沿用长片批准的 Musopen CC0 钢琴录音。第一主题接到它的重复，"
        f"循环长度 {DURATION:.3f} 秒，接续重叠 {AUDIO_OVERLAP:.2f} 秒；不淡出到静音。\n"
        "曲目：肖邦《降 E 大调夜曲》，Op. 9, No. 2。\n"
        "画作：Ivan Kramskoi, Moonlit Night (1880)，公有领域；来源见 ../SOURCES.md。\n"
        f"已检查 {FRAMES} 个解码画面、首尾画面、音频样本和响度，并核对桌面副本 SHA-256。\n"
        "长片没有改动；关键词在单独文本中。\n")
    print(json.dumps({"file": str(dest), "duration_s": DURATION, "frames": FRAMES,
                      "visual_wrap_mae": validation["loop_pixel_mae_0_255"],
                      "audio_wrap_step": validation["audio_wrap_step"],
                      "lufs": validation["lufs"], "true_peak_dbtp": validation["true_peak_dbtp"]},
                     ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
