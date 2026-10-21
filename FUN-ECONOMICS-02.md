# 都学了三年，放弃就白学了吗？ / Is Quitting After Three Years a Waste?

教育经济学 2（Education Economics 2）：沉没成本。系列从这一集起改名叫「教育经济学 / Education Economics」（Yancy，2026-10-19；第一集发布时叫「趣味经济学 1」）；文件夹和脚本仍叫 fun-economics-02。作者 Yancy Qin | Lucas Academy。接第一集《一根冰棍，要花多少钱？》结尾的预告「沉没成本 · 下一集」。

一句话主线：**过去的，已经沉下去了；将来，还没有来；能选的，只有现在。** 沉没成本教我们往前看；珍惜当下，就是认真做好现在这个选择。

配音稿：[docs/fun-economics-02/zh-edit.md](docs/fun-economics-02/zh-edit.md)（中文，`>` 行是英文字幕）、[en-edit.md](docs/fun-economics-02/en-edit.md)（英文配音稿，`>` 行是中文）。两份稿 id 一一对应。

## 制作进度（2026-10-19）

已完成：中文片 7:42、英文片 7:37，都过了 quality.py；上传文件夹在桌面「都学了三年放弃就白学了吗-上传」和「…-英文版-上传」（片子、中英字幕、封面、上传描述）。没上传；代码在分支 `claude/fun-economics-02`（2026-10-19 提交，开了 PR）。作者只写 Yancy Qin（10-19）。

## 0. 新会话从这里开始

- 工作目录：worktree `.claude/worktrees/fun-economics-02`，分支 `claude/fun-economics-02`。
- `public/fun-economics-02/` 和 `out/fun-economics-02/` 不提交（.gitignore），里面是图、实拍、配音、时间线和混音。
- 内存上限 25 GB：同时最多一个配音进程（CosyVoice 一个 6–8 GB）；渲染并发 2。
- 不上传；提交和开 PR 等 Yancy 说。

## 1. 已定的事（Yancy，2026-10-16～19）

- **中英文两部片**（2026-10-19 定；10-18 试过一部片两条配音，看过后改回两部）：同一份分镜，画面上不放任何语言的文字标签，只有片头和片尾用这部片自己的语言。每部片按自己的配音定节奏，各带中英两份字幕（自己的话和译文，都按自己的配音定时）。
- 直接讲 Mary 学钢琴三年：从有兴趣到没兴趣，遇到困难想放弃。家长多半不同意，因为花了钱和时间。坚持是好的，但如果理由错了，就是沉没成本谬误。
- **先**讲往前看的更好理由（练耐心和韧劲、Mary 真正喜欢什么、停一停重新想），**再**讲沉没成本谬误。
- 例子讲付出的工夫，不讲钱（美国孩子不太在乎已经花的钱）：乐高为主（拼错了，舍不得拆，总想怎么修），加第一步错了、越算越复杂的数学作业（编的题）。
- 彩蛋：腓立比书 3:7、3:13–14（中文和合本，英文 WEB）。
- 画风：SC00 01 02 07 用第一集的漫画风格（生成图）；SC04 05 06 09 写实（Pexels 实拍 + 生成的写实图）；SC08 油画；SC03 用第一集的图解风格（纸面、天平、下沉）。
- 提问的语气好奇、慢慢探索，不批评家长；结尾是一个开放的问题。

标题如上；封面用 cover-piano-a（孩子趴在琴谱上）；观众按家长和教育者优先（Yancy 2026-10-19：「看起来不错，就这样吧」）。

## 2. 结构和分镜

时间线由 `build_timeline.py --lang zh|en` 生成（第一集的做法，每种语言一条，中文约 7:42、英文约 7:37）。画面事件（写字、砝码落下、换镜头）挂在词上（`ANCHORS`），用 Whisper 听出来的词的时间（`check.py` 写进 `word-times.json`）。

| 段 | 内容 | 画面 |
| --- | --- | --- |
| SC00 学了三年，不想学了 | 第一首曲子的开心 → 练琴像任务 → 「我不想学钢琴了」→ 问家长 | 漫画 first-piece / practice-chore / dont-want / parents-think；问题后出片头 |
| SC01 「都学了三年了」 | 家长的第一反应；坚持要看因为什么 | 漫画 three-years / stick-with-it |
| SC02 往前看，有更好的理由 | 耐心和韧劲；喜欢什么（弹、听、写）；停一停 | 三个空框 + 往前的箭头 → 漫画 grit / music-loves / pause → 三框填满，身后是虚线的「已付」 |
| SC03 沉没成本 | 拿不回来的 = 沉没成本，像沉到水底的船；天平两边一样重；谬误 | 图解：砝码（金币 + 沙漏）+ 问号 → 船载着砝码沉底 → 天平（grit / pause 两条路各放一份）不动 → 砝码变成虚线 |
| SC04 拼错的乐高 | 拼到一半发现放错；舍不得拆，越修越难；哪条路最快；积木一块没少 | 实拍 7230999 → 生成 lego-wrong-brick（圈出放错的那块）→ 实拍 6666287 → lego-patched → 实拍 6663997 → 实拍 7313178 → lego-rebuilt |
| SC05 第一步错了的作业 | 8 支一盒、7 盒、14 人；7 + 8 = 15；越算越怪；回到第一步 7 × 8 = 56，56 ÷ 14 = 4；数学有时要算很久；没有白算 | 实拍 6996523 → 本子（notebook-page 上用铅笔字和图写题、错的算式、切成 14 段的铅笔、越来越乱的小数）→ 实拍 853819（擦）→ 本子（对的算式，圈出 4）→ 实拍 7015925 / 3981943 / 5182684 |
| SC06 为什么舍不得 | 宜家效应；被拆掉的乐高；大人更容易犯；「不能浪费」管的是还没花的 | 实拍 7117367 → 7311978 → 生成 robot-apart → 实拍 8799077 → 图解沙漏（上面是还没花的，亮；下面已经沉了，虚线） |
| SC07 回到钢琴 | 学会的没沉；今天的心情不等于前面的路；接下来怎么走；主线 | 漫画 skills-stay / tired-day / road-ahead → 图解：左边沉在水里的砝码、右边伸向雾里的虚线路、中间发光的「现在」（Mary） |
| SC08 彩蛋：保罗 | 保罗身后的「已经付出」；3:7；3:13–14；忘记背后不是过去不重要 | 油画慢推：伦勃朗《使徒保罗》、瓦伦丁《圣保罗写书信》、伦勃朗《狱中的圣保罗》、《扮作使徒保罗的自画像》 |
| SC09 结尾的问题 | 让你留下来的，是前面的路，还是身后已经走过的路？ | 实拍 6296878 → 7123932 → 航拍乡间路 38413453（50 fps，半速） → 片尾（双语） |

## 3. 素材（都在 `public/fun-economics-02/`，不提交）

- `images/`：Codex 生成。漫画 12 张（Mary 黄 T 恤黑短发、妈妈紫衣、爸爸；无文字）；写实 5 张（lego-wrong-brick / lego-patched / lego-rebuilt / notebook-page / robot-apart，无品牌、无文字、孩子只露手）；封面 cover-piano-a（选用，复制为 cover.png）和 cover-piano-b（备选：家长的手搭在肩上）。
- `footage/`：Pexels 实拍 21 段，`<段>-<id>.mp4`，来源和作者在 `footage/sources.json`；片中用 15 段（没用：sc04-7101127、sc04-7313304、sc05-3981946（孩子太小）、sc06-7312137、sc06-7981964、sc09-6672011（只有 720p））。
- `art/`：四幅保罗油画，来源见 `art/SOURCES.txt`。
- `music/`：《G 大调小步舞曲》（SC00–02）→ Joplin《Solace》（SC03–07）→ Satie《Gymnopédie No. 1》（SC08–09），同第一集；来源见 `music/SOURCES.txt`。音乐在每句话下面压低、在每个空隙里升起（`scripts/music_ducking.py`）。
- `fonts/`：马善政楷书（中文）、Andika（英文和数字；本子上的铅笔字也用它）。

## 4. 流程

```bash
python3 scripts/fun-economics-02/narration.py                 # 配音稿 → narration/cues.{zh,en}.json
NARRATE_THREADS=8 ../lucas-academy-media/.conda/bin/python scripts/fun-economics-02/narrate.py zh   # 还有 mary-zh、en、mary-en，一次一个
../lucas-academy-media/.conda/bin/python scripts/fun-economics-02/check.py           # Whisper 核对中文，记下画面挂的词的时间
../lucas-academy-media/.conda/bin/python scripts/fun-economics-02/check.py --lang en
python3 scripts/fun-economics-02/build_timeline.py --lang zh # 时间线、混音、中英两份字幕（再跑一次 --lang en）
node scripts/fun-economics-02/frames.cjs --comp=FunEconomics02Zh   # 每句一帧的检查图
python3 scripts/fun-economics-02/render.py zh                 # 分 4 段渲染（并发 2），配上混音（再跑 en）
python3 scripts/fun-economics-02/quality.py --lang zh         # 时长、编码、黑帧、响度、字幕
python3 scripts/fun-economics-02/package.py --lang zh         # 搬到桌面「都学了三年放弃就白学了吗-上传」（en：「…-英文版-上传」）
```

- 配音：旁白 louise/zh、louise/en（zero-shot-instruct 1.0，好奇、慢慢探索）；Mary 用 eunice/en（instruct，1.05，提示 D：好奇、俏皮的七岁女孩）。重录要改字或标点（同样的文字出同样的声音）。
- 核对：`check.py`（Whisper small）之外，每份转写都要读意思：Louise 的英文把 can't 读得像 can、won't 像 will、road 像 rows，所以英文稿用 cannot、will not、path。拿不准的词用 Whisper medium 和强制解码（episode 3 的 `force.py`）比读法；`retake.py` 一次配几种标点写法，按转写和强制解码的差距挑一条，`--install` 换进去，再把念法写进 `narration.py` 的 `RETAKE`（字幕不变）。
- 已重录（2026-10-18）：中文 sc05-01（也、Mary）、sc04-04（积木）、sc06-01（拼好）；英文见 `out/fun-economics-02/retakes.json`。
- 重新渲染时：`package.py` 把字幕也搬走了，先跑 `build_timeline.py --lang zh --srt-only`（和 en）再跑 `quality.py`。
- 交付：每种语言 `out/fun-economics-02/delivery/fun-economics-02.<lang>.mp4`、`fun-economics-02.<lang>.{zh-Hans,en}.srt`、封面（中文片用中文在前的封面，英文片用英文在前的）。

## 5. 事实和出处

- 沉没成本：已经发生、不管接下来怎么选都收不回的成本，不应影响决策。经典实验 Arkes & Blumer (1985) 剧院季票；Thaler (1980)。
- 宜家效应：Norton, Mochon & Ariely (2012), Journal of Consumer Psychology 22(3)。
- 被拆掉的乐高：Ariely, Kamenica & Prelec (2008), Journal of Economic Behavior & Organization 67(3–4)；当面被拆的那组，拼得少很多（平均 7.2 个对 10.6 个）。
- 大人比小孩更容易犯：Arkes & Ayton (1999), Psychological Bulletin 125(5)：大人把「不能浪费」用过了头。（文中关于动物不犯这个错的说法后来有争议，片中不用。）
- 经文：腓立比书 3:7、3:13–14。中文和合本；英文 World English Bible（公有领域，ebible.org 核对过）。
- 作业题：7 × 8 = 56，56 ÷ 14 = 4；错的那条路里的每一步算术本身是对的（1 ÷ 14 ≈ 0.0714，0.0714 × 7 = 0.4998，15.07 ÷ 8 ≈ 1.88，1.88 × 14 = 26.32），只是越走越远。
