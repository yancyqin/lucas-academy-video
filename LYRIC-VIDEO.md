# 歌词 MV 制作流程

把一首歌 + 一份歌词变成成片。为《One Breath》建的,换一首歌是换一个 JSON,不是改代码。

```
歌曲 ──┬─► 人声 stem ──► 强制对齐 ──► 逐句时间轴 ─┐
       │                                          ├─► song JSON ──► Remotion ──► mp4
       └─► 伴奏 stem ──► 节拍网格(可选)          │
                                                  │
文生视频 clip ──► Real-ESRGAN 4x ──► 慢放 ──► 素材 ─┘
CC0 实拍素材  ──────────────────────────────────┘
```

## 数据模型

一首歌一个 `src/songs/<name>.json`,三样东西:

```jsonc
{
  "audio": "audio/songs/xxx.mp3",     // 相对 public/
  "fps": 30, "durationSeconds": 313.27,
  "lines": [ {"t": 26.36, "section": "verse", "text": "..."} ],
  "shots": [ {"src": "footage/x-loop.mp4", "start": 0, "end": 15.5,
              "move": "in", "loopSeconds": 23.0} ]
}
```

`section` 是 `verse | prechorus | chorus | bridge | outro`,驱动 [lyrics-theme.ts](src/videos/lyrics-theme.ts)
里的配色、字号、字重。`move` 是运镜方向 `in | out | left | right | up`。

组件只有三个文件:[LyricsVideo.tsx](src/videos/LyricsVideo.tsx)(排版)、
[FootageLayer.tsx](src/videos/FootageLayer.tsx)(镜位+运镜+统一调色)、
[lyrics-theme.ts](src/videos/lyrics-theme.ts)(主题)。

## 步骤

### 1. 拿到人声 stem

**优先用平台导出的真分轨。** Suno 能导出 7 轨(主唱/和声/鼓/贝斯/吉他/合成器/其他),
放进 `stems/`。实在没有才用 demucs 分离。

### 2. 对齐歌词

```bash
.venv-align/bin/python scripts/align/align_lyrics.py
```

自动找 `stems/*Lead Vocals*`,没有就退回 demucs。输出 `<song>.aligned.json`,
确认无误后覆盖 `<song>.json`。

某段崩了(见下面"坑")就单独重对:

```bash
.venv-align/bin/python scripts/align/realign_window.py <首行号> <末行号> <起秒> <止秒>
```

手工微调用 [tools/tap-timing.html](tools/tap-timing.html)(要用 http 打开,空格打点、±0.1s 微调)。

### 3. 生成素材

见 [t2v/README.md](t2v/README.md)。**用蒸馏版 `--backend fastwan`**,不是官方 25 步配方。

### 4. 放大

```bash
.venv-align/bin/python scripts/upscale/esrgan.py <clip名> ...
```

**必须在原始 17 帧上放大,不能在慢放后的成品上放。** 前者全套 221 帧,后者约 9000 帧,
而且放大器面对的已经是插帧糊过的画面。

### 5. 慢放

```bash
ffmpeg -i tmp/upscale/X-4x.mp4 \
  -vf "setpts=24.5*PTS,minterpolate=fps=30:mi_mode=blend" \
  -c:v libx264 -crf 16 -pix_fmt yuv420p -an public/footage/X-loop.mp4
```

`blend` 不是 `mci`,**不做首尾回放**(见下面"坑")。放大之后**不要再加 unsharp**。

### 6. 渲染

```bash
npm run song:render     # 全片
```

只看某一段就渲 `OneBreathChorus`,窗口在 [src/Root.tsx](src/Root.tsx) 里改。

## 实测数据(M3 Pro / 36 GB)

| | |
|---|---|
| Wan 1.3B 蒸馏版 17 帧 | 约 **2 分钟**/条(官方 25 步版是 7.5 分钟) |
| Real-ESRGAN 4x | 约 **8 秒**/帧,一条 17 帧约 2 分钟 |
| VAE 解码峰值 | 17 帧 24.5 GiB / 33 帧 **35.9 GiB**(贴 36GB 天花板) |
| 全片渲染 | 9400 帧约 15 分钟 |

## 坑

**平台 stem 远好过 demucs。** demucs 把主唱和和声混在一轨,副歌里 gang vocal 填满句间,
导致音节边界根本测不出来。用真分轨可以只压主唱、和声完全不动。

**Suno stem 的 mp3 头是坏的。** ffprobe 读 313 秒的文件会报 1299 秒。**一律先解码成 wav**
再做任何切片。对齐脚本已经这么做了。

**强制对齐会在长间奏处丢轨。** 整曲一次对齐时,吉他 solo 之后的词会全部堆在同一个时间戳上。
用 `realign_window.py` 单独重对那一段,拿前后两句当锚点自校验。

**干唱轨的对齐质量远高于分离轨。** 同一句在 demucs 轨上前后两次能给出 +0.82 和 −0.78 秒
两个矛盾答案;在真干唱轨上包络验证能到分毫不差。

**首尾回放 = 假晃动。** forward + 完全倒放是回文,草会正着摆一遍再原样倒回来,一眼假。
改成单程超慢镜(21 倍以上)。

**混乱运动用 blend,不要 mci。** 运动补偿在水面焦散上会瞎编矢量,画面扭曲。低运动素材
用 mci 能保住细微抖动,但水、麦浪这类一律 blend。

**Wan 1.3B 画不了细颗粒。** 尘埃、雨丝、雪、火星全部失败,只会给一坨虚焦。大尺度高对比的
自然题材(丘陵、沙丘、云、麦田)才是它的强项。

**Wan 几乎不产生主体运动。** 帧间差通常 1–6(真实拍摄约 13)。所以运镜必须在 Remotion 里做
——参考片里的运动本来也大多是摄影机运动。

**歌词的显示时长比时间轴更容易出错。** `MAX_HOLD` 原本 6.5 秒,而副歌两句间距有 8.8–9.5 秒,
导致字唱到一半就消失、屏幕空白 2–3 秒。症状出现在"两句之间"时,先怀疑衔接逻辑,不要
去查各自的时间戳。

## 测量方法论

这套流程里大量决策靠测量而不是听感,几条通用的:

**比较两个音频前先量时间偏移。** demucs 写 stem 会带 **+23 ms** 解码延迟,Remotion 转 AAC 会带
**+42.67 ms**(48kHz 下正好 2048 采样)。错开这点距离去算相关度,会在瞬态处量出 −6 到 −8 dB
的假凹陷。

**用零处理对照,不要用原曲当基准。** 想验证"我只改了这一处",要拿同样的 stem 走同样的管线
但不做编辑,生成一个 null 版本再比。跟原曲比会被上面那些偏移污染。

**先验证度量本身。** 判断"这段音频是不是同一条"之前,先拿原曲对自己跑一遍——应该得到 0.996。
拿不到就是方法有问题,不是素材有问题。

**节拍网格从鼓点求,不从相位估计。** 自相关估相位在不同片段会偏 70 毫秒;直接检测鼓的能量
突变能到 3–7 毫秒。三个鼓点之间的间隔如果能闭合成整数拍,速度就是精确的
(本曲:150.013 秒 ÷ 180 拍 = 0.8334,即 **72.0 BPM 整**)。
