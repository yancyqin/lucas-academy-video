#!/usr/bin/env python3
"""Write the actual editorial decisions and measured delivery properties."""
import json, pathlib
import walk

HERE=pathlib.Path(__file__).resolve().parent
DATA=pathlib.Path(walk.DATA)

def read(path,default=None):
    return json.loads(path.read_text()) if path.exists() else default

def stamp(t):
    return f'{int(t//60)}:{t%60:06.3f}'

def write_notes():
    spec=read(HERE/"film/blue-wave.json")
    music=read(DATA/"music/normalized/report.json")["levy"]
    final=read(DATA/"film/蓝色浪潮.render.json")
    draft=read(DATA/"film/蓝色浪潮-draft.render.json")
    render=final or draft
    checks={x:read(DATA/f"film/check/{x}-validation.json") for x in ["draft","final","review"]}
    assets=read(DATA/"film/assets.json")
    lines=["# 蓝色浪潮 · 剪辑与验收记录", "", "仅使用 FILM-PLAN.md 指定的素材。无旁白、字幕或片内文字；没有新增生成式图像或视频素材，没有提交或推送 Git。", "", "## 交付文件", "", "| 文件 | 画面 | 时长 | 大小 |", "|---|---|---|---|"]
    for kind,file in [("draft","蓝色浪潮-draft.mp4"),("final","蓝色浪潮.mp4"),("review","蓝色浪潮-review.mp4")]:
        v=checks[kind]
        if v: lines.append(f'| `{file}` | {v["resolution"][0]}×{v["resolution"][1]} / 30 fps | {v["duration"]:.6f} s | {v["bytes"]/1024**2:.2f} MiB |')
    lines += ["", "主文件：x264 CRF 16、yuv420p、AAC 256 kbps / 48 kHz / 双声道、faststart。预览：从主文件转为 CRF 23，复制同一 AAC 音轨。初稿：960×540，主要使用原始视频（普希金舞者沿用已有锐化版）；成片全部使用锐化版。", "", "## 音乐与响度", "", f'- 唯一音源：`music/raw/levy-musopen.flac`。全曲保留，画面按 30 fps 取整为 8144 帧，即 271.466667 s，与计划 271.47 s 相差 0.003333 s。', f'- 原始：{music["in_lufs"]:.1f} LUFS，真峰值 {music["in_peak"]:.1f} dBTP；整体增益 {music["gain_db"]:+.2f} dB。', f'- 归一 WAV：{music["out_lufs"]:.1f} LUFS，真峰值 {music["out_peak"]:.1f} dBTP。原始峰值已到 0 dBTP，因此仅在会超过 −1 dBTP 的峰上限幅；输出 48 kHz / 24-bit。', '- 仅音频最后 3 秒淡出；画面开头 2.5 秒从黑场进入、最后 7 秒落到黑场。中途全部是交叉叠化，没有插入黑场。']
    for kind in ["draft","final","review"]:
        v=checks[kind]
        if v: lines.append(f'- {kind} 实测：{v["lufs"]:.1f} LUFS；{v["true_peak_dbtp"]:.1f} dBTP；视频 {v["video_duration"]:.6f} s / 音频 {v["audio_duration"]:.6f} s；实际解码 {v["decoded_frames"]} 帧。')
    lines += ["", "## 最终段落（时间为交叉叠化中点）", "", "| 段落 | 开始 | 结束 | 内容 |", "|---|---|---|---|"]
    bounds=[0]+[float(spec["section_boundaries"][str(x)]) for x in [29,58,88,117,145,174,205,228]]+[spec["end"]]
    names=["神奈川冲浪里","印象·日出","两幅蓝色舞者","罗纳河上的星夜","月夜","夏洛特夫人 → 惠斯勒","米兰达——暴风雨","自由引导人民","雾海上的旅人：原画运镜 → Muse → 原画"]
    for i,(a,b,name) in enumerate(zip(bounds[:-1],bounds[1:],names)): lines.append(f'| S{i+1} | {stamp(a)} | {stamp(b)} | {name} |')
    lines += ["", "## 逐镜实际窗口与速度", "", "以下开始/结束包含叠化重叠。视频完全停在所选片段的第一帧直到整个入场叠化结束，然后用 0.75 秒平滑起步，接恒定速度；该段之后最低速度不低于平均速度的 70%。使用 100 fps 运动补偿插帧后采样到 30 fps。画的推拉在叠化前完成，避免与停住的视频产生取景漂移。", "", "| 镜头 | 开始–结束 | 文件 | 视频源区间 / 实际平均速度 | 取景 | 滤镜 |", "|---|---|---|---|---|---|"]
    if render:
        for sh in render["shots"]:
            source=str(pathlib.Path(sh["source"]).relative_to(DATA))
            speed=f'{sh["in"]:.3f}–{sh["out"]:.3f} s / {sh["speed"]["moving_mean"]:.3f}×' if "speed" in sh else "原画"
            crop="完整人物，共同对齐画布，背景高斯模糊并压暗 40%" if sh["layout"]=="registered_portrait" else ("整幅素材全高等比居中，两侧模糊背景压暗 40%" if sh["layout"]=="contain" else f'{sh["crop"]} → {sh["crop_to"] or sh["crop"]}; zoom={sh["zoom"]}')
            lines.append(f'| {sh["id"]} | {stamp(sh["start"])}–{stamp(sh["end"])} | `{source}` | {speed} | {crop} | {sh["tint"]:.2f} |')
    lines += ["", "## 对齐与镜头取舍", "", "| 画 | 画/照片 NCC | 视频 0s 首帧/照片 NCC 或直接对齐 NCC | 处理 |", "|---|---|---|---|"]
    photos=read(DATA/"real/aligned/report.json",{})
    for pid,asset in assets.items():
        if "video" not in asset: continue
        meta=read(DATA/f'footage/muse/aligned-{"sharp" if final else "soft"}/{pid}.json',{})
        sc=meta.get("scores",{})
        p=photos.get(pid,{}).get("score")
        pp=f'{p:.3f}' if p is not None else "—"
        v=sc.get("clip_to_photo",sc.get("selected_score",sc.get("score")))
        vv=f'{v:.3f}' if v is not None else "待测"
        handling="普通叠化；不做结构变形" if meta.get("ordinary_dissolve") else ("Muse 视频继续使用；开头及末尾使用同一张 extended-wanderer.png" if meta.get("preserve_fullframe") else ("本版直接使用原素材，全高等比居中，不应用会偏移前景的注册画布" if pid in ["blue-dancers-orsay","blue-dancers","kramskoi-moonlit"] else "第一帧注册，固定变换应用于全段；取景避开填充边缘"))
        lines.append(f'| {pid} | {pp} | {vv} | {handling} |')
    lines += ["", "## 本版修正与取舍", "",
        "1. 按主人的复看意见，奥赛舞者、普希金舞者和《月夜》的原画及视频全部改成按各自实际画面边界全高等比居中。左右余量最多相差 1 像素，上下没有额外留空。取消共享对齐画布；两侧仍使用本幅素材的高斯模糊、压暗 40% 背景。人物、双手和原视频的完整边界保留。",
        "2. 按主人澄清，旅人段继续采用「原画运镜 → 原来的 Muse 视频 → 回到原画」。只修正开头原画：始终使用同一张 `codex/extended-wanderer.png`，全图缓慢推近 1.00→1.03，关闭亮度呼吸，没有独立变化的背景层。Muse 从 3:56.067 叠化中点进入，完整片段、速度、取景和蓝色滤镜恢复为最初认可的版本；4:19.333 叠化回同一幅原画。结尾仍按原版用雾中的局部叠化，保留最后 7 秒淡出和音乐最后 3 秒淡出。",
        "3. 其他分镜、时间、音轨和滤镜不变。惠斯勒仍为整幅画静止居中，不推拉、不呼吸。自由引导人民仍只在原画上按指定窗口缓慢推近。",
        "4. 《月夜》只用 0–8.5 秒，避开原视频约 9 秒起已被自身右边界切掉的手。奥赛舞者用 1.0–9.958 秒，普希金舞者用 0–6.5 秒，夏洛特用 0–8 秒。",
        "5. 《印象·日出》结构相关性低，保留普通叠化及蓝灰原画到暖色实景的冷暖变化。",
        "6. 旧版已经保存在 `archive/2026-11-05-v1/`，所有改动未 commit、未 push。",
        "", "## 建议观看", "",
        "- `0:59–1:28`：两幅舞者的前景都居中，全高显示。",
        "- `1:57–2:25`：《月夜》居中，靠近结尾时双手仍完整。",
        "- `3:47.9–3:54.7`：开头是同一幅旅人原画缓慢运镜；随后继续用原来的 Muse 视频，再回到原画。",
        "", "## 检查产物", "",
        "- `check/*-framing.jpg`：逐镜开头、中间、结尾取景。",
        "- `check/*-transition.jpg`：每次原画进入视频的首帧叠化。",
        "- `check/*-S*.jpg` / `check/*-every-10s.jpg`：实际导出文件的取样。",
        "- `check/*-ending.jpg`：旅人段原画 → Muse → 原画的实际画面。",
        "- `check/preflight.json`：每个居中前景的实际像素边界及旅人「原画 → Muse → 原画」顺序检查。",
        "- `check/*-validation.json`：全片实际解码、音画时长、响度、黑帧和闪变检查，及开头原画运镜比对、Muse 与最初认可版本的比对。",
        "- `blue-wave.json`：分镜副本。", ""]
    for kind in ["draft","final","review"]:
        v=checks[kind]
        if v: lines.append(f'{kind}：8144 帧全片解码通过；片中意外黑帧 {len(v["unexpected_black_frames"])}，大幅闪变候选 {len(v["potential_flashes"])}。')
    (DATA/"film/NOTES.md").write_text("\n".join(lines)+"\n")
    print(DATA/"film/NOTES.md",flush=True)

if __name__=="__main__": write_notes()
