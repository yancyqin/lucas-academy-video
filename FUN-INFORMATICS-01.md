# 计算机怎么算 1+1=？ / How Does a Computer Add 1 + 1=?

**Fun Informatics 1 · 趣味信息学1**（系列原名「信息论导论」，2026-10-07 改成 Fun Informatics / 趣味信息学）。一部约 15 分钟的片子，画面几乎全部来自 Inception Space 的
**The Pixel Science Room**（`mr-yancys-class-room`，inception-space-ui）：三幅 Live Painting 全部用上
（Pixels 十段、From Bits to Meaning 八段、Three Games 五段）、房间中央的 Nativity 3D 扫描全息、
四篇 Reader 展签、围棋盘点线玻璃、入口墙的土星展（只在全景里）。房间外只补三样：一段自己算出来的
分形放大、三张 Codex 电路图、一张画在房间玻璃上的"两个开关两盏灯"。

两个问题，一条线：开头先问「电脑的图像能不能无限放大？」（Q1），再用「电脑怎么算 1+1=？」（Q2）作引子；
像素讲完回答 Q1 的上半，开关相加回答 Q2，游戏和分形回答 Q1 的下半，香农收尾。

配音稿（可直接进 lucas-academy-media 的 `build.py` 流水线，段落/编号正则 VG/vg 改成 IT/it）：
[docs/fun-informatics-01/zh-edit.md](docs/fun-informatics-01/zh-edit.md) ·
[docs/fun-informatics-01/en-edit.md](docs/fun-informatics-01/en-edit.md)。95 句。
分形放大的渲染脚本：[scripts/fun-informatics-01/mandelbrot_zoom.py](scripts/fun-informatics-01/mandelbrot_zoom.py)。

## 1. 已定的事（Yancy，2026-10-06）

- **片名**：「电脑怎么算 1+1=？」/ "How Does a Computer Add 1 + 1=?"。封面只放这一个问句，中文大、英文小。
- **长度**：一部拍完，带停顿和卡片，不切成两部。
- **开头加 intro**：先问 Q1，放一段分形放大。"看起来可以。真的是这样吗？"然后才进 Q2。
- **IT01 加电路画面**：电脑里没有数字、只有开关，配电路板、芯片、晶体管的画面，Codex 生成。
- **1+1 是引子**，引出更深的问题：图像到底有没有最小单元？"无限"从哪里来？
- **三幅画全部用上**，包括 Three Games 73–85 s 的「YOUR FAVORITE GAME.」：那张图是 Yancy 从 Printables 的
  Link 透光浮雕模型重做成几千个彩色像素的（出处和许可记在 lucas-academy-inception-space
  `content/pending-room/yancy/ASSET-MANIFEST.md`：上传者把模型标为 CC0 / 公有领域，明确允许混用和商用；记录里也写了这不覆盖任天堂对角色本身的版权和商标，公开发布前要再评估）。
  片里只出现 12 s，作为"你最喜欢的游戏也是这样做出来的"一句的画面；要是上传后收到版权申诉，
  这一镜换成一张文字卡就行，旁白不用改。

封面底图：分形放大的一帧，或 Bits 墙 15–22 s（`TWO STATES`）。片内开场卡：片名 + 系列名 + 作者（v3 起是「作者 Yancy Qin, Louise Yang | Lucas Academy」）。

### v2（Yancy，2026-10-06 晚 → 10-07）

看完 v1 成片后改了顺序和台词，台词稿 [docs/fun-informatics-01/script-v2.md](docs/fun-informatics-01/script-v2.md) 是他确认过的版本：

- 「电脑」全部改成「计算机」，片名、封面、YouTube 标题一起改：「计算机怎么算 1+1=？」。
- 开场第一句先问 1+1；分形不再定格，一直放大到「真的是这样吗？先把这个问题放一放」。
- 数数讲细：为什么二进制也要进位（每个位置只有开、关）；墙上 0000 → 0100 每一行出现时正好说到它（拆成五小句）。
- 加法器整段挪到数数后面，接着「所以 1+1 写成 10」和「一直加到第 65 次是 01000001」；新加一句把两盏灯连起来读成 10。
- 删掉三句：「最右边那一位变得最快」「规则补全了信息」「规则也有尽头」（连同算过头的分形）。
- 香农尺子上的 0 换成「两面都是正面的硬币」（原来的太阳例子听着别扭）。
- 结尾「按 E」改成「按 R」（R 才是打开展签）。
- 没改的句子沿用 v1 的录音（按原编号对应），只重配改动的句子；配音在 `outputs/louise/{zh,en}/fun-informatics-01-v2`。
- 中文 it04-07（「开、开：和灯灭，进位灯亮。把两盏灯连起来读……」）是拼起来的：整句配了 13 次，Whisper 每次都把「灭」或「进位」听偏；
  前半句用 v1 已核对过的 it07-06 录音（0–3.8 秒），后半句单独配（一次通过），中间留 0.3 秒。拼好后整句 Whisper 又把两处「进位」都写成「静位」，
  可两半单独听都是「进位」——是 Whisper 按上下文猜字，不是读错。
- 同一段文字用 `--only` 重配，CosyVoice 每次给出一样的结果；`retake.py` 因此每次重试换一种标点。
- 数数五小句：墙上第 k 行的比特从 38.5 + 2.45k 秒开始聚、「→ k」约在 41 + 2.45k 秒亮；每句取 [39.9 + 2.45k, 42.35 + 2.45k]，
  一开口那一行已经在，说到数值时「→ k」亮起。

### v3（Yancy，2026-10-07）

- 系列名「信息论导论 ①」改成「**趣味信息学1**」（英文 Fun Informatics 1），开场卡、结尾卡、it11-07 卡和 YouTube 标题一起改；
  开场卡顶上的英文小字也从 `INFORMATION THEORY 01` 改成 `FUN INFORMATICS 01`。
- 作者改成「**作者 Yancy Qin, Louise Yang | Lucas Academy**」（英文片 "By Yancy Qin, Louise Yang | Lucas Academy"），开场卡、结尾卡、YouTube 说明都换。
  Yancy 确认是 Louise **Yang**（第二集方案里写的 Louise Meng 是笔误）。
- 系列英文名定为 **Fun Informatics**（中文 趣味信息学）：仓库里这一集的文件夹、组件、合成和交付文件都从 `information-theory-01`
  改成 `fun-informatics-01`（合成 `FunInformatics01Zh` / `FunInformatics01En`，npm 脚本 `fi01:*`；配音在
  lucas-academy-media `outputs/louise/{zh,en}/fun-informatics-01-v2`）。台词编号仍是 `itNN-MM`，配音文件都按它命名，不改。
- it06-10 立方体 → 球 → 圣母与圣子：不再是四段跳切，改成 pixels-close 第 138–193.8 秒**一镜到底、曲线变速**（新的 `ramp` 画面：
  关键帧 = [镜头第几秒, 画的第几秒, 那一刻的速度]，两帧之间用三次 Hermite 曲线，速度连续变化）。慢点对着台词：
  「立方体」时 1×，「变圆、变成一个球」时加速（中文最快约 18×，英文句子短，最快约 38×），「球」落下时慢下来，
  「散开」「聚成」约 1–3×，「圣母与圣子」说完时人像正好完整（第 191 秒），之后 0.4–0.5× 慢慢走到 193.8 秒；画在 194.1 秒开始淡出，不碰。
- 中文配音三处：
  - it06-04「落下来了，落到」读成了 là：朗读文本换成同音单读字「**洛**」（字幕不变），一次通过。
  - it10-03 结尾多出约 1 秒含糊人声（听着像「先进方」，在「一定能猜到。」后 8.7–9.6 秒）：录音在句末停顿处剪掉（7.6 秒），没重配。
  - it10-10「它是量出来的」读成了 liàng（Whisper 脱离上下文也听成「亮出来」）：朗读文本换成「**梁**」。整句重配 4 次，「量」都对了，
    但每次「省掉」都变成「审调」、「降生」常变成「降身」，所以又拼：前半句和后两句用原录音，「它是梁出来的。」取第 1 次重配
    （4.55–6.37 秒，压 2.2 dB 和原来那句一样响），停顿 0.54 / 0.97 秒，和原来的 0.52 / 1.03 秒一样。
  - 同一个「量」还在 it10-01（一把量信息的尺子）和 it10-11（都用这一把尺子量）：脱离上下文 Whisper 听成「良」「量」，没听成「亮」，所以没动。
  - it01-02「当然是 2。」改成「当然是 2 呀！」（Yancy，合并 PR 之后）。新录音一次通过，比旧的短 0.335 秒（旧的句尾还多出约 0.3 秒杂音），
    所以这句后面的停顿从 0.8 秒加到 1.135 秒，后面整片的时间一帧不动：画面直接沿用渲染好的分段，只换了混音。录音开头 0.62 秒有一下咔嗒声，
    会让裁剪留下 0.7 秒空白，已经清零。
- 英文稿 `en-edit.md` 的分段标题改成英文（原来照抄了中文），英文 YouTube 说明的章节名从这里读。
- YouTube 说明照 README "YouTube tags"（`scripts/youtube_tags.py`）：标签全小写，hashtag 先放 9 个默认的（#education … #lucas_academy），
  再放本片 6 个，一共 15 个；文件分【标题】【简介】【标签】【上传设置】四块，简介可以直接粘贴。
- **默认配音**（Yancy 确认，README "Narration voices"，`scripts/voice_defaults.py`）：fangfang/zh 零样本、无指令、1.15；
  louise/zh zero-shot-instruct、1.0、「请用好奇、慢慢探索的语气……」（就是本片中文原来的设置，中文片不动）；louise/en instruct、1.0、
  梵高那段 adventure guide 指令。英文旁白按新默认整段重配，录音在 `outputs/louise/en/fun-informatics-01-v3`（v2 留着）；
  `narration.py` 从 `voice_defaults.py` 取每句的设置，两份稿子里原来的「整体语气」行换成一句说明。
- **2026-10-08 看片反馈**（初中生观众）：梵高那种英文太活泼、太快（3:41 两个 on 听着太激动），8:28「The wall says it」要懂博物馆才明白。
  - 英文配音改回原来「好奇、不着急」的设置，louise/en 默认也改回去；没改的句子直接用原来的 v2 录音（`fun-informatics-01-v4` = v2 + 改过的句子）。
  - 开关三句改成 "Both switches off / One on, one off / Both on"（中文「关、关」「开、开」不变）。
  - 把墙当成说话人的四句改掉，中英文一起：it08-06「用一句话说」/ "In one sentence"，it09-01 去掉「看第三面墙」，
    it09-05「那你最喜欢的游戏是什么？」，it11-05「最后这一句是写给你的」。只是指着画面的「看墙上」那几句留着。
  - 中文 it11-05 重配了三遍：第一遍「字母」读成了 zìmù，第二遍「像素」偏向「香醋」，第三遍两个都对。英文 it08-06 第一遍多读了一个 the，重配一次。
- 英文里的 "wall" Louise 读得怪、也不清楚（Yancy，10-08），英文稿五处全改成 "screen"（it02-01、it03-04、it06-01、it06-07、it07-02），
  只重配这五句、只重渲英文片；中文「墙」不动，中文片的英文字幕跟着变成 screen。

## 2. 主线：两个问题，一条线

### 2.1 逻辑链

```
Q1 电脑的图像能无限放大吗？ ── 分形放大：看起来能。真的吗？（先放着）
  └─ Q2 电脑怎么算 1+1=？ ── 引子：打开电脑往里看，没有数字，只有开关
       ├─ 开关 → 比特 → 两个符号数数：1+1 写成 10；01000001 是 65
       ├─ 规则：65 → A → HELLO（规则补全信息）
       ├─ 像素：屏幕上最小的一块；排列才是图画；RGB → 像素图；同样的点换规则就换形状
       │    └─ 回答 Q1 上半：有最小单元。存好的图放大就是马赛克；"无限"是程序每次重新算出一张新的、有限的图。
       │         程序怎么"算"？最小的算，就是 1+1 ── 回到 Q2
       ├─ 开关怎么相加：两个开关两盏灯 → 1+1=10；更大的数、乘法都是很多次 1+1；几十亿个开关 ── Q2 答完
       ├─ 算出来的数还能变成声音、动作；同一串 0 1 五种意思 ── 规则给比特意义
       ├─ 游戏怎么做：规则 + 几个数 → 算出下一帧（贪吃蛇、竞技场、你最喜欢的游戏）
       │    └─ 分形同理：一行公式 + 每个像素的坐标 → 整张图；放大 = 换几个数再算一遍
       │         回答 Q1 下半：无限不在图里，在规则里。规则也有尽头：数字的位数有限
       ├─ 香农的尺子：信息 = 要知道这件事，得问几个"是不是"。猜数 3 个问题 = 3 比特；早知道的事 0 比特；
       │    贪吃蛇一步只用问方向（最多 2 比特），其它格子规则算出来；五子棋一盘几百个问题；
       │    分形视频：知道公式就只剩几个数，一百来个问题；Nativity 扫描：两万个三角形每个都得问，几百万个
       └─ 回到两个问题：1+1=10 是开关算的；图有最小单元，无限的感觉来自一条规则和几十亿次 1+1
```

### 2.2 段落顺序

| 段 | 问题 → 回答 | 画面来源 |
| --- | --- | --- |
| IT00 | Q1：电脑的图像能无限放大吗？看起来能。真的吗？ | 自算的分形放大 `fractal-main.mp4`，公式打在角上 |
| IT01 | Q2：电脑怎么算 1+1=？没有数字，只有开关。进房间 | Codex 电路板 / 芯片 / 晶体管开关；走廊门牌；入口 |
| IT02 | 一个位置两种样子 → 比特 | Bits 0–32 |
| IT03 | 只用两个符号数数 → 1+1 写成 10；01000001 = 65 | Bits 37–60 |
| IT04 | 65 是什么意思 → ASCII → A → HELLO | Bits 65–88；读法指南 SVG |
| IT05 | 像素：最小的一块；像素雨；2,309 点星系；RGB → 像素 Nativity；点线面；立方变球、圣母与圣子 | Pixels 15–97、133–195；Bits 93–121 |
| IT06 | **回答 Q1 上半**：像素图放大 → 马赛克；分形每放大一次重新算；程序怎么算 → 回到 1+1 | 像素 Nativity 帧 pixelated 放大；分形片段 |
| IT07 | 开关怎么相加：和、进位 → 1+1=10；更大的数、乘法；几十亿开关 | 半加器卡，画在 `mr-yancy-black.svg` 格点上 |
| IT08 | 声音、动作；同一串 0 1 五种意思；规则给比特意义 | Bits 121–176 |
| IT09 | 游戏怎么做：规则 + 几个数 → 下一帧；你最喜欢的游戏；分形：公式 + 坐标 → 每个像素 → **回答 Q1 下半**；规则也有尽头 | Games 1–85；分形片段；`fractal-overdrive.mp4` |
| IT10 | 香农的尺子：信息 = 要问几个问题。猜数 3 个；已知的事 0 个；贪吃蛇一步最多 2 个；五子棋一盘几百个；分形视频一百来个；扫描几百万个 | `ruler` 图；Games 1–15、44–70；分形小窗；Nativity 全息 |
| IT11 | 回到两个问题；墙上的两句话；下一集；结束卡 | 房间全景；Pixels 200–249；结束卡 |

- **长度**：95 句，中文约 2,400 字 ≈ 10 分钟语音，加停顿、卡片和分形片段 ≈ **12 分钟**。
- **声音**（Yancy 2026-10-06）：中英文都先试 Louise：中文 `louise/zh`，英文 `louise/en`。whole-person 试过 Louise 的中文，
  Whisper medium 抓到过几处读错（权柄读 bìng、命题读 míng、和读 kě 之类），每句都要过 check_lines；听下来不对就换回 `yancy/zh`。
  全片一种读法（zero-shot-instruct，速度 1.0）：「请用好奇、慢慢探索的语气，像带着孩子一起发现一样说。」
  两句问题 it00-01、it01-01 放慢、EXEMPT。
- **字幕**：流水线照常产 `zh-Hans.srt` / `en.srt`；上传与否沿用 2026-10-05 的决定（不烧字幕）。
- **音乐**：Echoes in the Void（Yancy / Suno，whole-person 已用），同一套混音参数（−17 dB under voice，长停顿升到 −10 dB，整片 −16 LUFS / −1.5 dBTP）。分形段落音乐可以稍抬。
- **镜头规矩**（demo/KIDS-MUSEUM-FILMMAKING）：先移动，停稳，再转向，然后才开口。移动时不说话。画里的黑场和 `WAITING...` 一律剪掉：不等它，也不解说它；段落之间的呼吸靠旁白的停顿。

### 2.3 信息论检查：能说，怎么说才不乱讲

| 片里的说法 | 对不对 | 怎么说 |
| --- | --- | --- |
| 屏幕上的图有最小单元（像素） | 对 | 说"屏幕上的图"。矢量图、分形是"存规则"，显示出来仍是像素 |
| 分形可以无限放大 | **不能这么说** | 无限的是数学里的分形，不是电脑。电脑每次只算一张有限的图；数字位数有限（double 约 16 位有效数字，放大到 10¹³ 倍左右相邻像素就算不出差别），再往下要更长的数、更多时间。片里说"无限不在图里，在规则里；规则也有尽头" |
| 1 比特 = 一个二选一的问题 | 对，有条件 | 加"两边一样可能"（1 到 8 猜数，每个数一样可能，才正好 3 比特） |
| 信息 = 要问几个"是不是"才知道 | 对 | 这是熵的标准直觉：最省的问法下，问题的个数 ≈ 比特数（8 个一样可能的答案 = 3 个问题 = 3 比特）。"能猜到的不算"就是冗余 |
| 贪吃蛇一步最多 2 比特 | 对，要说"最多" | 四个方向、一样可能才是 2 比特；蛇不能掉头，实际不到 2，所以旁白说"最多" |
| 五子棋一步约 7 个问题 | 对 | 画里的棋盘 11 × 11 = 121 个点，log₂ 121 ≈ 6.9；棋盘填满后更少，所以一盘是"几百" |
| 分形视频一百来个问题，扫描几百万个 | 对，是量级 | 分形只要中心两个坐标、放大速度、时长（约几十到一百多比特）；扫描两万个三角形、每个三个顶点、每个坐标十几比特，几百万比特 |
| 贪吃蛇只有几个数在变，规则记住了其它 | 对 | 冗余：知道规则和现在的状态，下一帧几乎全能推出来，新的只有玩家的那个选择 |
| 整盘五子棋就在 55 个选择里 | 对 | 一局棋的记录 = 落子序列；每一步最多 log₂(可走的点数) 比特 |
| 整段分形视频的信息只有几个数 | 对，要说前提 | 前提是"你也知道规则"。这是香农"双方共享码本决定要传多少"的想法，也是算法信息论（柯尔莫哥洛夫：最短的程序有多长）。片里只说"你也知道规则的话，我只要给你几个数"，不说"香农证明分形信息少" |
| 香农研究信息本身，不管内容 | 对 | 他明说语义与工程问题无关。"规则给比特意义"讲的是编码/读法，不是香农的度量，两句分开说 |
| 一切计算都是很多次 1+1 | 大体对 | 算术单元由逻辑门搭成，乘法是移位和加法；每个分形像素要算几百到几千次 z² + c。"几十亿个开关、一次次 1+1"是量级，不是精确数 |
| 存很多点 vs 存一条规则，信息差得很远 | 对 | 描述长度不同：扫描要存两万个三角形的坐标和贴图，分形只要公式和几个参数 |

## 3. 分镜与文案

成片的台词与分镜在 [docs/fun-informatics-01/storyboard.md](docs/fun-informatics-01/storyboard.md)：每句在中英文成片里的
开始时间、台词、画面（录像和秒数）、叠在上面的卡片。它从 `shots.ts`、时间线和两份稿子生成
（`node scripts/fun-informatics-01/storyboard.cjs`），所以总是和成片一致；规划阶段的分镜表制作中改动较多，已由它取代。
每句一张成片截图：`out/fun-informatics-01/storyboard/storyboard-{1,2}.jpg`（本地，不入库）。

## 4. 房间素材清单与三幅画的时间表

### 用到了什么

| 素材 | 在哪里 | 用在 |
| --- | --- | --- |
| 房间本体：32 × 32 × 8 m，六面 80% 不透明的黑色科技玻璃，围棋盘点线纹，透出太空 | `content/inception/rooms/mr-yancys-class-room.room.json`，`assets/rooms/mr-yancy-black.svg` | IT01、IT07（卡的底纹 + 地面格点）、IT11 |
| 走廊门牌 "The Pixel Science Room"（环形走廊西侧艺术区） | `museum.js` ringBayMidpoint(12) | it01-06 |
| 加载屏 + 太空舱 | whole-person 已有录像 | it00-01 |
| **Pixels: From Dots to Form**（v16，37,478 marks，254 s）全部 10 段 | `content/lpr/mr-yancys-classroom-pixels-v16.lpr.json`，东墙 z = +10.67 | IT05、IT11 |
| **From Bits to Meaning**（v1，22,388 marks，181 s）全部 8 段 | `…-information-v1.lpr.json`，东墙 z = 0 | IT02、03、04、05、06、08、11、封面 |
| **Three Games**（v1，18,672 marks，88 s）全部 5 段 | `…-games-v1.lpr.json`，东墙 z = −10.67 | IT09、IT10、IT11 |
| Nativity 3D 扫描全息（Yancy 用 Kiri Engine 扫的，Blender 清理，20,000 三角形，缩放 10 倍，hologram 渲染） | 房间 prop `p3`，`objects/nativity-c22216b50f9a.glb` | it10-11 |
| 土星展 "How a 3D Object Is Made"（素形 ｜ 上色，北墙） | `entranceExhibit.js` | it01-07、it11-08 的全景里 |
| Reader 展签 ×4：Start Here、Wall 01、Wall 02、Wall 03 | `content/inception/museum-labels/mr-yancy-*.html` | it10-11、it04-06；Wall 01 / 03 的图单独用 |
| `mr-yancy-bits-reading-guide.svg`（01000001 → 65 → A + 四张读法卡） | `assets/rooms/` | it04-03、it04-06 |
| `wall-1-triangles-to-3d.png`（散三角 → 剪影 → 圣母线框） | `assets/rooms/` | it05-11、it10-12 |
| `mr-yancy-preview-{pixels,information,games}-lpp-front.png`、`…-games-arena-start.png` | `assets/rooms/` | Reader 页里出现；information 图是封面备选 |
| 三个 Reader 球（sculptureOrb，x = 13.2）和按 E 的交互 | 房间 props | 每次开 Reader |
| 音乐 Echoes in the Void | Yancy / Suno | 全片 |

房间外的三样（都是本地文件，不提交）：

| 素材 | 怎么来 | 用在 |
| --- | --- | --- |
| `footage/fractal-main.mp4`（24 s，×2/s，到 ≈ 1.7 × 10⁷ 倍）+ `.json`（每帧的中心、宽度、倍数、迭代数） | `mandelbrot_zoom.py main`，见 §5.2 | IT00、IT01、IT06、IT07、IT09、IT10、IT11 |
| `footage/fractal-overdrive.mp4`（18 s，×8/s，到 ≈ 1.8 × 10¹⁶ 倍，最后 3 秒碎成越来越大的色块） | `mandelbrot_zoom.py overdrive` | it09-10 |
| `images/circuit-board.png`、`chip-die.png`、`transistor-switch-open.png`、`-closed.png` | Codex 生成（已生成，2026-10-06，提示词在 §5.3，`images/_generation.json` 记了来源） | IT01、it02-06 |

不用的只有 `source-galaxy.jpg`：画已经用它采样了位置，片里不需要再放原图。

### Pixels: From Dots to Form（254 s 一圈）

| 秒 | 画里发生什么 |
| --- | --- |
| 0–15 | 片头投影闪烁 |
| 15–35 | 像素雨：左 1→2→3 px 圆点，中 8 px 三角（36 个 1 px 方块、八行），右 12 px 方块 |
| 35–40 | 片头闪烁 |
| 40–72 | 2,309 个彩点各飞各的 → 聚成星系（到 63）→ 呼吸（63–67）→ 散落 |
| 72–77 | 片头闪烁 |
| 77–97 | 1,260 个 1 px 点：点（77–80）→ 线（80–88）→ 三角面（88–94）→ 淡出 |
| 97–102 | 片头闪烁 |
| 102–195 | 散三角（102–108）→ 四面体（108–115）→ 立方体（119–127，轮廓 127–147）→ 6×6 格子（133–139）→ 72% 圆角体（139–161）→ 球（161–184，179–184 加对角线）→ 散开再聚成圣母与圣子（184–195，22,882 marks） |
| 195–200 | 黑场 |
| 200–224 | 4,200 个像素写 "Pixels showing on right place, they become letters." |
| 224–229 | 黑场 |
| 229–249 | 2,200 个像素写 "and so form other things." |
| 249–254 | 黑场 |

### From Bits to Meaning（181 s 一圈）

| 秒 | 画里发生什么 |
| --- | --- |
| 0–15 | `WAITING...` 微闪，7–11.5 一粒比特落下 |
| 15–32 | `TWO STATES`（15–22）→ 两态交替 → `0   1`（20–28）→ `ONE BIT`（26–32）；比特雨 |
| 32–37 | 黑场 |
| 37–60 | `BITS → NUMBERS`：`0000→0 … 0100→4` 每 2.45 s 一行（38.5 起）；`01000001 → 65`（52–59） |
| 60–65 | 黑场，`01000001` 渐暗 |
| 65–88 | `BITS → LETTERS`：八比特重聚（65–68）→ `65`（69–76）→ `A`（74–81）→ `HELLO`（79–87） |
| 88–93 | 黑场 |
| 93–121 | `BITS → COLOR`：`65 200 255 / R G B`（97–104）→ 一个淡蓝像素（102–108）→ 像素 Nativity 聚成（101–116）→ `PIXELS → IMAGE`（108–116）→ 逐行关掉（116–121） |
| 121–149 | `BITS → SOUND` 样本 → 波形（121–133）；`BITS → MOTION` 亮点走轨迹（133–144）；轨迹收成 `01000001`（144–147） |
| 149–176 | `01000001` 居中（149–151）→ 分出 `65 / A / PIXEL / SAMPLE / MOVE`（151–165）→ 收回（165–168）→ `A CODE GIVES BITS MEANING.`（168–172）→ `TWO SYMBOLS. MANY WORLDS.`（172–176） |
| 176–181 | 黑场 |

### Three Games（88 s 一圈）

| 秒 | 画里发生什么 |
| --- | --- |
| 1–15 | `CLASSIC SNAKE · 2 APPLES`：23 步，每步 0.52 s，第 6、12 步吃到苹果 |
| 15–18 | `WAITING...` 闪 |
| 18–41 | 竞技场标题（18–21）→ 三条蛇（绿、蓝、黄）回放，每步 0.29 s |
| 41–44 | `WAITING...` |
| 44–70 | `GOMOKU`：55 步每步 0.39 s（44–65.5），赢的五连亮到 70 |
| 70–73 | `WAITING...` |
| 73–85 | `YOUR FAVORITE GAME.` + 几千个像素拼成的 Link 图（Printables 透光浮雕重做，见 §1） |
| 85–88 | `WAITING...` |

## 5. 制作流程

照 whole-person 的管线（`scripts/whole-person-01/`）复制一份到 `scripts/fun-informatics-01/`，
作品名 `FunInformatics01Zh` / `FunInformatics01En`，封面 `FunInformatics01CoverZh` / `…En`，
本地素材在 `public/fun-informatics-01/`（已加入 `.gitignore`），成品在 `out/fun-informatics-01/delivery/`。

### 5.1 录房间（已录，2026-10-06）

`scripts/fun-informatics-01/record-room.cjs`：照 whole-person 的 `record-chamber.cjs`，Playwright 开 headless Chrome，
用 dev server 的 `?debug&manual=1` 钩子按 1/30 s 推进世界时钟，人影隐藏，帧直接喂进 ffmpeg。站位都从 inception-space-ui
自己的模型模块算（`museum.js` / `hallRing.js`），不是手抄的数字。

```bash
# inception-space-ui 的 dev server：.claude/launch.json 里的 "inception-space-8110"（vite --port 8110）
PLAYWRIGHT_DIR=/Users/yqin/repo/ai-testing node scripts/fun-informatics-01/record-room.cjs <take> [--close] [--smoke]
# take = corridor | entry | bits | pixels | games | nativity | readers；--close 只对三面画有效；--smoke 录 2 s 并存第一帧看机位
```

每条写到 `public/fun-informatics-01/footage/<take>.mp4`（1920 × 1080，30 fps，关键帧每 15 帧）和 `<take>.json`
（帧数、第 0 帧的世界秒数、镜头标记 `marks`）。

| take | 长度 | 内容 | 标记（秒） |
| --- | --- | --- | --- |
| `corridor` | 38 s | 大厅出生点 → 走到南侧环口 → 转头看到门牌 → 沿环走近 → 站在内墙边正对「THE PIXEL SCIENCE ROOM」门 → 走进门 → 落进房间 | nameplate-in-view 11、at-door 27、through 33 |
| `entry` | 11 s | 落点朝北（土星双板在对面）停 3 s → 右转 90° 看到三面画 → 停 4 s | turn-right 3、facing-east 7 |
| `bits` / `pixels` / `games` | 183 / 256 / 90 s | 第一人称，离墙 7.4 m、眼高 4 m，画板占画幅高度 85%；三个 Reader 球隐藏；**第 0 帧 = 循环第 0 秒**，所以分镜里"bits 65–88"就是第 1950–2640 帧 | — |
| `bits-close` / `pixels-close` / `games-close` | 同上 | 离墙 5.4 m、眼高 3.5 m，画板占满宽度（上下各裁约 0.7 m），字更大；同样对齐循环 | — |
| `nativity` | 34 s | 从入口走到 Nativity 南侧 6 m（不录）→ 绕半圈 20 s → 走到展签球前 → R、点 Read 打开 "Pixel Science: Tiny Pieces, Big Ideas" 6 s | to-reader 20、reader-open 27 |
| `readers` | 18 s | 站在 bits 球前，R → Read 打开 "From Bits to Meaning"，慢慢滚到 "Watch the symbols gather" 的图 | reader-open 1 |

录的时候学到的，下次别再踩：

- **R 才是 Read**，E 在球旁边以外的地方会打开房间编辑器。R 先弹菜单（Read / Replay），要再点 Read 才是页面。
- **画布截帧必须和渲染在同一次 `page.evaluate` 里**：分成两次调用，浏览器在中间可能把 WebGL 缓冲清掉，结果 10–25% 的帧随机全黑。
  整页截图（Reader 那条）没这个问题。录完用 `signalstats` 数一下 YMAX < 12 的帧，应为 0。
- 站在球前（`orb=` 的传送点）球和底座正好挡在画中间，所以画的 take 先把 `propKey` 以 `-orb` 结尾的 prop 隐藏，再退到 7.4 m、升到 4 m，按 V 切第一人称。
- 相机竖直视角 65°；`ringDoorReturnPoint` 是出门时背对门站的点，要看门得转 180°，而且太近看不到门牌，改站到内墙边 4 m 外。
- 走进门后博物馆自己做过渡（星空隧道几秒）然后落进房间，`corridor` 的最后 5 s 就是这段，可以和 `entry` 接起来。
- 加载屏在 Remotion 里重画（whole-person 的 `INTRO` 代码）；太空舱用 whole-person 的 `record-chamber.cjs` 重新录了 12 s 到
  `footage/transit-chamber.mp4`（旧录像是本地工作副本，发布后已删）。

从 inception-space-ui 复制到 `public/fun-informatics-01/images/`：`mr-yancy-bits-reading-guide.svg`、
`wall-1-triangles-to-3d.png`、四张 `mr-yancy-preview-*.png`、`mr-yancy-black.svg`。

### 5.2 分形放大（自己算，不用网上的视频）

```bash
P=../lucas-academy-media/.conda/bin/python        # 有 numba + numpy；系统 python3 没有
$P scripts/fun-informatics-01/mandelbrot_zoom.py main      public/fun-informatics-01/footage/fractal-main.mp4
$P scripts/fun-informatics-01/mandelbrot_zoom.py overdrive public/fun-informatics-01/footage/fractal-overdrive.mp4
$P scripts/fun-informatics-01/mandelbrot_zoom.py main /tmp/x.mp4 --preview   # 640×360、1/4 的帧，先看一眼
```

- 公式就是 `z → z*z + c`，落点海马谷 c ≈ −0.7436439 + 0.1318259i，整集起步，`main` 每秒放大 2 倍、24 s；
  `overdrive` 每秒 8 倍、18 s，第 15 秒起 double 的 16 位有效数字用完，相邻像素算出同一个 c，画面碎成越来越大的色块，最后只剩两三块——
  这就是 it09-10 要的画面，不是 bug。
- 每一帧都是重新算的（没有存一张大图再缩放），所以片里说"每放大一次重新算一张"是真话。
- 配色用房间的青绿（navy → teal → cyan → mint）；集合内部纯黑。
- 旁边写出 `fractal-main.mp4.json`：每帧的中心、视野宽度、倍数、迭代数，Remotion 的公式/读数叠层从这里读，
  保证屏幕上的数就是算这帧用的数。
- 预览实测（numba，12 核）：640 × 360 的 180 帧 26 s；1080p 像素是 9 倍，`main` 720 帧估计 15–20 分钟，
  `overdrive` 540 帧、迭代数更高，估计 40–60 分钟。

### 5.3 电路画面（Codex，四张）

风格贴房间：深海军蓝底，青色走线，像围棋盘的点线；16:9；没有文字、没有品牌标志、没有人。
四张共用一个风格前缀，后面接各自的内容。生成后存到 `public/fun-informatics-01/images/`。

2026-10-06：四张已用内置 imagegen 生成并保存为 1920×1080 PNG；第 4 张在同一对话里以第 3 张为编辑底图，网格、固定触点和灯的位置已目视核对对齐。最终提示词、原图路径与校验值见 `public/fun-informatics-01/images/_generation.json`。

风格前缀（每张都加在最前面）：

```
Style: deep navy-black background (#06131e), thin glowing cyan lines (#59d7ff) and pale mint highlights (#a7f59b),
restrained and clean, like a dark glass museum wall with a faint grid of points and lines. Photoreal lighting, no text,
no numbers, no logos, no brand names, no people, no hands. 16:9, 1920x1080.
```

1. `circuit-board.png`（it01-03，缓推）：

```
A printed circuit board seen straight from above, filling the frame. Thin copper traces glow cyan and run in a tidy grid
with right-angle turns, small black chips and tiny components sit on a dark navy board, soft rim light, shallow depth of
field toward the edges.
```

2. `chip-die.png`（it01-04 前半）：

```
Extreme macro photograph of a silicon chip die under a microscope: dense rectangular blocks and ultra-fine parallel lines in
dark teal and cyan, a few blocks catching pale mint light, the pattern continuing past every edge of the frame.
```

3. `transistor-switch-open.png`（it01-04 后半、it02-06，开关"关"的状态）：

```
A single transistor drawn as a simple schematic: one small switch standing on a dark navy grid of faint points and lines,
the switch arm lifted open, a thin cyan wire leading in from the left and out to a small unlit round lamp on the right.
Minimal, centered, lots of empty space around it.
```

4. `transistor-switch-closed.png`（同一构图，开关"开"的状态；Remotion 在两张之间切换）：

```
Exactly the same composition as before: the same switch on the same dark navy grid, but now the switch arm is closed,
the cyan wire glows brighter along its whole length, and the round lamp on the right is lit with pale mint light.
```

要是第 4 张和第 3 张构图对不上，只留第 3 张，灯亮和线亮在 Remotion 里画。

### 5.4 配音、时间线、渲染、交付

```bash
# 1. 稿子 → 配音用的逐句 JSON（数字、二进制都写成读法；ASCII 读作“阿斯克码”/“Askey”）+ cues.json（字幕用原文）
python3 scripts/fun-informatics-01/narration.py
# 2. Louise 中英文配音（lucas-academy-media，CPU，约 1 分钟一句，两种语言可以并行）
cd ../lucas-academy-media
.conda/bin/lucas-narrate <repo>/public/fun-informatics-01/narration/zh.json --profile louise/zh --language zh --speed 1.0 --output-dir outputs/louise/zh/fun-informatics-01
.conda/bin/lucas-narrate <repo>/public/fun-informatics-01/narration/en.json --profile louise/en --language en --speed 1.0 --output-dir outputs/louise/en/fun-informatics-01
cd <repo>
# 3. Whisper 逐句核对：数字词先换成数字再比（零一零零…读对了不会被标），small 模型初筛、medium 复核，只列复核后仍可疑的句子
../lucas-academy-media/.conda/bin/python scripts/fun-informatics-01/check.py zh
# 4. 重配读错的句子，直到 Whisper 听到关键的词；同一段文字合成结果是固定的，所以每次重试换一种标点
../lucas-academy-media/.conda/bin/python scripts/fun-informatics-01/retake.py zh 'it07-04=两盏灯都不亮.*0加0等于0'
# 5. 时间线 + 旁白轨 + 音乐（Echoes in the Void，public/fun-informatics-01/music/）+ SRT；可只重建一种语言
python3 scripts/fun-informatics-01/build_timeline.py [zh|en]
# 6. 分段渲染（静音，4 段，某段卡住只重来那一段），拼接后合上混好的音轨
python3 scripts/fun-informatics-01/render.py en && python3 scripts/fun-informatics-01/render.py zh
# 7. YouTube 描述（章节时间从时间线读）+ 封面 1280×720
npm run fi01:youtube
# 8. 台词与分镜（从 shots.ts + 时间线生成）和每句一张中文成片截图的两张总表
node scripts/fun-informatics-01/storyboard.cjs
../lucas-academy-media/.conda/bin/python scripts/fun-informatics-01/sheets.py out/fun-informatics-01/storyboard-v3
```

- 时间线、混音、字幕的做法是 whole-person 的（`build_timeline.py` 直接导入它的函数）：每句先拉到 −23 LUFS，
  音乐在说话时低 17 dB、长停顿时升到低 10 dB，整片一个固定增益到 −16 LUFS，峰值 −1.5 dBFS。
- `HOLD`（每句后面多留的秒数）在 `scripts/fun-informatics-01/build_timeline.py`，给画面留时间：分形要看完、卡要读完、画要走到下一步。
- 画面的取片区间 `span` 在 `src/videos/fun-informatics-01/shots.ts`，按镜头长度自动变速，所以配音长短变了不用改。
  例外是 `ramp`（曲线变速）：关键帧按镜头里的秒数写，对着每种语言的台词，那句重配了要重新对一下。
- 第一次整片渲染卡在分形片段上（OffthreadVideo 抽帧超时）：当时配音和 Whisper 同时在跑，内存只剩几百 MB，
  分形又是 24 秒 245 MB 的高码率文件。现在分形重压成 `-tune fastdecode`，渲染改成 `render.py` 分段，没再出问题。
- 取片区间不能碰到画自己的黑场（比特墙的 32–37、60–65、88–93、144–149、176–181 秒等），碰到了成片里就是一闪黑。
  渲染完用 `signalstats` 扫 YMAX < 12 的帧，应为 0。
- 交付在 `out/fun-informatics-01/delivery/`：`fun-informatics-01.{zh,en}.mp4`、各自的 `zh-Hans.srt` / `en.srt`、
  `youtube-description.{zh,en}.txt`、`youtube-cover.{zh,en}.jpg`。

### 5.5 Remotion 合成

作品 `FunInformatics01Zh` / `FunInformatics01En`（`src/videos/fun-informatics-01/FunInformaticsVideo.tsx`），
封面 `FunInformatics01CoverZh` / `…En`。两层：`VISUALS` 背靠背铺满全片（录像、分形、电路图、静帧，交叉溶解），
`CARDS` 按句子叠在上面。新画的卡：

- `carry`：十进制 8 → 9 → 10 和二进制 0 → 1 → 10 两栏，逐行出现。
- `adder`：两个开关、两盏灯（和 / 进位）、两个规则框，按句子切开关状态；真值表逐行出现，1 + 1 = 10 金色；
  it07-07 电流沿导线流动，it07-08 四组接成一排，it07-09 铺满屏幕的开关。
- `guess`：1–8 八个数，三个问题各灭一半，留下 7。
- `ruler`：香农的尺子，七个刻度（0 · 1 · 2 · 3 · ~100 · ~400 · 几百万）按句子落上去，it10-11 全部到齐。
- `fractal-pixel`：分形定格上圈一个像素，c 进公式，迭代计数到 227，跑出去 → 它的颜色（数是 `mandelbrot_zoom.py` 算的）。
- `pixelzoom`：一帧画面按最近邻放大到 24 倍，像素变成方格。

## 6. 还要定的事

没有了。2026-10-06 Yancy 定了：片名带 "=?"；一部拍完；加 intro 和电路画面；1+1 作引子；三幅画全部用上（含 Link 那张）；
「规则也有尽头」留着；IT08 留着；中英文都先试 Louise；结尾不点下一集的题（it11-07 只说「接着香农的问题往下走」，
下一集讲什么等他学过再定）。
