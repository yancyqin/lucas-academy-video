# 好奇新世界 · 每周视频 —— 计划（v0.3，2026-10-20）

网站上的 Curious Worlds Weekly（`lucasgame-academy/weekly/`，每周五下午 4–5 点现场展示）每期配一部视频。
第 1 期把已经出过的 001–003 三期补上，约 15 分钟；从第 2 期起每周一部，跟当周的 Weekly 走，5–10 分钟。

本文是计划，还没有动手做。文末「待定」几条要 owner 先拍板。v0.2 吸收了顾问（Fable 5.1）的审稿意见，见文末「v0.1 → v0.2」。

## 沿用的规矩（README 里已有）

- 不烧字幕：干净画面 + `zh-Hans.srt` / `en.srt`；交付时第一句话就说视频和 SRT 在哪。
- 封面只有一个问题（大字中文、小字英文），交付前给 owner 约 10 个问题标题选。
- 片头卡写 Lucas Academy 和署名；片尾最后一句是一个开放式邀请问题，配音、上屏。
- 标签全小写，取自 `scripts/youtube_tags.py`；简介由脚本生成。
- 配音默认 `fangfang/zh`（zero-shot，1.15）和 `louise/en`（zero-shot-instruct，1.0）；每条 Whisper 检查（中文 ≥ 0.94）。
- 产品画面要真的：真实录屏、真实截图、真实作品图。Weekly 里本来就标「概念图」的图可以用，画面上照样标「概念图」。
- 连续的录屏用一条平滑变速曲线压缩（`src/lib/timeRamps.ts`），不剪成碎片。
- 只提交能重做的源头（稿子、代码、文档）；录屏、配音、渲染放 `lucas-academy-video-data/weekly/`，收尾时清理。

## 第 1 期 · 001–003 回顾（15:00，按主题分章，YouTube 章节）

按期号排会像更新日志。改成按主题讲：同一个项目跨三期的变化正好是故事（国际象棋：Lucas 的想法 → 选定美术 → Comeback 规则 → Underground 落石）。
每期 Weekly 页面不再当章节开头，只在需要时插 3 秒「当时的样子」。

| 章 | 时间 | 内容 | 画面来源 |
|---|---|---|---|
| 开场 | 0:00–0:45 | 封面问题 → 20 秒最好看的动作（过山车冲进黑洞、Avi 漂起来、落石砸到棋盘、天文水母张开）→ 片名卡 → 什么是 Weekly（周五 4–5 点，谁都能来，可以带一个想法） | 各章素材里挑 |
| **一 · 走进一座博物馆** | 0:45–4:15 | 「好玩，也要有所发现」；梵高房间：走廊走进去，停在一幅画前打开阅读（0:50）；Manifold · Golden Funnel 坐一圈（0:50）；Space Baby Avi 换色、走路、漂浮（0:35）；五件三维作品各转 8–10 秒（0:50） | 梵高房间用 `tools/presentations/capture` 重录成 16:9；过山车用 `roller-coaster-final/final-long.mp4` 的骑行段；Avi 录 is.lucasacademy.org/avi/；三维作品录 001 页面的 Atelier |
| **二 · 熟悉的棋，新的规则** | 4:15–7:30 | Lucas 的想法：四种美术方向、棋子视角（0:40）；「领先太多，局势会变吗？」、吃子对决（0:30）；选定蚀月王庭 → 修改版 → 三颗 3D 棋子（0:40）；Comeback：两个机器人，落后超过 5 分就复活一颗（0:45）；Underground：落石砸向领先的一方，王和后不会被砸（0:45） | `weekly/assets/chess-*.jpg`（概念图）；棋子录 002 页面查看器；**Comeback 录 002 页面里的演示，Underground 录 003 页面里的 75% 演示**（`weekly/chess/underground-demo.js`，不是 /chess/，/chess/ 只有 5/10/20%）；录前固定 `Math.random` 种子 |
| **三 · 读经文，学语言** | 7:30–10:15 | Bible Sequence：听 John 3:16 拼句子（0:35）→ 新玩法接字、接词（0:40）；语言的桥：两个孩子互教的想法 + 短片一瞥（0:30）→ 课堂（0:25）→ 周记第一期，芳芳和 Louise 朗读（0:35） | 改 `scripts/fun-informatics-02/record-bible.cjs` 录 bible.lucasacademy.org 和 `/sentence.html`；语言的桥录 `/class` 和 `?lesson=weekly-journal-1` |
| **四 · 编程课** | 10:15–12:15 | 周三 Coding 试运营：Rainbow Collector（0:15）；Glitch Arcade「身体是一个列表」，找到碰撞、改代码、游戏里验证（0:45）；Python：score 从 0 开始加 10（0:30）；4 人小班（0:15） | Rainbow Collector 是 leetcode4kids.com（第三方）：只用 Weekly 页面上的卡片，标来源；Glitch Arcade 录 `lucasacademy.org/app/?level=04-the-body-is-a-list`；Python 录 `programs/coding-class/score-homework` |
| **五 · 还有更多可能** | 12:15–13:45 | 物理：Newton + AI 一起探究（0:40）；信息学：趣味信息学 1、2（0:30）；生物：Cell Rap（0:20） | Newton 录 `human-led-ai-collaboration/coach/?demo=newton-showcase`（002 页面 10/9 加的）；三部成片只用海报 + 5–8 秒一瞥，简介里放链接 |
| **六 · 你的想法** | 13:45–15:00 | Matthew：「我想做一个好游戏，不用氪金也能赢！」整屏（0:10）；怎么提交想法 + 活动表（0:25）；开放式问题（0:20）；片尾卡（0:15） | 001/003 页面 |

## 以后每周（5–10 分钟）的固定格式

- 0:00–0:30 封面问题 + 片名卡（第 NNN 期）
- 3–6 条更新，每条 60–90 秒：3 秒 Weekly 页面 → 产品实录（一条变速曲线）→ 一句「去哪里试」（网址/二维码）
- 本周想法（如果有人带了想法）
- 开放式问题 + 周五邀请 + 片尾卡（约 0:45）

**预算上限**：7 种镜头、不为某一期新做卡片、旁白 ≤ 25 句（第 1 期 ≤ 45 句）、Whisper 一遍、每段连续录屏一条变速曲线。
**每周不做**：新卡片设计、AI 生成画面、长段成片节选、跑旧版本的 worktree、多轮重录。需要这些的内容单独做成片。
英文片每周都做：同一份镜头表，英文配音、英文录屏（本来是英文的画面共用），按英文配音定节奏。

## 旧 demo 找不到怎么办（按优先级）

1. **现在线上还能演示当时的东西**——直接录。已核实：Avi、梵高房间、语言的桥、Comeback 和 Underground（在 Weekly 002/003 页面里）都还在。
2. **线上已经变了**——`git worktree add` 到那一期日期前的提交，本地跑起来录（只读；不碰 owner 正在改的工作区，例如 `lucas-academy-bible` 有一批未提交改动）。只在第 1 期用。
3. **跑不起来**——用当时的截图：`weekly/assets/`、存档 Weekly 页面、`presentation/assets/` 的录像、各成片里已经拍过的产品画面。
4. **什么都没有**——不编造；用 Weekly 页面上的文字带过，旁白说清楚是「当时的想法」。

## 一次搭好、以后每周复用的流水线

第 1 期的大部分工作是搭这一套，之后每周只写稿、录新东西：

- `scripts/weekly/capture_page.cjs`：通用网页录屏（Playwright 1.59，`page.clock` 控制时间，固定 `Math.random` 种子，逐帧截图，画光标和点击波纹），一个 JSON 写「打开哪页、点哪里、停多久」。由 `record-lang.cjs` 推广而来。Inception Space 继续用 `tools/presentations/capture/record.cjs`（`?debug&manual=1` 手动时钟）。
- `src/videos/weekly/WeeklyEpisode`：7 种镜头——片名卡、Weekly 页面插入、录屏（带变速曲线）、静图（缓推）、成片海报、问题卡、片尾卡。所有期共用一套视觉、一首栏目音乐和一个转场音效。
- 一条命令 `npm run weekly -- 004`：`scripts/weekly/004/edit.md` → 配音 → Whisper → 时间线 → 渲染 → SRT → YouTube 简介。
- 生成的东西放 `lucas-academy-video-data/weekly/<期号>/`，不进 git。
- `WEEKLY-VIDEO.md`：每周照着做的清单。

## 每周节奏（建议）

Weekly 的中英文案在周五之前就写进网站了，所以稿子可以提前：

| 时间 | 做什么 |
|---|---|
| 周四 | 我按 `weekly-NNN.*.json` 和这周的提交起草稿子 + 镜头表，给 owner 看 |
| 周五 | owner 改稿 → 配音；周五展示后只补录屏，不改词 |
| 周六–周日 | 录屏、渲染、封面问题选项 |
| 周一 | owner 上传 |

## 内容安全

- 语言的桥里经文课文是 NIV（有版权）：不录这些课；万一入镜，加 Biblica 署名，帧不进 git。录周记和 WEB 经文的单元。
- 三维作品里的太阳仪用了 Solar System Scope 贴图（CC BY 4.0）：简介署名。
- 孩子：只出现 Lucas、Matthew 的名字和画。`/class` 等页面如果出现其他孩子的名字或作品，跳过或打码；周五现场录像先不用。
- 第三方页面（leetcode4kids.com）只用卡片截图，标来源。

## 已定（owner，2026-10-20）

1. **语言：中文、英文各一部片**（2026-10-20 看过初版后改定；初版是一部中文片 + 英文配音轨）。各按自己的配音定节奏，卡片只用自己的语言，
   产品画面也用自己的语言录（英文片重录英文界面和英文内容，本来是英文的画面共用）。每部片带中英两份字幕，按自己的配音定时。
2. **旁白：芳芳**（`fangfang/zh`）；英文 Louise（`louise/en`）。
3. **结构：第 1 期按主题分章，15 分钟**（上表）。

4. **片名：好奇新世界**（Curious Worlds）。第 1 期是「001–003 回顾」，之后期号跟 Weekly 一致（004 起）。
5. **配乐每期一首**（不固定一首栏目曲）。
6. **封面右上角一条斜的 ribbon，写系列名**（中文「好奇新世界」，英文「Curious Worlds」）。只在封面上，片子里没有。

做法和每周步骤：[WEEKLY-VIDEO.md](./WEEKLY-VIDEO.md)。

## v0.1 → v0.2（顾问意见，已核实后采纳）

- 第 1 期从按期号改为按主题（国际象棋三期连成一条线）；每期页面只做 3 秒插入。
- 补上漏掉的 Newton + AI 演示（002 期，10/9 加的物理项目）。
- Underground 的 75% 演示在 Weekly 003 页面里，不在 /chess/；Comeback 演示在 002 页面里。录前固定随机种子。
- 成片节选改为海报 + 5–8 秒一瞥，降低每期成本、把观众引到成片。
- 每周格式设预算上限（7 种镜头、≤ 25 句旁白）。顾问建议英文配音默认不做；owner 先选了中文片 + 英文配音轨，看过初版后改为中英各一部片（英文片重录英文画面）。
- 稿子提前到周四（文案周五前已在网站上）。
- 加「内容安全」一节：NIV、CC BY 署名、其他孩子。
- 更正：无头 Playwright 是会跑 requestAnimationFrame 的（不跑的是 app 里的预览窗格）；手动时钟是为了逐帧精确，不是为了 rAF。
- 顾问建议第 1 期 10 分钟——没采纳，owner 定的是 15 分钟。
