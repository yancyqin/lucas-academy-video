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

## 安装

Node 侧(渲染):

```bash
npm install          # Node 20+;Remotion 4.x
```

Python 侧(对齐 + 放大)。跟 `voice-cover/` 共用同一个 `.venv-align`,如果你已经按
[voice-cover/SETUP.md](voice-cover/SETUP.md) 建过就跳过前两步:

```bash
brew install uv
uv venv --python 3.12 .venv-align
VIRTUAL_ENV=.venv-align uv pip install torch torchaudio demucs stable-ts soundfile
VIRTUAL_ENV=.venv-align uv pip install spandrel pillow      # 放大用
```

torch 需要 Python 3.12,系统的 3.14 没有 wheel,所以必须指定版本。

### 模型权重

**Real-ESRGAN**(放大,64 MB),脚本写死找这个路径:

```bash
mkdir -p t2v/models/esrgan && curl -fL -o t2v/models/esrgan/RealESRGAN_x4plus.pth \
  https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth
```

**Whisper medium**(对齐,1.4 GB)首次运行 `align_lyrics.py` 时自动下载,不用手动准备。

**Demucs**(只在没有真分轨时才需要)首次运行时自动下载。

**Wan 2.1**(文生视频)见 [t2v/README.md](t2v/README.md)。设 `HF_HUB_DISABLE_XET=1`,
否则大文件传输会卡死在 0 字节。

### 验证

```bash
.venv-align/bin/python -c "import torch, stable_whisper, spandrel; \
  print('torch', torch.__version__, 'mps', torch.backends.mps.is_available())"
npx tsc --noEmit -p tsconfig.json
```


## 数据模型

一首歌一个 `src/songs/<name>.json`,三样东西:

```jsonc
{
  "audio": "audio/songs/xxx.mp3",     // 相对 public/
  "fps": 30, "durationSeconds": 306.67,
  "lyricAnchor": "lower",             // 歌词压低,别盖住脸和十字架;默认 center
  "dissolveSeconds": 0.55,            // 溶解长度,不能超过镜头之间的重叠
  "showNeighbours": false,            // 上下句虚影;实拍底上会糊成一团
  "lines": [ {"t": 26.36, "end": 30.1, "section": "verse", "text": "...",
              "echo": false} ],
  "shots": [ {"src": "footage/rejoice/S01.mp4", "start": 0, "end": 19.6,
              "move": "in", "loop": false, "lightRamp": false} ]
}
```

`section` 是 `intro | verse | prechorus | chorus | bridge | outro`,驱动
[lyrics-theme.ts](src/videos/lyrics-theme.ts) 里的配色、字号、字重。
`move` 是运镜方向 `in | out | left | right | up | none`(`none` 给自带运动的镜头,
比如已经按两倍画幅渲好慢推的静帧)。

每行的 `end` 是**实测的收声时间**,有它就不再用 `MAX_HOLD`;`echo` 标出 `(Rejoice)`
这类括号回声句,字号和不透明度都会降。镜头的 `loop` 默认关(见下面"坑"),
`lightRamp` 把镜头从冷影调到满金光——模型不给主体运动,这层只能后期加。

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

## 素材来源与许可

**生成的素材**(`sh*-loop.mp4`)由本机的 Wan 2.1 产出,没有第三方权利问题。

**实拍素材**(`cc0-*.mp4`)来自 Pexels,按其许可可免费商用、无需署名。
出处逐条记在 [public/footage/CREDITS.md](public/footage/CREDITS.md) ——
**每新加一条实拍素材都要往那里补一行**,否则片子发布时无法追溯来源。

`public/footage/` 整个目录不进仓库(见 `.gitignore`),所以 CREDITS.md 是唯一的记录。


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

## 第二首:《Rejoice》改了什么

同一套组件跑第二首歌,暴露了三处"只对第一首成立"的假设。都改成了按歌配置,
`one-breath.json` 行为不变。

**镜头默认不再 loop。** `FootageLayer` 原本无条件用 `<Loop>` 包每个镜头,因为第一首的
Wan 片是 12.2 秒的 boomerang,回环点本身就是运动反向处,接缝看不见。《Rejoice》的硬规则
是"绝不 loop、绝不倒放",所以 `loop` 现在要显式打开(旧镜头带 `loopSeconds` 视为打开)。
更根本的保证在结构上:**每个镜头都预渲染成一个和它在时间轴上等长的文件**,
镜头不可能被要求重播,因为它从不短于它要填的时间。`scripts/mv/verify_shots.py` 会
重新量所有文件长度,并逐条比较首帧与末帧——boomerang 和回环都会让末帧回到首帧。

**歌词按实测收尾,不再靠 `MAX_HOLD`。** 一个全局常量分不清"长音"和"间奏":强制对齐给
这首歌两句报了 22.4 秒和 24.5 秒的结束时间,两句都正好在长间奏前面。`LyricLine` 现在带
`end`,由 `scripts/align/refine_ends.py` 按人声能量夹出来。阈值不是猜的,是拿标注窗口量的:
唱的地方在 −23…−27 dB,间奏在 −46…−84 dB,所以门限取 −30 dB。**唯一量不出来的是开头那段**——
17–33 秒的器乐漏进 demucs 人声轨,峰值到 −23.6 dB,和唱的电平重叠,所以那一句靠上限收。

**`(Rejoice)` 这类回声句要单独放。** 录音里每段副歌只唱两次 `Again I sing, rejoice`,
歌词表却有三行——中间那行括号里的 `(Rejoice)` 是回声,不是第三句主旋律。用 medium 模型
逐词量三段副歌尾巴才看清这件事(第三段更明显:`Again I sing` 之后隔 2.1 秒才答 `Rejoice`)。
所以回声句被放进它所回应的那句后面**实测的静音间隙**里,顺序不变、不并入上一行,
字号和不透明度都调低。

**别拿上一首的 stem 对齐这一首。** Suno 每首歌导出的文件名都一样(`0 Lead Vocals.mp3`…),
所以 `stems/` 平铺放两首歌必然出事:《One Breath》是 313.272s,《Rejoice》是 306.672s,
而 `align_lyrics.py` 原本取 glob 的第一个匹配。**这个错误下游完全看不出来**——每句都拿到
时间戳,长度也像那么回事,只是全错。现在 `stems/` 一首歌一个目录,`align_lyrics.py`
递归找,**找到多于一条就直接报错让你用 `--stem` 指定**,不再替你猜。
长度对不上是第一个线索(注意别信 mp3 头,Lead Vocals 那条头里写 1299.79 秒),
确认要靠**冷转写**:切一段丢给 whisper,听见 "dust became a soul" 就说明拿错歌了。

**真分轨值得等。** 先用 demucs 分离也能做完,而且拿真分轨复核后位移中位数只有 0.060 秒,
但两件事只有真分轨能给:
- **收尾能量可信。** demucs 人声在 17–33 秒有 −23.6 dB 的乐器串音,和唱的电平重叠,
  开场那句只能靠上限掐掉;真分轨的间奏是 −93…−120 dB 的真静音,量出来是唱到 19.12 秒。
- **和声单独一轨,回声句才有答案。** demucs 把主唱和和声混在一起,`(Rejoice)` 只能靠
  推断安放;真分轨里和声轨在第三段副歌两句之间**单独唱**(275.82–278.48),
  直接证实这一行是和声回应,不是第三句主旋律。
