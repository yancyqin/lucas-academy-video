# 好奇新世界 · 每周视频怎么做

每周五的 Curious Worlds Weekly（`lucasgame-academy/weekly/`）配一部视频：**好奇新世界**，第 NNN 期跟 Weekly 第 NNN 期走（第 1 期是 001–003 回顾）。
为什么这样做、定了哪些事，见 [WEEKLY-DEMO-PLAN.md](./WEEKLY-DEMO-PLAN.md)。这里是每周照着做的步骤。

## 定下来的样子

- **中文、英文各一部片**（owner，2026-10-20）：同一份镜头表，各按自己的配音定节奏（`timeline.zh.json` / `timeline.en.json`），卡片只用这部片的语言。每部片带两份字幕（自己的话和译文），都按自己的配音定时。不烧字幕。
- **产品画面也分语言**：中文片录中文界面和中文内容，英文片录英文界面和英文内容（WEB 经文、英文句子、Weekly 的 `?lang=en`）。本来就是英文的画面（牛顿演示、Python 作业、博物馆走廊、过山车）只录一次，两部片共用。
- 旁白：芳芳（`fangfang/zh`）和 Louise（`louise/en`），用 `scripts/voice_defaults.py` 的默认读法。
- **系列名的斜 ribbon 只在封面上**，片子里没有（owner，2026-10-20）：中文封面「好奇新世界」，英文封面「Curious Worlds」。封面的字要大：问题 176 px（中）/ 150 px（英），斜带宽 132 px、带上的字 68 / 58 px（owner 嫌第一版太小）。
- 配乐每期一首（`shots.py` 的 `MUSIC`），在旁白下压低，空隙里升起，由时间线控制，不用 sidechain。
- 片尾最后一句是开放式问题；封面只有一个问题（README）。
- 5–10 分钟（第 1 期 15 分钟）。每期预算：旁白 ≤ 25 句，不新做卡片，录屏用一条变速曲线。

## 文件

| 什么 | 在哪 | 进 git |
|---|---|---|
| 配音稿（中文一行 + `>` 英文一行） | `docs/weekly/<期>/zh-edit.md` | 是 |
| 镜头表（录屏时间用标记）、要拷的素材、配乐、读法 | `scripts/weekly/<期>/shots.py` | 是 |
| 产品录屏怎么录 | `scripts/weekly/<期>/captures.cjs` | 是 |
| Weekly 页面截图 | `scripts/weekly/<期>/stills.cjs` | 是 |
| YouTube 标题和简介 | `scripts/weekly/<期>/youtube.json` | 是 |
| 录屏、截图（`captures/<语言>/`、`stills/<语言>/`）、配音、两条时间线 | `public/weekly/<期>/` → `lucas-academy-video-data/weekly/public/<期>/` | 否 |
| 混音、画面、成片、字幕 | `out/weekly/<期>/` | 否 |

`public/weekly` 是指向 `lucas-academy-video-data/weekly/public` 的软链接（新 worktree 里要重新建）。

## 每周步骤

```bash
# 1. 周四：按 weekly-NNN.{zh,en}.json 写 docs/weekly/NNN/zh-edit.md，写 shots.py / captures.cjs / stills.cjs，先给 owner 看稿子
node scripts/weekly/capture.cjs scripts/weekly/NNN/captures.cjs          # 产品录屏，中文（真实时间，30 fps）
WEEKLY_LANG=en node scripts/weekly/capture.cjs scripts/weekly/NNN/captures.cjs <名字…>   # 英文片要重录的几段
node scripts/weekly/stills.cjs scripts/weekly/NNN/stills.cjs             # Weekly 页面截图，中文
WEEKLY_LANG=en node scripts/weekly/stills.cjs scripts/weekly/NNN/stills.cjs   # 英文
python3 scripts/weekly/assets.py NNN                                      # 镜头表里的外部素材
python3 scripts/weekly/build_timeline.py NNN                              # 两条草稿时间线（估算时长，画面标 DRAFT）
npx remotion studio                                                       # 看 WeeklyNNN / WeeklyNNNEn

# 2. 稿子定了：配音（一次只跑一个 CosyVoice 进程）
python3 scripts/weekly/narration.py NNN
NARRATE_THREADS=8 ../lucas-academy-media/.conda/bin/python scripts/weekly/narrate.py NNN zh
NARRATE_THREADS=8 ../lucas-academy-media/.conda/bin/python scripts/weekly/narrate.py NNN en
../lucas-academy-media/.conda/bin/python scripts/weekly/takes.py NNN      # 剪齐、统一响度
../lucas-academy-media/.conda/bin/python scripts/weekly/check.py NNN zh   # Whisper；有标记的逐条听（再跑 en）
python3 scripts/weekly/build_timeline.py NNN                              # 用真实时长

# 3. 渲染和交付（每部片：混音 → 画面 → 封面 → 上传文字 → 桌面「好奇新世界-第N期-上传」/「…-英文版-上传」）
../lucas-academy-media/.conda/bin/python scripts/weekly/deliver.py NNN mix
npx remotion render WeeklyNNN out/weekly/NNN/picture.zh.mp4 --muted --props='{"episode":"NNN","lang":"zh","voice":false}'
npx remotion render WeeklyNNNEn out/weekly/NNN/picture.en.mp4 --muted --props='{"episode":"NNN","lang":"en","voice":false}'
npx remotion still WeeklyNNNCover out/weekly/NNN/cover.zh.jpg && npx remotion still WeeklyNNNCoverEn out/weekly/NNN/cover.en.jpg
python3 scripts/weekly/youtube.py NNN
../lucas-academy-media/.conda/bin/python scripts/weekly/deliver.py NNN package
```

重配一句：改稿子后 `narration.py`，再 `narrate.py NNN zh --only <id> --force`，然后 `takes.py`、`check.py`、`build_timeline.py`。

## 录屏的坑

- 录屏用 Chrome 自己的截屏流（`Page.startScreencast`），抓的是**真实窗口**，不是 Playwright 模拟的视口：窗口大小要自己设，`capture.cjs` 会量 `innerWidth/innerHeight` 再校正。像素比用 `--force-device-scale-factor`。
- 静止的页面不出帧；`capture.cjs` 按时间戳把帧补成恒定 30 fps。
- 导航以后光标会丢，`glide` 会重新装。
- Weekly 页面开了平滑滚动，页脚也是 `.la-chrome`：截图时用瞬间滚动，只算真正吸顶的 `.site-header` 的高度（`stills.cjs`）。
- Weekly 里嵌的演示用的是页面自己的版本：Underground 75% 在 003 页面（`weekly/chess/underground-demo.js`），/chess/ 只有 5/10/20%；Comeback 在 002 页面。
- 博物馆（Inception Space）要逐帧录：`preview_start` 起 `Inception Space capture 8110`，第一次 Vite 冷编译会超过录制器 120 秒的等待，先在预览窗格里打开一次。脚本在 `lucasgame-academy/tools/presentations/capture/`（复制到 `lucas-academy-video-data/weekly/work/` 再跑，别在那个仓库里留文件）。
- 第三方页面（leetcode4kids.com）只用 Weekly 页面上的卡片截图，标来源；语言的桥里 NIV 的课不录。
- 两种语言的录屏长短不同：镜头表里的录屏时间写成标记（`"pause"`、`["rock1", 2.6]`、`"end"`），不要写死秒数，同一个瞬间才能在两部片里都对上。
- CodeMirror 把一行拆成很多 token：在编辑器里点某个词，要按整行的字符位置找文本节点（`captures.cjs` 的 glitch-arcade），否则代码根本没改到。
- 语言的桥默认界面是英文、句子先中文；英文片点「Think first, then tap to see the English」把英文显出来。句子游乐场用右上角的 English 切界面。
