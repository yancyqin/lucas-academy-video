# 跨越中等收入陷阱（方案）

**状态：已上线（2026-10-27）** https://youtu.be/Wzatiq3aC8U 。一部片 17:45，中文音轨默认、另带英文音轨（都是 Yancy 的克隆音色）；YouTube 上标题、简介、8 个章节中英文都对，封面是中文问句。上线后检查时还差两处，在 Studio 里补：中文字幕没有上传（只看到英文字幕）；04:25 还没有链到《一根冰棍》的视频卡片（现在只有一张「查看更正的错误」卡片，在开头 0–5 秒）。上传包在桌面「跨越中等收入陷阱-上传」。工作数据（插图、原声、配音输入、时间线、混音）在 `lucas-academy-video-data/middle-income-trap/` 和 `lucas-academy-media/outputs/yancy/{zh,en}/middle-income-trap-*`。

Yancy 的第一人称片：从李录在哥大的对谈切入，讲**什么样的教育能突破天花板**。先出中文（Yancy，2026-10-25），英文以后再说。稿子是 Yancy 自己写的，按 SCRIPT-AND-VOICE.md（2026-10-24）的新做法：稿子以 Yancy 为准，配音前先写演绎稿，先配一分钟给 Yancy 定语速。

- 定稿（字幕）：[docs/middle-income-trap/zh-edit.md](docs/middle-income-trap/zh-edit.md)
- 演绎稿：[docs/middle-income-trap/voice-direction.md](docs/middle-income-trap/voice-direction.md)
- 文案来路与核查：education 仓库 `output/papers/middle_income_trap/`（原稿、整理稿 v0.1）、`thinking/1_philosophy/education_middle_income_trap_v0.1.md`（P98–P107）
- 原始素材（不进 git）：`../lucas-academy-video-data/middle-income-trap/`

## Yancy 定下的（2026-10-25）

- 不讲政治。李录对谈里讲产业政策、贸易、制裁、政府的部分一律不用。美国民权、法国抗议两处只陈述、不评价。阿根廷只从教育讲。
- 李录的话切原视频，Yancy 用中文复述一遍。片段要切得长一些。
- 开头用标注稿的方案一（不要冷开场）：钩子问句 → 带火了 → 什么是中等收入陷阱 → 提问 → 「是供给？需求？还是制度？」→「我们先听听李录怎么讲」→ 原声 A → 停 1.5 s →「我认为」→「这不只是国家的事……」。
- 「还是制度？」和「我认为」之间要停够，免得听成李录说的。
- 整体视频下面加进度条，让人可以跳过。
- 配音用 Yancy 的声音，整体要有 passion，语速比以前快。
- 音色：重录了参考音（`lucas-academy-media/docs/YANCY_ZH_RECORDING_SCRIPT.md`），试听后 Yancy 说「还是旧音色好」，继续用 `yancy/zh`。
- 语速：陈述句 1.2；问句（整句以问号结尾）1.1，问完停 1.2 秒，「停一停，让人思想」。自问自答的句子（问完马上答）算陈述句。
- 删掉李录「能力圈」那段：引子 sc03-08、原声 C、复述 sc03-09。
- sc04-03 不说「美国教育里倡导的」，改说「教育理念里一个重要的概念」。
- sc05-09 不提 Lucas Academy（「有点像做广告」），改成「我们做教育的初衷」；画面上也不放 Lucas Academy 标志卡。
- 视频方案：[docs/middle-income-trap/video-plan.md](docs/middle-income-trap/video-plan.md)。进度条照魔方那期；插图用 Codex 生成，提示词在 [codex-prompts.md](docs/middle-income-trap/codex-prompts.md)。

## 制作（Yancy 2026-10-26：「你可以做视频了」）

流程：
1. `../lucas-academy-media/.conda/bin/python scripts/middle-income-trap/narrate.py --speed 1.2 --question-speed 1.1`
2. `check.py`（Whisper）
3. `python3 scripts/middle-income-trap/assets.py`：插图取每张最新的 -vN，另有李录片段和定格、金的照片
4. `.venv-align/bin/python scripts/middle-income-trap/build_timeline.py --speed 1.2 --question-speed 1.1`：时间线、镜头、音乐混音
5. `node scripts/middle-income-trap/frames.cjs`：每个镜头一帧
6. `python3 scripts/middle-income-trap/render.py`
7. `npx remotion still src/index.ts MiddleIncomeTrapCover out/middle-income-trap/delivery/youtube-cover.png`
8. `python3 scripts/middle-income-trap/package.py`：桌面「跨越中等收入陷阱-上传」

各部分在哪：
- 镜头清单：`scripts/middle-income-trap/edit.json`，61 个镜头。
- 画面：`src/videos/middle-income-trap/MiddleIncomeTrapVideo.tsx`。
- 封面：`Cover.tsx`，只放 Yancy 的问句「是什么，让一个人或者国家停在天花板下面呢？」（10-26 定），右上角是系列彩带。
- 插图：23 张 Codex 插图，提示词在 `docs/middle-income-trap/codex-prompts.md`，每张右下角标「AI 插图」。
- 真实的人和事件不用 AI 画：
  - 金：用上一集的公有领域照片。
  - 法国：用图标卡。
  - 阿根廷：用数字卡和两城示意图（磁盘上没有地图数据，不另外下载）。
- 音乐沿用系列已授权的三首：萨蒂 → 咏叹调（第 6 段）→ 耶稣，世人仰望的喜悦（第 7 段）。李录原声前 1.2 秒退掉，原声后 1.0 秒回来。
- 混音 −16 LUFS。

## 李录原声

**来源**
- Columbia Business School 官方 YouTube《36th Annual Graham & Dodd Event with Li Lu '96》，https://youtu.be/YRhnX_JAbC8 ，2026-10-05，纽约 Metropolitan Club，主持 Tano Santos。
- 2026-10-25 用 yt-dlp 下载 720p，经 Yancy 同意。文件在 data 目录 `footage/lilu-cbs-2026-10-05.mp4`，960×720，88 分钟，353 MB；同目录有 YouTube 英文字幕。
- 中文字幕用哥大官网的官方中文翻译。PDF 在 education 仓库 `sources/talks/`，页码见下表。

**画面**：原片是 16:9 画面加上下黑边，各 90 px。裁成 960×540（y=90），再放大到 1920×1080。

| 片段 | 原片时间 | 长度 | 内容 | 放在 | 中文字幕出处 |
| --- | --- | --- | --- | --- | --- |
| A | 00:39:40.55–00:40:21.60 | 41.1 s | many countries have reached that level and stagnated there … never really break away from it | sc00-01 之后 | 中文稿 p. 10 |
| B | 01:24:17.75–01:25:04.05 | 46.3 s | On the zero-sum game, the trouble is … compound your knowledge … in the trusting way | sc02-10 之后 | 中文稿 p. 20 |
| ~~C~~ | 00:08:02.35–00:08:28.90 | 26.6 s | when Warren practices … circle of competence … study more and make it better | 已删（Yancy 10-25） | 中文稿 p. 3 |

- 切点用 stable-ts（small.en）按词定，前后各留 0.2–0.45 s。切好的文件在 data 目录 `clips/lilu_{A_trap,B_zero_sum,C_circle}.mp4`。
- 片段 A 从 "And so many countries" 开始，前面那句 "the Chinese government has a decision to make" 不用。

**每段的处理**
- 片段带原声播放，音乐在片段前 1.2 s 退掉、片段后 1.0 s 回来（照 fun-informatics-03 的 `QUIET`）。
- 片段结束后停 0.8 s，再接 Yancy 的复述。
- 片段期间，屏幕下方有一行出处：「李录 · 哥伦比亚商学院 · 2026-10-05」。

## 进度条（Yancy：让人可以跳过；10-25：像魔方那期一样）

照魔方 2×2 那期的章节条（`claude/cube-2x2-film` 分支的 `ChapterTrack`），组件在 `src/videos/middle-income-trap/ChapterBar.tsx`：
- 全宽分段，比例和 YouTube 按章节画出来的进度条一致；
- 每段上方都写章名，当前章亮起；
- 金色 ▼ 跟着播放点走；
- 片头有「点下面的进度条，跳到任意部分」和每段上方的 ↓；
- sc00-09 指向「证据」（可以跳过）和「学什么有用」（直接到这里）。

细节见 [video-plan.md](docs/middle-income-trap/video-plan.md)。画面上的条点不了，真正的跳转靠 YouTube 章节，`package.py` 从时间轴生成，第一章 00:00。

**章节**
- SC00 李录的问题
- SC01 证据
- SC02 学什么有用
- SC03 学习不一定要有用
- SC04 什么才是有用
- SC05 普通家庭怎么办
- SC06 “终将”
- SC07 芥菜种

## 配音

- `yancy/zh`，`zero-shot-instruct`。全片一个基准读法；只在 SC06（凝重）和 SC07（希望）换语气。指令见 `scripts/middle-income-trap/narrate.py` 的 `TONE`，里面没有「慢」字。
- 庄子那句和经文那句标了「慢 0.9」，是故意放慢的。
- **语速：定为 1.2**（Yancy 2026-10-25 听过三版后定）。Yancy 同时要求：按文案的重点词、重点句加重，该慢的地方放慢。标注稿在 education 仓库 `output/papers/middle_income_trap/跨越中等收入陷阱_重点标注_v0.3.md`，等 Yancy 看过，再改演绎稿、配全片。
  - 当初试的是 1.2 / 1.3 / 1.4 三版。
  - 2026-10-25 配出来的中位语速（只算说话时间）：1.2 → 4.5 字/秒，1.3 → 5.0，1.4 → 5.5。「法国人走上街头」是 3.2。
  - Whisper 全过。sc00-04 的「供给」强制读 jǐ，因为模型常读成 gěi。
  - 试听样片在 data 目录 `samples/开头试听_语速{1.2,1.3,1.4}.mp3`，含原声 A 和停顿，每版约 1 分半。定下的数要写进这里、SCRIPT-AND-VOICE.md 第 5 节和 `scripts/voice_defaults.py` 的 `yancy/zh`（那份文档还在另一个分支上，没合）。
- **命令**：
  - `../lucas-academy-media/.conda/bin/python scripts/middle-income-trap/narrate.py --check-only`：演绎稿和字幕逐句对齐。
  - `… narrate.py --speed 1.3 --section sc00`：配一段。
  - 输出到 `lucas-academy-media/outputs/yancy/zh/middle-income-trap-v1/s<speed>/`。
- 每条都要过 Whisper。易错字列在演绎稿末尾。

## 中文配音（2026-10-25 配完）

- 77 句，语速 1.2，全部过了 Whisper。被标出的 7 句里，多数是同音字或繁体字造成的低分：李录 → 李路／理录，罢课 → 霸克，源自 → 原字，便士 → 辩试，哈代 → 哈黛。真正改的只有两处：
  - sc00-06「怎么讲」换成 take2；
  - sc00-05「供给」强制读 jǐ。
- 「仆人」「欧几里得」用拼音强制读过一遍，Whisper 听到的和原来完全一样，所以保留原来那一条。
- 拼音是替换那个字，不是加在字后面：`欧[j][ǐ]里得`、`[p][ú]人`。
- 语速：普通句中位 4.5 字/秒，放慢的句子中位 4.0 字/秒（约 −11%）。
  - 列举、连问的句子带着句中停顿，量出来偏慢：sc02-02、sc02-04、sc05-07。
  - 短句偏快：sc00-06、sc02-11。
  - 这几句要 Yancy 用耳朵听。
- 全片 13.4 分钟（不含音乐），章节：
  - 00:00 李录的问题
  - 01:45 证据
  - 03:24 学什么有用
  - 05:46 学习不一定要有用
  - 07:33 什么才是有用
  - 09:13 普通家庭怎么办
  - 10:52 “终将”
  - 12:19 芥菜种
- 时间轴、混音和字幕由 `/Users/yqin/repo/playground/lucas-academy-video/.venv-align/bin/python scripts/middle-income-trap/build_timeline.py --speed 1.2 --listen` 生成；worktree 里没有 .venv-align，要用主 checkout 的。
- 试听：data 目录 `samples/全片试听_中文_语速1.2.mp3` 和同名 `.zh-Hans.srt`。

## 画面（初步，已由 video-plan.md 取代）

规则沿用「法国人走上街头」：
- 公有领域画作和文献（Wikimedia，避开 BY-SA）；
- Pexels 片段只作气氛；
- 不用 AI 生成的「像真的」新闻图；
- 学生作品不经同意不用；
- 出处统一写进 `art/sources.json`。

| 段 | 想法 |
| --- | --- |
| SC00 | 开场标题卡 → 李录原声 A → 复述时用对谈画面的定格加字幕 → 「供给？需求？制度？」三个词逐个出现 → 停 1.8 s，切到 Yancy 的章节卡 → 「我认为：教育的质量」 |
| SC01 | 简单数字卡：「多上一年学 ≈ +9%」；地图标出韩国、台湾、爱尔兰与拉美；「上了几年学」对「学会了多少」两根柱 |
| SC02 | 一串专业名逐个弹出；一个大字「卷」；考场、自习室气氛片段（Pexels）；流水线片段对「标准化」；原声 B |
| SC03 | 拉斐尔《雅典学院》里的欧几里得（公有领域）；旋转的盘子；哈代的旧照（待查版权）；数论到加密的一个锁图标；陆治《梦蝶》或其他公有领域庄子画；原声 C |
| SC04 | 文字卡「谁选的，为谁选的，漏掉了什么」；孩子发呆、玩玩具的气氛片段 |
| SC05 | 1963 年华盛顿游行的美国政府公有领域照片；法国片里已有的抗议素材（沿用 sources.json 的授权）；家长和孩子一起玩的片段；Lucas Academy 标志 |
| SC06 | 布宜诺斯艾利斯港和芝加哥的 1900 年代旧照（PD-AR、美国国会图书馆）；地图；空教室 |
| SC07 | 芥菜、发芽的延时片段；鸟在树枝上；经文字卡（和合本） |

## Yancy 看过第一版成片（2026-10-26）

- **先停下视频和配音。** Yancy 要细看文案，会大改。文案给了 education 仓库 `output/papers/middle_income_trap/跨越中等收入陷阱_文案_v0.3.md`，逐字就是现在成片里的配音。等改完，按新稿重配、重剪。
- **作者行**：片头、片尾、简介照旧写「Yancy Qin | Lucas Academy」。
- **封面问句**：「是什么，让一个人或者国家停在天花板下面呢？」（Cover.tsx 已改）。
- **画面上的字要中英双语**，英文比中文稍小一点。Yancy 是从章节卡说起的；上一集「法国人走上街头」的片名和图卡就是中文在上、英文小一号在下。重剪时章节卡、进度条、大字卡、数字卡、关键词都照这个做。章节卡本身 Yancy 还要再确认。
- **欧几里得插图多了一只手**（三只手）。其余 22 张逐张查过手和手指，没有问题。06-euclid 让 Codex 只改这一处，存成 `06-euclid-v2.png`。

## 文案 v0.4（2026-10-26，等 Yancy 定稿）

Yancy 在 v0.3 上改了几处，并在括号里加了几段（原样存为 education `output/papers/middle_income_trap/跨越中等收入陷阱_文案_v0.3_Yancy批注.md`）。
助手按批注放好位置，做了轻润色，又补了两块，写成 `跨越中等收入陷阱_文案_v0.4.md`：

- 一块是家长利用碎片时间和孩子一起学、一起玩，引了数字棋、睡前数学、《传送门 2》三个研究；
- 一块是结尾把各章串起来的回顾。

**v0.5 最终稿（10-26，等 Yancy 再审一遍）**：v0.4 全部接受，另外改了四处。
- 删掉机会成本后面那句可选的例子。
- 「学语文」改成「学语言」，Yancy 不想限定在中文语境。
- 《传送门 2》换成任天堂的两个研究：《超级马力欧 64》（Kühn 2014）和《集合啦！动物森友会》（Johannes 2021）。
- 最后一句用 Yancy 自己改的：「……愿意了解世界，愿意真正地了解他人，这一点点的道，一定会在我们心中发芽……」。

配音约 4,408 字（v0.3 是 3,306 字），成片估计 17 分钟左右。v0.5 文件末尾列了新加内容的来源，打包时要并进 `package.py` 的 SOURCES。**审完以前不改 zh-edit.md，也不配音、不重剪。** 审完后要做：

- **「可以点击右上角，看我们另一个视频」**（学什么有用一章）：
  - 画面加一个箭头，指向右上角；
  - YouTube Studio 在同一时间点加卡片，链到《一根冰棍，要花多少钱？｜趣味经济学1》，片尾画面也可以再放一次；
  - 这里没有记那一集的 YouTube 链接，上线以后才能加卡片。
- **爱因斯坦那句**：画面标「爱因斯坦引用」，出处只写书名 *Out of My Later Years*（原话 "Thus the wit was not wrong…"，在 Citadel 1984 年版第 36 页）。那句话不是他自己的，不要写成他的原话。
- **新加的问句**照规矩用 1.1 倍速，句后停 ≥1.2 秒。
- **新章节内容要配图**：机会成本、织毛衣、数字棋、睡前数学、一起玩电子游戏、回顾。真人真事不用 AI 画。

## v0.5 重配、重剪（Yancy 2026-10-26：「可以了，开始配音和重剪吧」）

- **稿子**：`zh-edit.md` v0.5 逐字照 education 仓库 `跨越中等收入陷阱_文案_v0.5.md`（98 句，4,408 字），句子重新编号；`voice-direction.md` 里没改的句子读法一字不动。
- **配音**：takes 换到 `lucas-academy-media/outputs/yancy/zh/middle-income-trap-v2/`。`narrate.py --reuse <v1 目录>` 把读的字、语气、慢速、语速都相同的 74 句从 v1 复制过来（就是第一版成片里那一条），只配改了的 5 句和新加的 19 句。`--plan` 先列出要配哪几句。
  ```
  ../lucas-academy-media/.conda/bin/python scripts/middle-income-trap/narrate.py --speed 1.2 --question-speed 1.1 --reuse ../lucas-academy-media/outputs/yancy/zh/middle-income-trap-v1
  ```
- **画面上的字全部中英双语**：edit.json 里写「中文|English」，中文在上、英文小一号在下（约 0.6 倍，大字 0.45 倍）。片名卡加英文片名 Crossing the Middle-Income Trap 和系列英文名；章节卡写「第 N 段 · Part N」加英文章名；进度条每段中文下面一行短英文名（`edit.json` 的 `chapters`，`build_timeline.py` 写进 timeline）；AI 插图、李录出处、图表、片尾也都加了英文。封面没动（只放问句，Yancy 10-26 定）。
- **sc00-09 跳过箭头**（Yancy：「这句的时候要加个箭头，有需要可以跳」）：画面压暗一半，进度条上方从「证据」起点画一道金色大弧，落在「学什么有用」起点，写「认同的话，可以跳过这一段 / Agree? You can skip this part」和「直接到这里 / Jump to here」。第一版那两个小提示太不显眼。
- **sc02-07「可以点击右上角」**：右上角稍往里放《一根冰棍，要花多少钱？》的封面小卡，一支箭头指向右上角（YouTube 卡片的提示就从那个角弹出来，小卡不能压在那里）。`package.py` 把这句的时间写进上传说明，在 Studio 里那个时间点加卡片。
- **新镜头**：机会成本的影子图、AI 能力卡、织毛衣、爱因斯坦引语卡（只写引用，不画人）、「学习的陷阱」卡、厨房、数字棋数字卡、睡前数学、马力欧和动物森友会两张数字卡（只写研究，不画游戏角色）、一起玩游戏、结尾回顾清单（每章一行，跟着旁白亮起）。新插图见 codex-prompts.md 第三批。
- **配乐**按章节起点接（SC00、SC06、SC07），句子再编号也不会错位。
- `build_timeline.py --draft`：还没配的句子用静音占位，只用来提前看画面，不能拿来渲染交付。
- **Whisper**：24 句新配的大多是同音字低分（量一量 → 凉一凉、终将 → 中疆、掷骰子 → 至头子，骰读对了 tóu）。真要重配的两句：sc05-01「呼吁」被读成像「普遇」，sc05-11 漏了「也」、「认路」不清。各配 take2，两个模型都听对了，换上；原来那条存成 `.take1.wav`。
- **成片（2026-10-26 22:00）**：17:24，98 句、2 段原声、78 个镜头、5 张新插图（24～28，28 用 -v3）。−16.8 LUFS、峰值 −1.3 dBFS，没有黑帧，字幕 293 条。章节：00:00 李录的问题 · 01:50 证据 · 03:30 学什么有用 · 07:15 学习不一定要有用 · 08:22 什么才是有用 · 10:27 普通家庭怎么办 · 13:23 “终将” · 14:51 芥菜种。已打包到桌面「跨越中等收入陷阱-上传」，YouTube 卡片在 04:07。关键画面 data 目录 `samples/v0.5-关键画面.png`。

## 章节卡和双音轨（Yancy 2026-10-26：「章节卡可以简短一下，章节卡要中英文，视频里所有 label 都要中英文，这样回来就做双音轨了」）

- **章节卡**（Yancy 10-26 看过建议的 8 张：「可以」）：8 段每段都有，包括第 1 段（片名卡之后）。一张小卡：「第 N 段 · Part N」、中文章名、英文章名，在画面正中停约 2.5 秒（`CARD` 2.9 秒含淡入淡出），不再按镜头类型挑。以字卡开头的几段，字卡的字等章节卡收起再出：sc05-01 的「普通人、普通家庭 / 怎么办？」改到 @0.42、@0.55，结尾回顾整张在卡片收起后淡入，第一行改到 @0.38。
- **所有字中英双语**：片尾出处补齐英文（中文字幕出处、公有领域）。edit.json 里没有只写中文的字了。
- **重渲染（2026-10-26 22:42）**：加了 8 张章节卡、片尾出处补齐英文，其余不变。17:24、−16.8 LUFS、峰值 −1.3 dBFS、没有黑帧，已重新打包到桌面。
- **Yancy 听出的两处读音（10-26）**：sc01-08「换了一个量法」的「量」读成了 liàng，sc02-18「超过很多人」的「很」不是三声。先用强制拼音（`[l][iáng]`、`[h][ěn]`）重配，Yancy 听了「还是不对」：这种标记只是提示，模型不一定照读。改成读的字换同音字，配四条候选给 Yancy 挑（data 目录 `samples/读音候选_1梁_2凉_3狠_4不加重.mp3`），Yancy：「这两种方法都没问题」。用「梁法」和「狠多人」；sc01-09「这样一量」也照样写成「一梁」重配。替换下来的存成 `.liang4.wav`、`.hen-off.wav`、`.hotfix.wav`。Whisper 听不出声调，这类只能靠耳朵。
- **sc05-01 要读成问句**（Yancy：「应该是疑问句 不是陈述句」）：原来「呼吁教育制度改革？从上到下的改变？」读成了陈述，改用 Yancy 写的「呼吁教育制度改革，从上到下的改变吗？」，zh-edit 和 education 文案 v0.5 一起改了。新的一条 Whisper 听到「吗？」；「普通家庭怎么办？」后面停了约 1.5 秒，留着。旧的存成 `.statement.wav`。三句改读音的试听：data 目录 `samples/改读音三句_量法_很多人_改变吗.mp3`。
- **双音轨以后做**：画面现在不属于哪一种语言，英文配音可以照「法国人走上街头」那样，每句英文和中文同一时刻开始，共用这一个画面（news-education-01 的 build_timeline.py）。英文字幕另做。封面现在只有中文问句。

## 英文音轨（Yancy 2026-10-27：「做英文配音m4a吧」「也需要英文字幕，先给我」）

- **画面和中文音轨不动**，英文另出一个 m4a，上传时在 YouTube Studio 加成英文音轨；和「法国人走上街头」不同，那一集是按中英较长的一条排时间。
- **稿子**：[docs/middle-income-trap/en-edit.md](docs/middle-income-trap/en-edit.md)，句号和 zh-edit 一一对应，用英文写（不是逐句翻译），按每句中文的时长写短，约 2.7 词/秒。引文用英文原文：Heath 译的欧几里得、Feynman、Hardy、Einstein、Freire、WEB 经文（太 13:31–32）；庄子是我们自己译的。
- **配音**：`narrate_en.py`，yancy/zh 音色走 CosyVoice cross-lingual，每段的语气照中文（基准 / 凝重 / 希望），陈述 1.1、问句 1.0，中文 `慢 0.9` 的句子同样放慢。takes 在 `lucas-academy-media/outputs/yancy/en/middle-income-trap-v1/`。sc00-01 原来 "Can a country" 被听成 "kind of country"，改成 "Could a country"。
- **合成**：`build_en_track.py`。每句英文从中文那句的时刻开始，前一句超时就顺延（报出来），最多顺延 3 秒；碰到下一段原声或片尾就加快，最多 1.15 倍，再不够就停下来让人改稿。配乐、压低、响度照中文。输出 `delivery/middle-income-trap.en.m4a`（和成片一样长）。
- **英文字幕**：`build_en_track.py --srt-only` 不用等配音，按中文每句的时间排英文（英文和中文同时开始），所以一份英文字幕两条音轨都能用；李录两段用哥大官方英文讲稿原文。300 条，每条不超过约 64 个字符。已放到桌面上传文件夹。
- **成品（2026-10-27 09:11）**：98 句英文，Whisper 全过（低分都是数字写法、A.I./AI、Li Lu 按中文念；sc06-07 只是 Whisper 停在了句中停顿，单独转写后半句一字不差）。22 句比中文晚开始，最多 3.3 秒（「终将」一段约 3 秒，sc07-13 3.3 秒），只有经文那句加快到 1.076 倍。m4a 17:28，和成片差 1 毫秒，−16.4 LUFS、峰值 −1.3 dBFS。字幕按英文延长，但不压到下一条，300 条无重叠。桌面上传文件夹已有「英文配音.m4a」「英文字幕.srt」，上传说明写了怎么加音轨。英文版预览（成片配英文音轨）在 data 目录 `samples/跨越中等收入陷阱_英文音轨预览.mp4`。

## 开场钩子（Yancy 2026-10-27）

Yancy：「开场附近加一两句往后的钩子，表明不只是谈国家层面的问题，是和普通人普通家庭跟发展很有关系的」。看过两个放法后，Yancy 写了这句，放在第一句后面：「其实不只是国家。一个人、一个家庭，也会碰到这样的天花板。这一集我们先从国家说起，最后我会落到在我们每个人家里，我们怎么办，我们如何与我们的子女一同成长。您也可以根据进度条直接跳到后面的部分。」

- zh-edit v0.6 / en-edit v0.2：新句是 sc00-02，原来的 sc00-02～09 顺延成 sc00-03～10。
- 中文 takes 搬到 `middle-income-trap-v3`（`narrate.py --reuse` 按读的字对上 98 句），英文 takes 按同样的编号改名搬到 `outputs/yancy/en/middle-income-trap-v2`，只新配 sc00-02。「成长」读的字写成「成掌」。
- 画面：sc00-02 用 `20-climb-together`（大人牵孩子上台阶）；说到「根据进度条」时，进度条的「跳到任意部分」提示（每段上方 ↓）再亮一次（edit.json `barHintAt`）。
- 片子变成 17.8 分钟，章节时间都往后挪了约 17 秒；上传说明、字幕、英文音轨都按新时间重出。
- Yancy 看过改后的开头：「文案没问题！不需要改，这个重复是正常的！」sc00-09「这不只是国家的事」留着。sc01-09「这样一量」用现在片子里那条（一梁）。
- **成片（2026-10-27 10:44）**：17:45，中文 −16.8 LUFS、中文字幕 299 条；英文音轨 17:45、−16.4 LUFS、英文字幕 305 条；卡片 04:25。已打包到桌面「跨越中等收入陷阱-上传」。
- **英文封面（2026-10-27）**：`Cover.tsx` 的 `MiddleIncomeTrapCoverEn`，同一张图，只放英文问句 What Keeps a Person or a Country Stuck Under the Ceiling?（Ceiling 用余烬橙），右上角彩带写 Lessons from the Headlines，照「法国人走上街头」的英文封面。桌面上是「跨越中等收入陷阱-英文封面.jpg」，package.py 以后自动带上。

## 还没定的

0. ~~章节卡~~：每段都有、简短的中英双语小卡（10-26 定）。
1. ~~基准语速~~：已定 1.2。开头要按 Yancy 的意见重排：原声 A 挪到「是供给？需求？还是制度？」之后，前面加「我们先听听李录怎么讲」，钩子再加强；三个方案见标注稿。
2. ~~片名和封面~~：片名「跨越中等收入陷阱｜从新闻看教育」，封面放问句（10-26 定）。
3. 太 13 那句的说法，要 Yancy 自己定（education 整理稿 §3 第 10 段）。现在照 Yancy 原话念。
4. 英文版：等中文版完成后再说。
