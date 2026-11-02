# 诺贝尔奖：光遗传学是什么？从信息学的角度看

**Fun Informatics 4 · 趣味信息学4**。作者 Yancy Qin | Lucas Academy。

2026 年诺贝尔生理学或医学奖（10 月 5 日公布）颁给了光遗传学：从一种绿藻里找到一个「光控开关」，装进神经细胞，用光就能让它发出信号。
这一集从信息学看它，先讲**开关**（接第一集的 0 和 1），再讲**编码和解码**（光怎样把一幅画面重新送进看不见的眼睛）。

文案照 `SCRIPT-AND-VOICE.md`（2026-10-24 起的标准）：稿子是 Yancy 的，第一人称。这份文档只放结构、事实和画面，供 Yancy 挑着用；
每段的「Yancy 可以从哪说起」是提示，不是台词。（SCRIPT-AND-VOICE.md 还没提交，只在 worktree `moonlight-copyright-issue-42921b` 里，分支 `claude/project-docs-rewrite-d273a4`。）

## 1. 已定的事（Yancy，2026-10-31 / 11-01）

- **片名**：「诺贝尔奖：光遗传学是什么？从信息学的角度看」。英文片名待定（第 7 节）。
- **期数是第四期。** 2026-10-21 上传的《公开的路上，怎样共享一个秘密？｜迪菲—赫尔曼密钥交换》（https://youtu.be/RtF84AxdzjU）是单独的一部，不算进趣味信息学。
  原来排在第四期的 Shibboleth / 校验（issue yancyqin/lucas-academy-video#28）挪到第五期；第三期结尾那句预告（「偷偷改掉一个字……我们下次再说」）由第五期接上。
- **先 B 后 A**：先讲开关，回顾第一期的 0 和 1；再进编码和解码。主线是 A（重新看见斑马线）。
- **开场用绿藻**：Hegemann 好奇一个单细胞绿藻怎么游向光。
- **D（寻址）只说一句**：光照亮一大片，只有装了开关的那种细胞会响应。
- **C（只能看 vs 能按开关、因果）不在这一集展开**，留着以后单独做一期。这一集只用一句话交代「科学家为什么想要一个开关」。
- **文案**：Yancy 让 Claude 先起一稿（11-01）：[docs/fun-informatics-04/zh-draft.md](docs/fun-informatics-04/zh-draft.md)。
- **配音**（11-01）：还是用 Louise 和芳芳。芳芳语速快一些，1.2 或 1.3；Louise 大约 1.1。语气等文案定了再调。
- **收尾**（11-01）：圣经里的光。有时讲物理的光（创世记「要有光」；诗篇「脚前的灯、路上的光」），更多时候讲属灵的光（补经文）。
  然后问「你需要这样的光吗？除了用眼睛，还需要什么样的解码器，才能接收到这样的光呢？」
  最后不提 Lucas Academy，改成请大家订阅、留言（Yancy 11-01）：「如果你喜欢这期视频，欢迎订阅我们的频道！在这里，我们一起学习、一起思考。也欢迎你留言，告诉我们你感兴趣的话题！」
- **画面先生成，不买衣藻**（11-01）：找不到的素材由 Yancy 用 Muse 生成短视频，Claude 用 Codex 出首帧参考图（`scripts/fun-informatics-04/images.py`）。
  以后要实拍的话，莱茵衣藻的培养液 Carolina Biological Supply（item 152041）和 Ward's Science 都有卖。
- **诺贝尔官网的插图可以用**：官网写的是「非商业用途免费使用，需署名」，Yancy 确认频道没有开收益（2026-11-01）。以后开了收益，这些图要重新评估。

## 2. 这一集只讲一件事

**信息能换一种载体，只要两头约好同一套规则，意思就还在。**

- 绿藻的开关把光换成电：光一照，门一开，带电的离子流进去，就是一个电信号。
- 眼镜把画面换成一闪一闪的光，新装的开关再把光换成电，大脑学会这套新规则，画面就又回来了。
- 第一集说过：「同一串 0 和 1，五种意思。它一次都没变，变的只是规则。」（it08-05）这一集是同一个道理，只是发生在一个人身上。

## 3. 结构

| 段 | 讲什么 | 关键的一下 |
| --- | --- | --- |
| OG00 开场 | 一碟绿水，一照光，绿色往光那边跑 | 「这么小的东西，怎么知道光在哪？」→ 片名卡 |
| OG01 开关（回顾第一期） | 计算机靠开关记 0 和 1；神经细胞也是「发，或者不发」 | 第一集玻璃上的两个开关、两盏灯 |
| OG02 绿藻的开关 | 光控开关怎么找到、怎么装进神经细胞 | 蓝光一照，神经细胞发出信号 |
| OG03 从开关到消息 | 按一下是一个比特；按出一串，才是消息 | 第一集「同一串 0 和 1，五种意思」 |
| OG04 眼睛 | 眼睛自己的光开关坏了，电线还好 | 相机坏了、电线还在 |
| OG05 重新看见斑马线 | 新装的开关 + 会翻译的眼镜 + 学会新规则的大脑 | 几个月后，他认出斑马线的白条 |
| OG06 圣经里的光 | 看得见的光，属灵的光；需要什么样的解码器 | 「光照在黑暗里，黑暗却不接受光」 |

长度先按 6–8 分钟想，Yancy 写完再看。

### 3.1 OG00 开场 · 一碟绿水

- **事实**：莱茵衣藻是单细胞绿藻，大约 0.015 毫米。把它搅进培养皿，水会变成淡淡的绿色；从一边照光，绿色就往光那边移，因为这些看不见的小藻都在往光游。
  它靠细胞表面一个小小的橙色点感光，叫**眼点**。九十年代初，Hegemann 想知道：它对光的反应怎么会这么快？
- **画面**：诺贝尔官网图 2（衣藻和眼点）；要是能买到衣藻（或眼虫）培养液，可以在家实拍一碟绿水被手电照着变色（第 5 节）。
- **Yancy 可以从哪说起**：10 月 5 日看到这条新闻时的第一反应？家里谁问过「光」或「大脑」的问题？还是直接从这碟绿水说起？

### 3.2 OG01 开关 · 回顾第一期

- **第一集说过的**（[docs/fun-informatics-01/zh-edit.md](docs/fun-informatics-01/zh-edit.md)）：
  - it02-06「就像家里的电灯开关：不是关，就是开。计算机里那些小开关，记的就是比特。」
  - it04-02「两个开关，两盏灯。」开、开 → 10。
  - it07-09「一台计算机里有几十亿个这样的开关。」
- **接到大脑**：神经细胞发出的信号，要么发、要么不发，每一次都一样大（「全或无」，神经科学教科书的内容，写稿前给一个出处）。人脑大约有 900 亿个神经细胞，每个都连着几千个别的神经细胞。
  这里只说「有点像开关」，不说「神经细胞就是开关」：信号发多快、什么时候发，也都带着信息。
- **为什么想要一个开关（C 只用这一句）**：以前的方法太粗，没法确定某一种神经细胞到底管什么，诺贝尔官网说那时的大脑图像「像一张模糊的照片」。
  Crick 想过：要是能从外面按一下某一种神经细胞就好了；神经信号非常快，最好用光来按。他自己也说这个想法听着太遥远。
- **画面**：第一集 Pixel Science Room 的玻璃画「两个开关两盏灯」、Bits 墙（数据在 `lucas-academy-video-data/fun-informatics-01/public/`）；诺贝尔官网图 1（科学家梦想有一个神经细胞的开关）。

### 3.3 OG02 绿藻的开关

- **事实**（全部出自诺贝尔官网科普背景）：
  - Hegemann 测到：光照到眼点，半毫秒后就出现电信号。光照到人眼，再变成电信号，至少要 10 毫秒，绿藻快了二十多倍。
  - 他猜：绿藻里有一个蛋白，既能接住光，又是一道让离子通过的门。当时没人见过自己会对光反应的离子通道，很多人不信。
  - 2000 年前后，日本的研究者公开了衣藻的基因，Hegemann 找到两个像感光蛋白的基因，交给 Nagel。Nagel 把它们放进青蛙卵，卵的表面长出这种蛋白；光一照，门在 0.2 毫秒内打开。
    这就是**通道视紫红质**（channelrhodopsin-2）。放进别的细胞，那个细胞也会对光有反应。2003 年发表。
  - Deisseroth 在精神科见过很多病人，想弄懂活的大脑。他写信向 Nagel 要来这段基因，放进大鼠的神经细胞；蓝光一照，神经细胞马上发出信号，还能传给别的神经细胞。2005 年发表。
  - 2006 年这个方法有了名字：光遗传学。2007 年在活老鼠的大脑里成功：用一根很细的光纤照运动皮层，老鼠的胡须就动了。后来还找到能「关掉」神经细胞的蛋白，用的是别的颜色的光。
- **D 这一句**：光照到的是一大片，可只有被装上这段基因的那一种神经细胞会响应。
- **画面**：诺贝尔官网图 3（青蛙卵）、图 4（培养皿里的神经细胞）、图 5（活老鼠和光纤）。老鼠只用插图，不用手术实拍。
- **不讲**：2012 年「重新唤起恐惧记忆」的实验（对孩子太吓人，也离这一集的主线远）。

### 3.4 OG03 从开关到消息（B 到 A 的桥）

- 按一下开关，是一个比特。一串按法，才是一句话；同一串，换一套规则，意思就变了（第一集 it08-05）。
- 由此引出问题：光能不能把一整幅画面，送进一双看不见的眼睛？

### 3.5 OG04 眼睛 · 相机坏了，电线还在

- **事实**：眼睛里本来就有自己的光开关，就是视杆细胞和视锥细胞：它们把光换成电，交给后面的细胞，再通过视神经送进大脑。
  **视网膜色素变性**这种病会让视杆、视锥细胞慢慢坏掉；可后面的细胞和视神经很多还是好的。
- **可选画面**：香农的通信图（第二集讲过香农），画成眼睛：世界 →（眼镜：翻译）→ 光 →（新开关：接收）→ 大脑。

### 3.6 OG05 重新看见斑马线

- **事实**（Sahel 等，*Nature Medicine* 2021；Sorbonne、STAT、Futurity 的报道）：
  - 一位 58 岁的病人，视网膜色素变性。医生在他一只眼睛里注射基因，让视网膜神经节细胞（视杆、视锥之后接力的下一棒）长出一种类似的光控开关，叫 **ChrimsonR**。
    它对**琥珀色**的光敏感，比蓝光对眼睛安全。
  - 他要戴一副特制的眼镜：眼镜上的相机找出画面里明暗变化的地方，实时变成琥珀色的光脉冲，打在视网膜上。眼镜就是翻译。
  - 注射后大约五个月开始训练。几个月后，他开始认出斑马线的白条。在实验室里，他能找到、摸到、数出桌上的东西：笔记本 39 次里摸中 36 次（92%），小的订书钉盒只有 36%。
  - 不戴眼镜，他还是看不见。只有这一位病人，是**部分**恢复。诺贝尔官网说这类治疗还在临床试验里。
- **接回第一集**：光还是光，开关还是开关，变的是规则；他的大脑花了几个月，学会了读这套新规则。
- **画面**：Codex 示意图（标「AI 生成·示意」）：眼镜、琥珀色光点、斑马线。不画「他看到的画面」，因为没人知道他眼里具体是什么样子。

### 3.7 OG06 圣经里的光（Yancy 定的方向，11-01）

- 看得见的光：创世记 1:16「于是神造了两个大光，大的管昼，小的管夜，又造众星。」（Yancy 11-01 从 1:3 换成这一节。）诗篇 119:105「你的话是我脚前的灯，是我路上的光。」（字面是灯，讲的是神的话，当过渡。）
- 属灵的光：约翰福音 8:12「我是世界的光……」；约翰福音 1:5「光照在黑暗里，黑暗却不接受光。」（接上「接收」「解码器」。）
- 问题：你需要这样的光吗？除了用眼睛，我们还需要什么样的解码器，才能接收到这样的光呢？
- 英文片：WEB 的约翰福音 1:5 是 "hasn't overcome it"，没有「接收」的意思；KJV 是 "comprehended it not"，可以考虑用 KJV。

## 4. 事实和出处

| 事实 | 出处 |
| --- | --- |
| 获奖人、获奖理由、2026-10-05 公布、「光控开关」、大脑图像像草图 / 模糊照片 | [诺贝尔新闻稿](https://www.nobelprize.org/prizes/medicine/2026/press-release/)、[科普背景 PDF](https://www.nobelprize.org/uploads/2026/10/popular-medicineprize2026.pdf) |
| 衣藻约 0.015 mm、眼点、绿水往光移、半毫秒 vs 人眼 ≥10 毫秒、青蛙卵 0.2 毫秒、2003、2005、2006 命名、2007 老鼠胡须、Crick 的设想、900 亿神经细胞、人工耳蜗 | 科普背景 PDF |
| 关键论文：Nagel 2002 *Science*、Nagel 2003 *PNAS*、Boyden…Deisseroth 2005 *Nat Neurosci*、Aravanis 2007 *J Neural Eng* | 科普背景 PDF 的 Key Publications |
| 2021 年病人、ChrimsonR、琥珀色、眼镜、92% / 36%、约五个月后开始训练 | [Sorbonne](https://sorbonne-universite.fr/en/news/optogenetic-methods-restore-partial-vision-blind-patient)、[STAT 2021-05-24](https://www.statnews.com/2021/05/24/scientists-use-optogenetics-for-first-time-to-help-blind-patient-see/)；论文 Sahel 等 2021 *Nature Medicine*，doi 10.1038/s41591-021-01351-4（作者顺序写稿前对原文核一遍） |
| 斑马线白条 | [Futurity](https://www.futurity.org/?p=2571282)（转述 Sahel） |
| ChrimsonR 室内的光打不开，要靠眼镜给光 | [Retina Society 2020 报告（Sahel）](https://www.retinasociety.org/content/meetingarchive/2020/sahel-jose-alain-signs-of-functional-vision.pdf)、Futurity |
| 中文人名：卡尔·戴塞罗思、彼得·黑格曼、格奥尔格·内格尔 | [新华社 2026-10-05](https://www.news.cn/world/20261005/d99d6630d7e849d9a37575621a25e54d/c.html) |
| 病人是不是法国人 | 待核实（试验在巴黎做，但手上的报道没写病人国籍；核实前稿子里不说「法国」） |
| 神经信号「全或无」 | 待补一个教科书出处 |

中文用词：光遗传学、通道视紫红质、莱茵衣藻、眼点、视网膜色素变性、视杆细胞、视锥细胞、视网膜神经节细胞、视神经。

## 5. 画面素材

**镜头表**（48 个镜头，每个镜头的来源、候选缩略图、Muse 提示词、实拍清单、音乐和署名）：[docs/fun-informatics-04/video-plan.html](docs/fun-informatics-04/video-plan.html)（11-01）。
Yancy 11-01：能找到的素材就找，找不到的 Yancy 用 Muse 生成短视频。Commons 只用 CC0 / CC BY，不用 CC BY-SA。

- **诺贝尔官网插图**（Mattias Karlén 绘）。署名：「© The Nobel Committee for Physiology or Medicine. Ill. Mattias Karlén」，写进片尾和 YouTube 说明。
  - 科普图：`POP_Fig_2.jpg`（衣藻和眼点）、`POP_Fig_3_ENG_01.jpg`（青蛙卵）、`POP_Fig_4_ENG_01.jpg`（神经细胞）、`POP_Fig_5_ENG_01.jpg`（老鼠和光纤）、`NP_POM_2026_3-2_01.jpg`；
    科学背景图：`ADV_FIG_1_02.jpg` … `ADV_FIG_4-02.jpg`。都在 `https://www.nobelprize.org/uploads/2026/10/` 下。
  - 图 1（Crick 的梦想）只在科普 PDF 里，网页上没有单独的文件。网页上那句「非商业免费使用」说的是列出来的插图，图 1 要用的话先单独确认许可，不行就让 Codex 重画。
  - 带英文字的图，中文片要么只截没有字的部分，要么重画。
- **第一集的画面**：两个开关两盏灯、Bits 墙；数据在 `lucas-academy-video-data/fun-informatics-01/public/`，用法见 FUN-INFORMATICS-01.md §5.4。
- **Codex 插图**（Claude 用 `codex exec` 生成，自己检查、不合格就重做，给 Yancy 看成品）：眼睛「相机坏了、电线还在」、眼镜和琥珀色光点、香农通信图画成眼睛。标「AI 生成·示意」。
- **在家实拍**（可选）：电灯开关一开一关（接第一集）；手电照一碟衣藻或眼虫，看绿色往光那边移。培养液要买，Yancy 定。

## 6. 准确性红线

- 只说「部分恢复」「一位病人」「要戴眼镜」「还在临床试验」，不说「治好了失明」。
- 治眼睛用的是琥珀色光的 ChrimsonR，不是绿藻原来那个蓝光的通道视紫红质，两个不要混。
- 神经细胞「有点像开关」，不说「就是开关」。
- 不画、不描述那位病人「看到的画面」。
- 老鼠只用诺贝尔官网的插图。

## 7. 待定

- [ ] Yancy 改中文稿 v0.1；定稿后再写英文稿。
- [ ] 配音：Louise（约 1.1）和芳芳（1.2 / 1.3）各配一段给 Yancy 听，再定用谁；英文片谁来说也一起定。
- [ ] 英文片名。候选：「The Nobel Prize: What Is Optogenetics? An Informatics View」。英文片谁来说（SCRIPT-AND-VOICE.md 第 6 节）。
- [ ] 封面：标题长，按封面标准把「光遗传学是什么？」做成大问句，「诺贝尔奖」「从信息学的角度看」做小字；右上角系列角标「趣味信息学 4」。
- [ ] 配乐（Public Domain / CC0 / CC BY）。
- [x] 要不要买衣藻实拍：先不买，用 Muse 生成（11-01）。
- [ ] Yancy 用 Muse 生成 G1–G7，放进 `public/fun-informatics-04/muse/`。
- [ ] issue #28 的标题还写着「趣味信息学4」，要改成 5（Yancy 11-01 同意 Shibboleth 放到下一期）。
- [ ] 补「全或无」的出处；对一遍 Sahel 2021 原文的作者和细节。

## 8. 制作（2026-11-01 起，Yancy：「做视频吧」）

稿子按 zh-draft v0.1.2 配，哪句要改再按编号重配。中文片先做，英文稿等中文定稿再写。

**画面**

- Muse 视频（Yancy 生成，原件在桌面，复制进 `public/fun-informatics-04/muse/G1-1.mp4` … `G7-1.mp4`）：
  G2（绿藻向光）效果最好，开头 og00-03 和结尾 og06-07 都用它；G3 眼镜、G4 光点、G5 摸笔记本可用；G6 相机只用前 5.5 秒（后面能看见卡口上的字）。
  G1 两秒后水面晃得厉害，开头改用 Codex 首帧 dish-green 的静帧；G7 只有一根鞭毛，不准确，不用，换成 Codex 的衣藻静帧 + Commons 的真实显微镜画面。
- 素材清单和署名：[docs/fun-informatics-04/footage-sources.json](docs/fun-informatics-04/footage-sources.json)（22 段 Pexels、4 段 Commons、9 张诺贝尔插图）；
  `scripts/fun-informatics-04/fetch_sources.py` 下载，`assets.py` 整理成 `public/fun-informatics-04/clips/`（统一 1920×1080 无声 H.264；Commons 的小录像保持原比例，片里放在圆形「显微镜视窗」里）。
  Pexels 的单个视频页会弹人机验证，下载链接是从搜索页的数据里取的。
- 第一期的画面直接从第一期中文成片里剪（画面上没有字幕）：电灯开关、墙上数数、两个开关两盏灯、「同一串 0 和 1，五种意思」。
- 诺贝尔插图上的英文标注换成中文：`nobel_zh.py`，用标注周围的底色盖掉英文，原位写中文（冬青黑体），其他不动。
- 示意图在 Remotion 里画（`src/videos/fun-informatics-04/FunInformatics04Video.tsx`）：神经信号和 0/1 灯、发得快慢、半毫秒和十毫秒、光控的门、装上开关的细胞、光照亮一片、
  一个比特到一串比特、眼睛（按信号走的顺序画：光 → 光开关 → 接力的细胞 → 视神经 → 大脑，不是解剖图）、编码 → 解码链。
- 每个镜头右下角标出画面来源：实拍 · Pexels · 作者；真实实验录像 · 作者 · Wikimedia Commons · 许可；图 · 诺贝尔生理学或医学奖委员会，Mattias Karlén 绘；画面 · 趣味信息学 1；AI 生成 · 示意。

**时间线和声音**

- 镜头表 `scripts/fun-informatics-04/edit.json`（按台词编号对时），`build_timeline.py` 出 `public/fun-informatics-04/timeline.json`、旁白、混音和字幕；
  没配音时 `--draft` 按每秒 4 个字估时长，先看画面。
- 配乐：莫扎特《小星星变奏曲》K. 265（Simone Renzi，CC BY 3.0），和第三期同一份录音，每段用不同的变奏，OG06 用慢板变奏，片尾回到主题；人声进来就避让（music_ducking.py）。
- 配音：试音 `voice_test.py`（OG00 + OG01 共 16 句，Louise 1.1、芳芳 1.2、芳芳 1.3），Yancy 选定后 `narrate.py --voice … --speed …` 配全片。演绎稿 [voice-direction.md](docs/fun-informatics-04/voice-direction.md)。
- 渲染：`render.py`（四段渲染再拼，`--draft` 半尺寸）；`frames.cjs` 每个镜头出一帧做截图表。

**配音记录（2026-11-01）**

- Yancy 选了 Louise 1.1（`louise/zh`，zero-shot-instruct，全片一个速度）。英文片单独做一部（Yancy：文字比较多）。
- 开场换成方案 B，Yancy 改过（[hooks.md](docs/fun-informatics-04/hooks.md)，zh-draft v0.2）。Claude 为了事实准改了三处措辞，记在 zh-draft 的版本说明里。
- 66 句，取 `lucas-academy-media/outputs/louise/zh/fun-informatics-04-v1/s1.10/`；OG01 直接用试音那 8 条（同样的字、同样的指令和速度）。
- Whisper（small，低分再用 medium）核对后重配 11 句，换下来的在同目录 `alternates/`：
  og00-07（开头多出「猜」，「一碟」听成「一点」）、og00-08（多了一声「嗯」）、og00-09（「束」）、og02-01（「碟」两次都听偏，读法改用同音的「叠」）、
  og02-06（人名中间加停顿）、og02-12（「只有」读成 zhī）、og04-02（「棒」「送」）、og04-06（句尾多出一串含糊的声音，重配后还在，剪在 5.6 秒，后面是 0.35 秒的静音）、
  og06-01（停顿落在「多」后面）、og06-02（「第一章」后多出一个字）、og06-05（「接受」去掉重音）。
- Whisper 听成同音字的没改：绿藻 → 绿枣，眼点 → 岩点（三声变调，读得对），视杆 → 视感，解码 → 结码（变调）等。
- 时间线 9 分 18 秒，混音 −16.2 LUFS，峰值 −1.5 dBFS。
- Yancy 11-01：「短视频尽量拉长使用，文案允许的话」：开场眼镜放到 og00-04 的四分之三再接斑马线；相机先用 Codex 静帧（和视频第一帧一样）再接整段视频，不加速不跳；
  后面眼镜放到 og05-05 的八成，光点一直放到 og05-06 结束（叠「编码：画面 → 光点」），编码 → 解码图移到 og05-07。

**中文片交付（2026-11-01）**

- Yancy：「没问题，出成片」「中文版先放到桌面」。全尺寸渲染（`render.py`），1920×1080、30 fps、9:19，零黑帧，−16.2 LUFS，真峰值 −1.5 dBTP，LRA 2.9（`out/fun-informatics-04/delivery-check.zh.json`）。
- 桌面「诺贝尔奖光遗传学是什么-上传」：`fun-informatics-04.zh.mp4`、`youtube-cover.zh.jpg`、`fun-informatics-04.zh.zh-Hans.srt`、`fun-informatics-04.zh.en.srt`、`youtube-description.zh.txt`（移进去的，逐个核对过 sha256）。
- 封面 `cover.py`：「大脑里，也有开关吗？」（「开关」琥珀色）配诺贝尔的开关和大脑插图；小标题「2026年 诺贝尔奖 / 光遗传学，从信息学的角度看」；不加系列斜条（Yancy 11-01：「趣味信息学封面不要那个斜条」）；另一版「光遗传学是什么？」配 G2 最后一帧，绿水在暗处看不清，没用（留在 `out/fun-informatics-04/cover/`）。
- 英文字幕 `captions.py`：翻译中文片自己的台词（`docs/fun-informatics-04/translations.json`），每行不超过 42 个字母；经文用 WEB，约翰福音 1:5 按和合本「黑暗却不接受光」直译。
- 上传说明 `youtube.py`：章节取自时间线，署名只列片中真用到的素材。
- 还没做：英文片（单独写稿、单独配音）。Yancy 的 7 段 Muse 原件还在桌面上，项目里有一份（`public/fun-informatics-04/muse/`，不提交）。

**英文片（2026-11-01 开始）**

- Yancy：「封面改一下小标题：2026年 诺贝尔奖 / 光遗传学，从信息学的角度看（去掉生理或医学奖）」，已换（桌面上的封面也换了）；「开始做英文吧」。
- 英文稿 [en-draft.md](docs/fun-informatics-04/en-draft.md)：和中文片同样的 66 个编号，一句对一句，所以两部片子共用一份镜头表。经文用 WEB；约翰福音 1:5 用 KJV「the darkness comprehended it not」，WEB 的「hasn't overcome it」接不上「接收」。
- 英文演绎稿 [voice-direction.en.md](docs/fun-informatics-04/voice-direction.en.md)：`louise/en`，1.1，三种英文语气（base / curious / gentle），数字和难念的名字写成读法（Deisseroth → Dice-er-roth）。`narrate.py --lang en`。
- 画面：`edit.json` 每个带字的镜头加了 `…En`；`build_timeline.py --lang en` 换上英文字、诺贝尔插图的英文原版、第一期英文片的画面（`fi1en-*`）；合成里画的字都在 `WORDS` 表里，`FunInformatics04En`。
- 英文封面「Does the Brain Have Switches?」，英文上传说明 `youtube.py --lang en`，英文片的中文字幕 `captions.py --lang en`（用中文稿的句子，和英文一句对一句）。
- 文件名：时间线改成 `timeline.<lang>.json`，渲染输出在 `out/fun-informatics-04/<lang>/`。
- 「一个比特」示意图（og03-01）里，单个开关淡出和一排开关出现之间原来空了约 0.7 秒；已修（英文片用修好的版本）。中文片在 5:07 左右也有这一下，Yancy 11-01：「不用，保持原样」，中文片不重新渲染。

**英文片交付（2026-11-01）**

- 桌面「诺贝尔奖光遗传学是什么-英文版-上传」：`fun-informatics-04.en.mp4`（1920×1080、30 fps、9:08，零黑帧，−16.2 LUFS，真峰值 −0.9 dBTP，LRA 2.9）、`youtube-cover.en.jpg`、
  `fun-informatics-04.en.en.srt`、`fun-informatics-04.en.zh-Hans.srt`、`youtube-description.en.txt`（移进去的，逐个核对过 sha256；`out/fun-informatics-04/delivery-check.en.json`）。
- 工作数据：不能再生的输入（7 段 Muse 视频、6 张 Codex 首帧，38 MB）备份在 `lucas-academy-video-data/fun-informatics-04/`，带 `SHA256SUMS`、`README.md` 和 `restore.sh`。
  restore.sh 2026-11-01 测试过：恢复到一个空目录后，65 个文件（下载的素材、诺贝尔插图和中文标注版、Muse、首帧）和现在的逐字节一样，41 段整理好的视频时长一样。
  配音在 lucas-academy-media `outputs/louise/{zh,en}/fun-informatics-04-v1/`。桌面上的 Muse 原件 Yancy 已经清掉了。
