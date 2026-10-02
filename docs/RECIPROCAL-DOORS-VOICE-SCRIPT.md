# 语言的桥 · 配音演绎稿（中英）

这是**怎么读**的稿子；字幕永远用 issue 里确认的原文，这里的改动不会动字幕。
改完告诉我，我运行 `apply-md` 同步，只重新生成改过的句子。

- `<strong>词</strong>`：强调。已确认会作为特殊标记送进模型；效果偏细微，所以只放在真正的对比词、关键词上。
- 只能加标点、不能改字：`……` 停一下、`！` 提气、`？` 上扬、加 `，` 断句。脚本会逐句核对读的字和字幕一致。
- `语气`：`默认`＝本人原来的朗读语调；`亮`＝更有起伏、更有精神的高点句（中文用混合做法，保留本人语调，声纹相似度 0.70–0.83；英文实测混合做法反而更平，所以英文的“亮”只靠 `!`、`...` 和重音）；`开心`／`轻柔`＝instruct 模式，效果更强，但声音不太像本人（相似度约 0.6），不建议使用。
- `语速`：0.82 开场和最重的句子 · 0.85 分量重 · 0.9 基准 · 0.95 轻快。
- `停顿`：这句之前留几秒安静（默认句间 0.45 秒，场景开头 0.7 秒）。
- 每句先写中文，下一行 `en |` 是对应的英文，重音跟中文对齐。
- **两支片子都是全片一种读法**（同梵高那期，2026-10-01 定）：中文 `zero-shot-instruct`「请用活泼、亲切的语气，像给孩子讲故事一样说。」语速 1；英文「Please speak in a lively, warm voice, like telling a story to children.」语速 1。下面每句的 `语气` / `语速` 标注已不再使用（逐句切换会忽快忽慢）；强调和标点照样生效。示范句（我来帮你 / Let me help you）保持慢速、平读。
- 两支独立视频：中文版用中文时间轴，英文版用英文时间轴（停顿设置两版相同）。

## RD01 · 听懂了，读起来却很难

rd01-01 | 想象一个孩子。 ｜语速 0.82 ｜停顿 1
     en | Imagine a child.
rd01-02 | 别人把故事<strong>念给他听</strong>，他<strong>能</strong>说出发生了什么。 ｜语速 0.9 ｜停顿 0.8
     en | When someone <strong>reads a story aloud</strong>, he can tell us what happened.
rd01-03 | 轮到<strong>自己读</strong>，有些字，却让他停下来。 ｜语速 0.85 ｜停顿 0.6
     en | When he reads it <strong>himself</strong>, some words... stop him.
rd01-04 | 我们在学习<strong>阅读障碍</strong>的资料时，注意到这样的情况。 ｜语速 0.9 ｜停顿 0.7
     en | We noticed examples like this while learning about <strong>dyslexia</strong>.
rd01-05 | 有些孩子，<strong>认字、拼写</strong>很困难。 ｜语速 0.9
     en | Some children find <strong>word reading and spelling</strong> difficult.
rd01-06 | 但单看这一点，还<strong>不能</strong>知道这个孩子能<strong>理解</strong>什么、能<strong>做</strong>什么。 ｜语速 0.85 ｜停顿 0.75
     en | That alone does <strong>not</strong> tell us everything they can <strong>understand</strong>, or <strong>do</strong>.

## RD02 · 多开一个入口

rd02-01 | 所以，我们可以看看：这个孩子<strong>需要什么帮助</strong>？ ｜语速 0.9
     en | So we can ask: what <strong>help</strong> does this child need?
rd02-02 | 如果今天是<strong>理解故事</strong>，可以听、看图，再聊一聊。 ｜语速 0.95
     en | If today's goal is to <strong>understand a story</strong>, we can listen, look at pictures, and talk about it.
rd02-03 | 需要<strong>练认字</strong>时，就<strong>认真</strong>练认字，也给合适的帮助。 ｜语速 0.9
     en | When the goal is <strong>word reading</strong>, we practise reading with suitable support.
rd02-04 | 每个孩子的情况<strong>不一样</strong>，我们要先<strong>了解他</strong>。 ｜语速 0.85 ｜停顿 0.65
     en | Each child is <strong>different</strong>. We need to get to know the child <strong>in front of us</strong>.

## RD03 · 我们想到双语课堂

rd03-01 | 这启发我们想到<strong>中英文学习</strong>。 ｜语气 亮 ｜语速 0.9
     en | This led us to think about learning... <strong>Chinese and English</strong>.
rd03-02 | 比如，一个孩子能<strong>听懂</strong>中文，却还不认识很多<strong>汉字</strong>。 ｜语速 0.9 ｜停顿 0.55
     en | One child may <strong>understand</strong> spoken Chinese but know only a few Chinese <strong>characters</strong>.
rd03-03 | <strong>另一个</strong>孩子读中文比较顺，讲<strong>英文</strong>时却需要帮助。 ｜语速 0.9
     en | <strong>Another</strong> may read Chinese more easily but need help speaking <strong>English</strong>.
rd03-04 | 这些情况和阅读障碍，有<strong>不同的原因</strong>。 ｜语速 0.85 ｜停顿 0.65
     en | These difficulties have <strong>different causes</strong> from dyslexia.
rd03-05 | 它们提醒我们一个相似的问题：哪一步<strong>难</strong>？还能<strong>从哪里开始</strong>？ ｜语速 0.88 ｜停顿 0.6
     en | They invite a similar teaching question: <strong>which step</strong> is difficult, and <strong>where else</strong> can we begin?

## RD04 · 两个孩子，两扇门

rd04-01 | 我们来设想<strong>两个</strong>孩子。 ｜语气 亮 ｜语速 0.9
     en | Let's imagine... <strong>two</strong> children.
rd04-02 | Jacob 用<strong>中文</strong>讲故事比较顺，Mary 用<strong>英文</strong>讲比较顺。 ｜语速 0.92
     en | Jacob tells stories more easily in <strong>Chinese</strong>. Mary tells them more easily in <strong>English</strong>.
rd04-03 | 学<strong>中文</strong>时，Jacob 可以帮 Mary；学<strong>英文</strong>时，Mary 可以帮 Jacob。 ｜语速 0.92
     en | Jacob can help Mary with <strong>Chinese</strong>, and Mary can help Jacob with <strong>English</strong>.
rd04-04 | 这就是“<strong>互惠</strong>”：我有能帮<strong>你</strong>的地方，你也有能帮<strong>我</strong>的地方。 ｜语速 0.85 ｜停顿 0.85
     en | That is... <strong>reciprocity</strong>: I have something that can help <strong>you</strong>, and you have something that can help <strong>me</strong>.
rd04-05 | 两个人<strong>都教</strong>，也<strong>都学</strong>！ ｜语气 亮 ｜语速 0.9 ｜停顿 0.55
     en | <strong>Both</strong> children teach, and <strong>both</strong> learn!

## RD05 · 共同的渠道：先一起看见

rd05-01 | 可是，一开始话还说不通，<strong>怎么办</strong>？ ｜语速 0.88
     en | What if they <strong>cannot yet</strong> explain everything to each other?
rd05-02 | 我们想到<strong>画画</strong>！ ｜语气 亮 ｜语速 0.9 ｜停顿 0.85
     en | We thought of... <strong>drawing</strong>!
rd05-03 | 两个人可以先画<strong>同一个</strong>故事，看<strong>同一张</strong>图。 ｜语速 0.95
     en | They can draw the <strong>same</strong> story and look at the <strong>same</strong> picture.
rd05-04 | 图画让他们有一件可以<strong>一起看</strong>、<strong>一起说</strong>的事。 ｜语速 0.9
     en | Now they have something to <strong>look at</strong> and <strong>talk about</strong> together.
rd05-05 | 这是他们<strong>共同的渠道</strong>。 ｜语速 0.85 ｜停顿 0.55
     en | Drawing is <strong>a channel they share</strong>.
rd05-06 | 看图之后，也要问问对方：你想表达的，是<strong>这个意思</strong>吗？ ｜语速 0.9 ｜停顿 0.6
     en | They still need to ask each other: is this what you <strong>meant</strong>?

## RD06 · 一次互教，可以怎样发生？

rd06-01 | 比如，他们一起画一个小故事：<strong>杯子倒了</strong>，朋友来<strong>帮忙</strong>。 ｜语气 亮 ｜语速 0.95
     en | For example, they draw a small story: <strong>a cup tips over</strong>, and a friend comes to <strong>help</strong>.
rd06-02 | Jacob 指着画说： ＋ [示范·慢] 我来帮你。　（分段朗读，此行只读不改）
     en | Jacob points to the picture and says, ＋ [示范·慢] 我来帮你。
rd06-03 | Mary 告诉他，英文可以说： ＋ [示范·慢] Let me help you.　（分段朗读，此行只读不改）
     en | Mary tells him, in English, we can say, ＋ [示范·慢] Let me help you.
rd06-04 | 然后，<strong>交换</strong>！ ｜语气 亮 ｜语速 0.9 ｜停顿 0.55
     en | Then they... <strong>switch</strong>!
rd06-05 | Mary 试着说<strong>中文</strong>，Jacob 试着说<strong>英文</strong>。 ｜语速 0.92
     en | Mary tries the <strong>Chinese</strong>, and Jacob tries the <strong>English</strong>.
rd06-06 | 说不顺？可以听一听，<strong>再试一次</strong>。 ｜语气 亮 ｜语速 0.9
     en | If a phrase is difficult, they can listen, and <strong>try again</strong>.
rd06-07 | 遇到不认识的字，就把这个字<strong>找出来</strong>，<strong>一起学</strong>。 ｜语速 0.92
     en | If a written word is unfamiliar, they <strong>find it</strong> and learn it <strong>together</strong>.
rd06-08 | 老师在旁边，帮他们<strong>确认意思</strong>。 ｜语速 0.88 ｜停顿 0.6
     en | Their teacher helps them <strong>check the meaning</strong>.

## RD07 · 文字、声音、图画，各有用处

rd07-01 | <strong>文字</strong>，让我们学着<strong>自己读</strong>。 ｜语速 0.9
     en | <strong>Written words</strong> help us learn to read <strong>for ourselves</strong>.
rd07-02 | <strong>声音</strong>，可以示范<strong>怎么说</strong>。 ｜语速 0.9 ｜停顿 0.35
     en | <strong>Sound</strong> can show us how a phrase is <strong>spoken</strong>.
rd07-03 | <strong>图画</strong>，帮我们<strong>一起</strong>谈故事。 ｜语速 0.9 ｜停顿 0.35
     en | <strong>Pictures</strong> give us something to discuss <strong>together</strong>.
rd07-04 | 什么时候用哪一种，要看这次<strong>想学什么</strong>。 ｜语速 0.85 ｜停顿 0.75
     en | We choose what to use by asking what we <strong>want to learn</strong>.
rd07-05 | <strong>理解故事</strong>时，可以先看图、听故事。 ｜语速 0.92 ｜停顿 0.55
     en | To <strong>understand a story</strong>, we may begin with pictures and listening.
rd07-06 | <strong>练认字</strong>时，可以<strong>先试着读</strong>，需要时，再用声音和图画帮忙。 ｜语速 0.92
     en | To <strong>practise word reading</strong>, we can <strong>try reading first</strong>, and add sound or pictures when needed.

## RD08 · 学新的，也让原来的继续长

rd08-01 | 还有一件事，<strong>很重要</strong>： ｜语速 0.82 ｜停顿 1
     en | There is something else... we <strong>care about</strong>.
rd08-02 | 学英文时，中文<strong>也</strong>可以继续用； ｜语速 0.9 ｜停顿 0.6
     en | Chinese can <strong>keep growing</strong> while a child learns English.
rd08-03 | 学中文时，英文<strong>也</strong>有用。 ｜语速 0.9 ｜停顿 0.3
     en | English <strong>still matters</strong> while a child learns Chinese.
rd08-04 | 喜欢画画的孩子，可以<strong>继续画</strong>，也用画<strong>帮助大家</strong>学。 ｜语气 亮 ｜语速 0.92 ｜停顿 0.55
     en | A child who enjoys drawing can <strong>keep drawing</strong>, and use it to <strong>help the group</strong> learn.
rd08-05 | 我们希望孩子学会<strong>新的</strong>东西，同时，把<strong>原来会的</strong>，用得更好。 ｜语速 0.85 ｜停顿 0.7
     en | We want children to learn something <strong>new</strong>, while making good use of what they <strong>already know</strong>.

## RD09 · 这条渠道，也可以连接两代人

rd09-01 | <strong>父母和孩子</strong>，也可以这样试。 ｜语速 0.9 ｜停顿 1
     en | <strong>Parents and children</strong> can try this too.
rd09-02 | 父母更习惯<strong>中文</strong>，孩子更习惯<strong>英文</strong>，可以一起画、一起讲<strong>同一个</strong>故事。 ｜语速 0.92
     en | If parents are more comfortable in <strong>Chinese</strong> and children in <strong>English</strong>, they can draw and tell the <strong>same</strong> story together.
rd09-03 | 父母说出自己的意思，孩子帮助找英文的说法，再<strong>一起确认</strong>。 ｜语速 0.92
     en | A parent shares what they mean, a child helps find the English words, and they <strong>check it together</strong>.
rd09-04 | <strong>两代人</strong>都有可以<strong>分享</strong>的东西，也都有可以<strong>学习</strong>的东西。 ｜语速 0.85 ｜停顿 0.7
     en | <strong>Both generations</strong> have something to <strong>share</strong>, and something to <strong>learn</strong>.

## RD10 · 结尾

rd10-01 | 这就是“<strong>语言的桥</strong>”。 ｜语速 0.85 ｜停顿 1
     en | This is our... <strong>Language Bridge</strong>.
rd10-02 | 我们从阅读障碍教育得到启发，正在设计<strong>中英双语</strong>的多媒体学习方式。 ｜语速 0.9 ｜停顿 0.6
     en | Inspired by dyslexia education, we are designing ways to learn through <strong>Chinese, English</strong>, words, sound, and pictures.
rd10-03 | 从<strong>一个共同的故事</strong>开始： ｜语速 0.88 ｜停顿 0.6
     en | We can begin with <strong>one shared story</strong>.
rd10-04 | <strong>你教我</strong>一句，<strong>我教你</strong>一句，我们<strong>一起</strong>多懂一点！ ｜语气 亮 ｜语速 0.85 ｜停顿 0.55
     en | <strong>You</strong> teach me a phrase, <strong>I</strong> teach you a phrase, and we understand a little more <strong>together</strong>!
