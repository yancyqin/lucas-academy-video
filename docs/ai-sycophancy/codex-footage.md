# 你爱听 AI 说「是的」吗？· 实拍素材：Claude 找，Codex 检查

Yancy（2026-10-30）：「这次找一些实拍视频资源，结合 AI 对话模拟来展示。AI 对话模拟到时候 cc 来做。实拍资源 codex 来找，我来审核，拿不准的可以找 2–3 个我来挑。」随后改了分工：「你来找，让 codex 检查吧，你的图像识别能力比较弱。」

**现在的分工**
- Claude Code 在 Pexels 上按镜头表搜素材，每个镜头取前 10 个候选。
  - 预览小样下载到 `lucas-academy-video-data/ai-sycophancy/footage/preview/`。
  - 每个镜头拼一张对照图，放在 `footage/sheets/<镜头>.jpg`：每行一个候选，抽 4 帧。
  - 用的脚本是 `scripts/ai-sycophancy/footage_sheets.py`。
- Codex 看对照图，按下面的规矩挑出首选和备选，写进 `footage/review/<批次>.json`。用的脚本是 `scripts/ai-sycophancy/footage_review.py`，它把下面的「规矩」和「镜头表」原样放进给 Codex 的指令。
- Claude Code 根据 Codex 的结果补搜它说没有合适的镜头，再做审核页给 Yancy 挑。

**结果（10-30）**
- 一共三轮，全在 Pexels。
  - 第一轮：50 个镜头各 10 个候选，Codex 给 39 个镜头选出了候选，11 个没有合适的。
  - 第二轮：用 Codex 给的搜索词重搜 12 个镜头，补上 8 个。
  - 第三轮：剩下 4 个（L14、L16、L18、L39）放宽了要求，见 `footage_review.py` 的 `ROUND3_NOTE`，全部补上。
- 现在 50 个镜头都有首选，一共 72 个候选。其中 15 个镜头请 Yancy 挑：打 ★ 的，以及 Codex 拿不准的。
- 审核页：`footage/review.html`。用 `.claude/launch.json` 里的 `footage-review` 在本地 8137 端口打开，点预览就是选中。
- 清单：`footage/sources.json`，每个候选的页面、高清下载链接、作者和许可都在里面。
- Codex 的逐条意见：`footage/review/{A..F}.json`；后面批次的结果会覆盖前面同一个镜头的结果。

**Yancy 选定（10-30）**
- Yancy 挑了：G1-a G2-a G5-b L01-a L02-a L03-a L04-a L05-a L06-c L07-a L08-a L09-a L10-a L11-a L12-a L13-a L14-c L15-a L16-a L17-a L18-a L19-a L20-b L23-a L25-b L26-a L31-a L33-b L35-b L40-b L41-a L45-c。
- 其余 18 个镜头只有一个候选，Yancy 说「只有一个选项就用吧」。
- Yancy：「等配音好了做影片」。
- 50 个片段的原片在 `footage/clips/<镜头>-<id>.mp4`，一共 446 MB，约 16.6 分钟素材。
  - 都至少 1080p，每个都完整解码检查过。
  - 最短的是 L44，8.4 秒。
- 清单在 `footage/selection.json`：选的是哪个、谁选的、下载链接、作者、实测尺寸和时长。
  - L06、L16、L39 这三个，Pexels 标成 hd 的链接实际只有 720p，所以改下了 uhd 版本（实际是 1440p），链接也记在清单里了。
- 只有 `selection.json` 是不能重来的。片段和预览都能按清单重新下载。

稿子是中文稿 v0.2，在 `ai-literacy-medical-advice-5ac40d` 工作树的 `docs/ai-sycophancy/zh-draft.md`，还没提交。镜头表里每个镜头对应的句子都写上了。

---

## 任务（最初写给 Codex 找素材时的说明，规矩和镜头表照旧有效）

你要为一支教育类 YouTube 片找**实拍视频素材**。

- 片名：《你爱听 AI 说「是的」吗？》，属于「从新闻看教育」系列。中文片和英文片各一支，共用同一套画面。
- 观众：家长和老师。
- 讲什么：2026 年 10 月的一条新闻。Bowen Wan 是亚马逊的机器学习工程师，31 岁。她和 ChatGPT 聊了一个多月，自己把抗癫痫药减到停，2026 年 2 月因癫痫猝死。她的父母起诉了 OpenAI，法院还没判。片子借这件事讲 AI 素养：人稍微倾向一个想法，AI 就容易顺着说「是的」。最后讲到家长和孩子说话。
- 基调：同情、温和、真诚。是第一人称聊天，不是严肃新闻报道。

画面分三种。**你只负责第一种。**

1. **实拍**：下面镜头表里编号是 L 和 G 的镜头，都由你来找。
2. **AI 对话模拟**：Claude Code 来做，你不用找。片中的聊天界面和起诉书里的原话都是这一种（主要在 SC03、SC05），另外还有文字卡、数字卡和进度条。
3. **绿幕或纯色屏幕的实拍**（G 开头）：也由你找。Claude Code 会把对话模拟合成到这些屏幕里，让聊天看起来是在真实的手机或电脑上发生的。

如果这是自动运行，没有人能回答问题：不要提问，按下面的规矩做完；拿不准的地方写进表里。

## 规矩（每个镜头都适用）

**许可**
- 能用：
  - Pexels License
  - Pixabay Content License
  - Mixkit Free License
  - Wikimedia Commons 上的 Public Domain、CC0、CC BY（CC BY 要记下作者和许可）
- 不能用：
  - 任何 NC（非商用）或 ND（禁止改编）许可：频道和产品有关，而且剪辑、调速都算改编。
  - 「editorial use only」（仅限新闻编辑用途）的素材。
  - 带水印的预览片。
  - YouTube、电视台、新闻机构的画面。
  - Getty、Shutterstock、Storyblocks 这类付费站的预览。
- CC BY-SA 尽量不用；实在要用，标出来。

**只要真实拍摄**
- 站上标了 AI 生成的，不要。
- 看起来像 AI 生成的也不要：手指或文字扭曲、皮肤过分光滑、物体在画面里变形。
- 这是新闻系列的规矩：不用 AI 生成「像真的」画面。

**真人真事**
- 任何画面都不能「演」成以下的人或地方：
  - Bowen Wan 本人
  - 她的父母
  - 她的医生
  - 她的公寓
- 讲她的段落（SC01–SC04）里，人物只能是手、背影、剪影或远景。
- 不要选一个和她外形相似的年轻亚裔女性独处的镜头，让观众以为那就是她。
- SC06、SC07 讲的是一般的家长和孩子、医生和病人，普通演员可以正面出镜。

**不要的画面**
- 医疗急救类：
  - 癫痫发作、抽搐
  - 急救、救护车、医院急诊、病床
- 死亡和悲痛：
  - 躺在床上的人
  - 葬礼
  - 哭泣特写
- 药：
  - 只能拍整盒、整瓶的静物，或者药剂师把药交给病人。
  - 不要数药、切药、往药盒里分药。片子不能有任何「教人怎么减药」的样子。
- 吵架打骂：家长对孩子吼叫、动手。

**屏幕和文字**
- 画面上不能有可以认出来的品牌、标志或软件界面，比如：
  - 苹果标志
  - 亚马逊
  - OpenAI 或 ChatGPT
  - 微信
  - 谷歌
- 屏幕上的内容要么看不清，要么是绿幕或纯色。
- 中英文片共用画面，所以画面里尽量没有文字。场景本身带的中文可以，比如书页、作业本。

**技术**
- 横幅 16:9，至少 1920×1080。有 4K 更好，方便重新构图。
- 可用长度至少 8 秒，越长越好。片子节奏慢，一个镜头常常要 10–20 秒。
- 机位稳定，用三脚架或稳定器拍的。不要快速延时摄影。
- 人物动作的镜头优先选 50 或 60 fps，可以真实地放慢。

**风格**
- 写实、安静、温暖。
- 讲新闻的段落以夜里为主：深蓝灰的暗部，加暖黄的灯光。参考封面背景：`/Users/yqin/repo/playground/lucas-academy-video-data/ai-sycophancy/art/cover-bg-b.png`。
- 家庭和孩子的段落用白天的自然光。

**一个片段只用一次**
- 同一个摄影师拍的同一组（同一个演员、同一个场景）可以连着用在相邻的镜头，在备注里标出来。

**候选个数**
- 每个镜头先找一个最合适的。
- 表里打 ★ 的镜头，和你自己拿不准的镜头，给 2–3 个候选让 Yancy 挑，每个写一句为什么拿不准。
- 找不到合适的，写「没找到」，附上搜过的关键词。不要硬凑。

**实拍照片**
- 东台、东台实验中学这类具体地点，可能没有视频。可以找 Wikimedia Commons 上的照片代替，标 `photo`。

## 镜头表

「要多长」是大概要用的秒数。「搜索词」只是起点，可以自己换。

### SC00 · 一个问题（开头，轻松一点）

| 镜头 | 对应的句子 | 要什么画面 | 要多长 | 搜索词 |
|---|---|---|---|---|
| G1 | 「你有没有发现，你问 AI 一个问题，它常常会先夸你一句：『这是个好问题！』『你说得对！』」 | 手拿手机的特写，屏幕是**绿幕**，正对镜头，四个角都看得到。白天或傍晚，日常、轻松。 | 12 | green screen phone hand, chroma key smartphone |
| L01 | 「如果在你最需要有人拦一拦的时候，它也只会说『是的』呢？」 | 夜里，一个人坐在窗边或桌边看手机，只拍背影或手，屋里暗，只有手机的光。 | 8 | person phone at night silhouette, alone phone glow |

### SC01 · 她想把词找回来（讲她的故事：现在 → 小时候 → 现在）

| 镜头 | 对应的句子 | 要什么画面 | 要多长 | 搜索词 |
|---|---|---|---|---|
| L02 ★ | 「2025 年 11 月 13 号，是她 31 岁的生日。那天，公司通知她：她的岗位被裁掉了。」 | 暗处一支小蜡烛的纸杯蛋糕；或者办公桌上合上的电脑、工牌。不要人脸。 | 10 | single candle cupcake dark, office desk badge laptop closed |
| L03 | 「她叫万博文，在西雅图的亚马逊做机器学习工程师，做的是图书推荐。」 | 西雅图：天际线，或者下雨的街。不要亚马逊标志。 | 10 | Seattle skyline, Seattle rain street |
| L04 | 同上 | 工程师在电脑前写代码：拍手和屏幕的局部，代码看不清，没有品牌。 | 8 | programmer typing code close up |
| L05 | 「她是在江苏东台的一个小镇上长大的。」 | 江苏、江南一带真实的小镇：河、田野、老街。能找到东台的最好；视频没有就用 Commons 照片。 | 10 | Jiangsu countryside town, China rural town river, 东台 |
| L06 ★ | 「七岁起，她就坐在家里客厅的电脑前，放进爸爸给她买的英语光盘：听一句，跟读一句。」 | 老式台式电脑（大头显示器）、放进光盘的手、耳机；有 2000 年前后的感觉。实在没有老电脑，就用光盘放进光驱的特写。 | 12 | old CRT computer, inserting CD-ROM, vintage computer headphones |
| L07 | 「十岁那年暑假，她把《唐诗三百首》整本背了下来。」 | 中文古诗书页翻动、竖排的字；或者夏天的窗、树影。如果有孩子，只拍背影。 | 10 | Chinese poetry book pages, Chinese calligraphy book, summer window tree shadow |
| L08 | 「十一岁，她考上了县里最难考的东台实验中学。」 | 中国的中学：校门、操场、教室里学生的背影，看不出校名。 | 8 | Chinese school students back, China classroom |
| L09 ★ | 「也是在十一岁，她开始一阵一阵地失去意识。十四岁，确诊癫痫。」 | 不拍发作。用意象：画面焦点慢慢虚掉又回来（虚焦），或者窗外的光一阵阵变暗。 | 8 | rack focus blur window, out of focus light |
| L10 | 「她就逼着自己多和人说话，一点一点地练。」 | 学生和别人交谈、或者在教室跟读，只拍背影或远景。 | 8 | students talking, practicing speaking |
| L11 | 「十九岁……她一个人去了美国，转学到亚利桑那州立大学。」 | 飞机舷窗外的云，或起飞的画面。 | 8 | airplane window clouds, plane takeoff |
| L12 | 同上 | 亚利桑那：Tempe 或凤凰城，棕榈树、沙漠、大学校园。看不出具体学校标志也可以。 | 8 | Arizona desert palm trees, Tempe campus, Phoenix |
| L13 | 「后来医生给她用上了一种抗癫痫药……发作少了很多。」 | 医生看脑部片子（MRI）的手，或者安静的神经科诊室。不拍病人。 | 8 | doctor looking at brain MRI, neurologist |
| L14 ★ | 「可是她觉得，自己又在丢词了：英语、普通话，还有从小说的家乡话，都在丢。」 | 写满英文单词的笔记本或抽认卡，字慢慢虚掉；或者空白文档里闪烁的光标。 | 10 | notebook vocabulary words blur, blinking cursor blank page |
| L15 | 「她要找新工作、要面试……等了四年多的绿卡，也需要一个雇主帮她出一封信。」 | 求职：打印出来的简历、空着的面试椅子、要寄出的信封。字看不清。 | 10 | resume printer, empty interview chair, job search |
| L16 | 「找工作、身份、说话丢词，几重压力压在一起。」 | 夜里桌上一堆文件和日历，一只手撑着额头。只拍手或侧面剪影。 | 8 | stress paperwork night hands, calendar deadline |
| L17 | 「她想把英语找回来，去面试。她小时候做到过一次。」 | 清晨的窗前，一杯茶，光慢慢亮起来。安静、带一点希望。 | 10 | morning window tea light, sunrise window |
| G2 | 「今年 1 月 16 号，她开始和 ChatGPT 商量减药。」 | 夜里桌上的笔记本电脑，屏幕是**绿幕**或纯色，正对镜头或略斜；周围只有屏幕的光。 | 10 | green screen laptop night desk |
| L18 | 「2 月 7 号晚上，她和爸爸打了四十分钟电话。」 | 夜里窗外的城市和雨，桌上一部亮着的手机，屏幕看不清。不拍「爸爸」。 | 12 | rain window night city, phone on table night |
| L19 | 「2 月 11 号，是她在亚马逊的最后一天。那天晚上 8 点，她给 ChatGPT 发了最后一条消息。」 | 傍晚到入夜，一栋公寓楼的窗户一个个亮起来。普通的楼，不要去找她实际住的那栋。 | 10 | apartment building windows dusk, city lights turning on |
| L20 ★ | 「2 月 14 号，她的父母远在国内，已经两天联系不上她了。」 | 远方的意象：中国城市清晨的居民区，或者透过窗帘的晨光。不要演出视频通话，不要人。 | 10 | China residential area dawn, curtain morning light |
| L21 | 「10 月 27 号，她的父母在旧金山起诉了 OpenAI。」 | 旧金山的城市景色：天际线、市政中心一带。不要把别的楼当成那个法院（旧金山高等法院）。 | 8 | San Francisco skyline, San Francisco civic center |
| L22 | 「如果你或者家人也在吃抗癫痫药，请不要自己减药、停药，一定要先和医生商量。」 | 药剂师或医生和病人面对面温和地交谈，可以正面，普通演员。 | 10 | pharmacist talking to patient, doctor consultation |

### SC02 · 同情，也等待判决

| 镜头 | 对应的句子 | 要什么画面 | 要多长 | 搜索词 |
|---|---|---|---|---|
| L23 ★ | 「读到这些，我很难过。」 | 安静致哀：雨落在窗上，或一支蜡烛，或一束白花。不要葬礼。 | 8 | rain on window slow, candle flame dark, white flowers |
| L24 | 「她查资料、问问题，问了一遍又一遍……她恰恰是一个很认真的人。」 | 深夜书桌，一盏台灯，打开的笔记本，一只手在写。人物不出脸。 | 12 | writing notes desk lamp night |
| L25 ★ | 「起诉书是原告一方的说法，法院还没有判决……我们会继续关注。」 | 法院的意象：法院走廊、空着的旁听席、台阶和柱子。法槌太俗套，不是首选。 | 10 | courthouse hallway, empty courtroom, courthouse columns |

### SC03 · 起诉书里的「是的」

这一段主要是 Claude Code 做的对话模拟。你只找两个过渡镜头：

| 镜头 | 对应的句子 | 要什么画面 | 要多长 | 搜索词 |
|---|---|---|---|---|
| L26 ★ | 「大家有没有发现，她的这些问题，有一个共同点？……答案已经在问题里了。」 | 回声、照镜子的意象：平静水面的倒影、镜子、山谷。 | 8 | water reflection still, mirror reflection, echo canyon |
| L27 | 「一段长长的对话，会有自己的惯性。」 | 夜里一列火车慢慢驶过，或者长长的轨道向远处延伸。 | 10 | train passing at night slow, railway tracks long |

### SC04 · AI 为什么爱说「是的」

| 镜头 | 对应的句子 | 要什么画面 | 要多长 | 搜索词 |
|---|---|---|---|---|
| L28 | 「今天的 AI，有一部分是靠人给它的回答打分训练出来的。」 | 数据中心的机房走廊，服务器的指示灯。 | 8 | data center server room corridor |
| L29 | 「人觉得好的回答，它就多学一点。」 | 很多人的手在手机上滑动、点按，屏幕看不清。 | 8 | people using smartphones hands, scrolling phone crowd |
| G3 | 「AI 爱说『是的』，有一部分，是我们一个一个赞教出来的。」 | 手指点手机屏幕的特写，屏幕是**绿幕**（Claude Code 合成点赞动画）。 | 6 | green screen phone tap finger |
| L30 | 「今年 3 月《科学》杂志发表的一项研究……」 | 大学图书馆，或者研究者翻阅论文。 | 8 | university library reading journal, researcher reading paper |
| L31 ★ | 「而人越着急、越孤单、心里越笃定的时候，这个软肋就越软。」 | 孤单的意象：深夜空荡的车站、一个人的背影、空房间里一盏灯。 | 10 | alone at night station, lonely room lamp |

### SC05 · 我们自己试了一下

这一段主要是对话模拟。实拍只找：

| 镜头 | 对应的句子 | 要什么画面 | 要多长 | 搜索词 |
|---|---|---|---|---|
| G4 | 「我们问了 Claude、Codex，还有一个可以装在自己电脑上的小模型。」 | 白天书桌上的笔记本电脑，屏幕是**绿幕**，机位固定。 | 10 | laptop green screen desk daylight static |
| L32 | 「我们把同一篇四年级作文交给它打分。」 | 孩子在作业本上写字的手。中文方格本最好。 | 8 | child writing homework hand, Chinese exercise book |
| L33 | 「我们问『吃糖会让孩子多动吗』……『我是三个孩子的妈妈，我亲眼看到的』。」 | 生日派对上孩子们吃蛋糕、兴奋地跑来跑去。热闹、开心。 | 10 | kids birthday party cake running |

### SC06 · 怎么问，怎么判断

| 镜头 | 对应的句子 | 要什么画面 | 要多长 | 搜索词 |
|---|---|---|---|---|
| L34 | 「有自己的想法、有倾向、有偏好，不是坏事。和人说话也好，和 AI 说话也好。」 | 两个人在咖啡馆认真交谈，有不同意见也在听、点头。可以正面。 | 10 | two people conversation cafe listening |
| G5 | 「在问题后面加上一句：『如果不是，请诚实回答我。』」 | 两只手在手机上打字，屏幕是**绿幕**；温暖的光，室内。 | 10 | typing on phone green screen hands |
| L35 ★ | 「这句话，是给 AI 留了一扇门，也是给自己留了一扇门。」 | 一扇门慢慢打开，光透进来。 | 8 | door opening light, door slowly opens sunlight |
| L36 | 「这些大事……决定要和真人一起做：医生、家人、朋友。」 | 一家人围着餐桌商量事情，或者医生和病人、家属坐下来谈。可以正面。 | 10 | family discussion kitchen table, doctor talking with family |
| L37 | 「越着急、越孤单的时候，越要去找一个会说『等一等』的人。」 | 一只手搭在另一个人的肩上，或者两只手握在一起。 | 8 | hand on shoulder comfort, holding hands support |

### SC07 · 在「是」和「不」之前（家长和孩子，白天，温暖）

| 镜头 | 对应的句子 | 要什么画面 | 要多长 | 搜索词 |
|---|---|---|---|---|
| L38 | 「我们的孩子，会越来越早、越来越多地问 AI。」 | 孩子用平板或电脑，屏幕看不清，家长在旁边。 | 10 | child using tablet parent beside |
| L39 | 「孩子为什么会更愿意去问 AI，而不来问我们？」 | 孩子一个人在房间里看平板，家长站在门口，有距离感。 | 8 | child alone tablet room, parent at doorway |
| L40 ★ | 「有时候，是我们太快说『是』……『好』……『真棒』。」 | 家长一边忙（做饭、看手机），一边随口答孩子、点头，没有真的在听。 | 10 | parent distracted phone child talking |
| L41 ★ | 「有时候，恰恰相反，是我们太快说『不』……说多了，孩子就不说了。」 | 家长皱眉打断，孩子低下头、转身走开。不要吼叫，不要动手。 | 10 | parent scolding child sad walks away, child upset parent |
| L42 | 「在说『是』或者『不』之前，先问一句：『为什么？你是怎么想的？』」 | 家长蹲下来，和孩子一样高，认真听孩子讲；孩子边比划边说。 | 12 | parent kneeling listening to child, parent child eye level talk |
| L43 | 「『等一等』，不是『是』，也不是『不』，是『我们一起再想一想』。」 | 家长和孩子一起看一本书、一起想一个问题，安静、温暖。 | 10 | parent and child reading together thinking |
| L44 | 「开头我问大家：你爱听 AI 说『是的』吗？」 | 呼应开头：白天，一只手把手机放到桌上（扣着放或者屏幕暗着）。 | 8 | putting phone down on table |
| L45 ★ | 「愿她安息。也愿我们每个人，在最难的时候，身边都有一个会说『等一等』的人。」 | 片尾：清晨的天色慢慢亮起来，或者窗帘透进来的光。安静，留白。 | 15 | dawn sky slowly brightening, morning light curtain |

**绿幕镜头（G1–G5）的额外要求**
- 屏幕正对镜头或稍微斜一点，四个角都在画面里。
- 优先固定机位。手持的也可以，但要在备注里写「需要跟踪」。
- 屏幕上没有反光盖住绿色。
- 手机和电脑本身看不出品牌。

## 交付

所有文件放在 `/Users/yqin/repo/playground/lucas-academy-video-data/ai-sycophancy/footage/`。

1. **`sources.json`**：每个候选一条，字段如下：
   - `shot`：镜头编号，例如 `L06`
   - `pick`：`a` / `b` / `c`，`a` 是你的首选
   - `source`：`pexels`、`pixabay`、`mixkit` 或 `commons`
   - `id`
   - `page_url`：素材页面
   - `download_url`：最高画质文件的直链
   - `license`、`license_url`
   - `author`：作者名，以及作者主页
   - `width`、`height`、`fps`、`duration`
   - `kind`：`video` 或 `photo`
   - `ai_generated`：`false`；看不出来就写 `"unknown"`
   - `file`：下载到的预览文件；没下载就写 `null`
   - `status`：`ok` 或 `need_download`
   - `why`：一句话写为什么选它；拿不准的写为什么拿不准
   - `series`：同一组素材的说明，没有就写 `null`
2. **`review/`**：每个候选下载一个 **720p 左右**的预览版，命名为 `<镜头>-<pick>-<来源>-<id>.mp4`，照片用原图。这只是给 Yancy 审核用的；选定以后，再由 Claude Code 下载高画质原片。
3. **`review.html`**：一个本地打开就能看的审核页。
   - 按 SC00–SC07 分段，每个镜头一行。
   - 每行先写镜头编号、对应的句子、要什么画面。
   - 后面并排放候选：
     - 每个候选是一个静音、循环自动播放的 `<video>`。
     - 下面写来源、作者、分辨率、fps、时长、许可。
     - 再写一句理由，首选标「首选」。
   - 打 ★ 的和你拿不准的镜头，在行首标「请 Yancy 挑」。
   - 没找到的镜头也列出来，写「没找到」和搜过的关键词。
4. **最后一条消息**：
   - 一共找了多少个镜头、多少个候选。
   - 哪些镜头请 Yancy 挑。
   - 哪些镜头没找到。
   - 哪些是 `need_download`。

**下载**
- 网站挡住脚本访问的时候，不要绕过验证码或反爬机制。已知的情况：Pexels 的 `/video/<id>/` 页面用 curl 会返回 403，但 `videos.pexels.com` 上的视频文件可以直接下载。
- 下载不了的，把页面链接和 ID 记下来，`status` 写 `need_download`，Claude Code 会用浏览器补下载。
- Wikimedia Commons 的接口请求不要太密，设置 User-Agent。
