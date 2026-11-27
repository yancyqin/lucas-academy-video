"""混音: loudness of the whole film, and whether the music really gives way to the voices (README "Music under
narration": 20 dB under a voice, 9 dB under in any gap of 0.8 s or more, 0.35 s attack, 0.8 s release)."""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import numpy as np

from common import FAIL, item

SR = 16000



def loudness(path: Path, spec: dict) -> tuple[dict, list]:
    err = subprocess.run(["ffmpeg", "-nostats", "-hide_banner", "-i", str(path), "-map", "0:a:0",
                          "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    summary = err[err.rfind("Summary:"):]
    i = float(re.search(r"I:\s+(-?[\d.]+) LUFS", summary)[1])
    lra = float(re.search(r"LRA:\s+(-?[\d.]+) LU", summary)[1])
    tp = float(re.search(r"Peak:\s+(-?[\d.]+|-inf) dBFS", summary)[1])
    lo = spec["loudness"]
    found = []
    if abs(i - lo["lufs"]) > lo["tol"]:
        found.append(item("mix", FAIL, "mix.lufs", f"整体响度 {i:.1f} LUFS，标准是 {lo['lufs']:.0f}±{lo['tol']}",
                          "用 loudnorm 或增益调到标准", key="mix.lufs"))
    if tp > lo["tp_max"]:
        found.append(item("mix", FAIL, "mix.true_peak", f"真峰值 {tp:.1f} dBTP，上限 {lo['tp_max']:.1f}",
                          "加限幅（alimiter）", key="mix.true_peak"))
    return {"lufs": i, "lra": lra, "true_peak": tp}, found


def _runs(mask: np.ndarray) -> list[tuple[int, int]]:
    edges = np.diff(np.r_[False, mask, False].astype(np.int8))
    return list(zip(np.flatnonzero(edges == 1), np.flatnonzero(edges == -1)))


def ducking(played: np.ndarray, spec: dict) -> tuple[dict, list]:
    """Check the actual full-film mix, with independent voice and music evidence.

    Compare the mixed music with its un-ducked source to cancel the composition's
    own dynamics. Subtitle/paragraph boundaries are not voice activity boundaries.
    """
    if not spec.get('music') or not spec.get('lines'):
        return {'skipped': 'no music under narration in the spec'}, []
    from common import decode_audio, ffprobe
    required = ('voice_audio', 'music_audio', 'music_source')
    missing = [key for key in required if not spec.get(key) or not Path(spec[key]).is_file()]
    if missing:
        return {'missing': missing}, [item('mix', FAIL, 'mix.music_evidence',
            '配乐检查缺少实际音轨', '提供全时间线 voice_audio、music_audio 和未压低的 music_source；不能只看总音量。',
            key='mix.music_evidence')]
    voice, music, source = (decode_audio(Path(spec[key])) for key in required)
    duration = len(played) / SR
    if any(abs(len(x) - len(played)) > SR * .1 for x in (voice, music, source)):
        return {'duration': duration}, [item('mix', FAIL, 'mix.music_duration',
            '配乐或人声来源没有覆盖完整时间线', '三个来源须与最终混音同起点、同时长。', key='mix.music_duration')]
    # ffmpeg's default stereo-to-mono route is (L + R) / sqrt(2).
    # A mono narration copied into both final channels gains sqrt(2) on that
    # analysis route; it was not amplified in either delivered channel.
    final_channels = (spec.get('format') or {}).get('audio_channels', 2)
    voice_channels = next(s['channels'] for s in ffprobe(Path(spec['voice_audio']))['streams']
                          if s['codec_type'] == 'audio')
    route = np.sqrt(2) if voice_channels == 1 and final_channels == 2 else 1.
    music_channels = next(s['channels'] for s in ffprobe(Path(spec['music_audio']))['streams']
                          if s['codec_type'] == 'audio')
    music_route = np.sqrt(2) if music_channels == 1 and final_channels == 2 else 1.
    activity_voice = voice
    voice = voice * route
    music = music * music_route
    n = min(map(len, (played, voice, music, source)))
    hop, step = 320, .02
    count = n // hop
    arrays = [x[:count * hop].astype(np.float64).reshape(count, hop) for x in (played, voice, music, source)]
    p, v, m, s = arrays
    rms = lambda x: np.sqrt(np.mean(x * x, axis=1))
    vr, mr, sr = rms(v), rms(m), rms(s)
    dbs = lambda x: 20 * np.log10(np.maximum(x, 1e-9))
    times = (np.arange(count) + .5) * step
    exempt = (times < 2) | (times > duration - 5)
    exceptions = []
    found = []
    for row in spec.get('music_exceptions', []):
        if (not isinstance(row, dict) or not row.get('reason') or not row.get('owner_evidence')
            or not 0 <= row.get('start', -1) < row.get('end', -1) <= duration + .1):
            found.append(item('mix', FAIL, 'mix.music_exception', '无配乐区间缺少作者依据',
                '例外必须有 start/end、reason 和 owner_evidence，不能由生成器自行添加。', key='mix.music_exception'))
            continue
        exceptions.append(row)
        exempt |= (times >= row['start'] - .6) & (times <= row['end'] + .8)
    # A claimed music stem must actually be audible in the encoded final mix.
    # AAC coding error may scale with the voice; complete missing music must not.
    err = rms(p - v - m)
    tolerance = np.maximum.reduce([.05 * vr, .10 * mr, np.full(count, 1e-4)])
    bad_mix = err > tolerance
    bad_fraction = float(np.mean(bad_mix)) if count else 1.
    if bad_fraction > .05:
        found.append(item('mix', FAIL, 'mix.music_reconstruction', '最终混音与提交的配乐、人声不一致',
            f'{bad_fraction:.1%} 的时间窗无法由 voice_audio + music_audio 还原；检查是否漏混、错轨或错时。',
            key='mix.music_reconstruction'))
    holes = [(a * step, b * step) for a, b in _runs((dbs(mr) < -75) & (dbs(sr) > -55) & ~exempt)
             if (b - a) * step >= 1.]
    for i, (a, b) in enumerate(holes):
        found.append(item('mix', FAIL, 'mix.music_coverage', '影片中途没有背景音乐',
            '原曲此处仍有声音，但最终配乐中断；只有作者明确要求的例外可留空。',
            t0=a, t1=b, key=f'mix.music_coverage.{i}'))
    # Gain is measured from actual stems, not trusted from a gain-envelope file.
    power = np.sum(s * s, axis=1)
    gain = np.sum(s * m, axis=1) / np.maximum(power, 1e-18)
    gain_db = dbs(np.maximum(gain, 1e-9))
    valid = sr > 1e-6
    activity_rms = np.sqrt(np.mean(activity_voice[:count * hop].reshape(count, hop).astype(np.float64) ** 2, axis=1))
    active = dbs(activity_rms) > -48
    spans = []
    for a, b in _runs(active):
        if spans and (a - spans[-1][1]) * step < .8:
            spans[-1][1] = b
        else:
            spans.append([a, b])
    rows, unavailable = [], []
    for (_, b), (a, end) in zip(spans, spans[1:]):
        gap = (a - b) * step
        if gap < .8 or np.any(exempt[b:a]):
            continue
        interior = np.arange(b + 8, a - 5)
        boundary = np.r_[np.arange(max(0, b - 8), b), np.arange(a, min(end, a + 8))]
        interior = interior[valid[interior]]
        boundary = boundary[valid[boundary]]
        if not len(interior) or not len(boundary):
            unavailable.append([b * step, a * step])
            continue
        rise = float(np.percentile(gain_db[interior], 80) - np.median(gain_db[boundary]))
        minimum = 6. if gap >= 1.4 else 2.
        rows.append({'gap': [round(b * step, 3), round(a * step, 3)],
                     'rise_db': round(rise, 2), 'minimum_db': minimum})
        if rise < minimum:
            found.append(item('mix', FAIL, 'mix.ducking_gap', '人声与停顿之间没有按规范压低、回升音乐',
                f'实际配乐增益只回升 {rise:.1f} dB，至少应回升 {minimum:.0f} dB；已排除钢琴本身的强弱变化。',
                t0=b * step, t1=a * step, key=f'mix.ducking_gap.{b}'))
    # Check sustained music masking, independently of its before/after gain.
    block = 50  # one second; do not call a quiet consonant a whole quiet sentence
    size = count // block * block
    voice_sec = np.sqrt(np.mean(vr[:size].reshape(-1, block) ** 2, axis=1))
    music_sec = np.sqrt(np.mean(mr[:size].reshape(-1, block) ** 2, axis=1))
    speaking = np.mean(active[:size].reshape(-1, block), axis=1) >= .3
    margin = dbs(voice_sec) - dbs(music_sec)
    median_margin = float(np.median(margin[speaking])) if speaking.any() else None
    if median_margin is not None and median_margin < 17:
        found.append(item('mix', FAIL, 'mix.music_level', '人声下的背景音乐整体过响',
            f'说话时间窗的典型人声/音乐差只有 {median_margin:.1f} dB；目标约 20 dB，允许录音动态波动。',
            key='mix.music_level'))
    masked = np.flatnonzero(speaking & (margin < 6))
    if len(masked):
        found.append(item('mix', FAIL, 'mix.music_masking', '配乐可能盖住人声',
            '这些一秒时间窗内音乐距人声不足 6 dB：' + ', '.join(str(int(t)) for t in masked[:12]),
            t0=float(masked[0]), t1=float(masked[0] + 1), key='mix.music_masking'))
    return {'method': 'full_film_stems_and_actual_voice_activity', 'duration': duration,
            'coverage_holes': holes, 'authorized_exceptions': exceptions,
            'reconstruction_bad_fraction': bad_fraction, 'voice_analysis_route_gain': float(route),
            'music_analysis_route_gain': float(music_route),
            'gaps': len(rows), 'rows': rows,
            'unmeasurable_source_rests': unavailable,
            'median_voice_music_margin_db': round(median_margin, 2) if median_margin is not None else None,
            'median_rise_db': round(float(np.median([r['rise_db'] for r in rows])), 2) if rows else None,
            'minimum_voice_music_margin_db': round(float(margin[speaking].min()), 2) if speaking.any() else None}, found
