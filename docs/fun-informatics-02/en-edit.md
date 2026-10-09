# Do You Know Claude? 英文配音稿（英文制作适配 · v0.6 · 2026-10-09）

Fun Informatics 2. By Yancy Qin, Louise Yang | Lucas Academy. Video plan: [FUN-INFORMATICS-02.md](../../FUN-INFORMATICS-02.md).

写法与中文稿相同：`<strong>…</strong>` 是强调，字幕里自动去掉；每句下面 `>` 开头的是对应的中文，只作对照，不会读出来。

v0.6：英文版沿用定稿结构，教学例子为英语重新编写。中文只在猜字游戏的对照画面中保留；下方中文译文用于英文片的中文字幕，不改中文版台词。

屏幕与读法：
- 开场填空：Emma pulled on her sho__ and stepped out into the ra__. Beside the gate, she spotted a ___.
- cl03-04 的 L、D 按字母名称读；游戏对照不逐字解释中文选项。
- cl03-14 屏幕：The ltitle dog ran aorund the gadren. 旁白按正常拼写读。
- 注意力例子：Maya lent Ben a book. He read it on the train. 连线只作示意。
- 年份和字母在 narration.py 中明确拼写，字幕保留常规写法。

Voice: `louise/en`, using the current Fun Informatics 1 delivery (scripts/voice_defaults.py).

Overall tone: Please speak in a curious, unhurried voice, like discovering something together with a child.
Overall speed: 1.0

## CL00 · Opening: take some away, can you still tell?

Section tone: 

- cl00-01 | Let's start with a little game. What is this?
  > 先来玩个小游戏。这是什么？
- cl00-02 | Just patches of colour, right? Let's slowly step back...
  > 只是一块一块的颜色，对吧？我们慢慢往后退……
- cl00-03 | It's a pond, with water lilies floating on it.
  > 原来是一个池塘，水面上开着睡莲。
- cl00-04 | One more. This sentence has a few letters missing. Can you still read it?
  > 再来一个。这句英文缺了几个字母，你还读得出来吗？
- cl00-05 | The first two are fairly easy: shoes, rain. But what did Emma spot beside the gate? A cat, a dog, or a fox? The sentence doesn't tell us.
  > 前两个比较容易：鞋子、雨。可艾玛在门边看见了什么？猫、狗，还是狐狸？这句话没有告诉我们。
- cl00-06 | The part you can guess has a name: <strong>redundancy</strong>. The part you can't guess is the <strong>information</strong>.
  > 猜得中的那部分，有个名字，叫<strong>冗余</strong>。猜不中的那部分，才是<strong>信息</strong>。
- cl00-07 | Everyone in this episode is called Claude, and what they do is, in a way, the same thing. Do you know Claude? How many do you know?
  > 今天这一集的主角，都叫 Claude。他们做的，其实是同一件事。你认识 Claude 吗？认识几个？

## CL01 · Three Claudes

Section tone: 

- cl01-01 | The first Claude is a painter: Claude Monet, born in France in 1840.
  > 第一个 Claude，是一位画家：克劳德·莫奈。他 1840 年生在法国。
- cl01-02 | The second Claude is a scientist: Claude Shannon. We met him last time; he measured information in bits.
  > 第二个 Claude，是一位科学家：克劳德·香农。上一集我们见过他，他用比特量出了信息。
- cl01-03 | They were born more than seventy years apart, yet for ten years they were both alive.
  > 他们俩出生差了七十多年，却在这个世界上同时活过十年。
- cl01-04 | In 1916, Monet was painting water lilies in his garden in France. That same year, Shannon was born in America.
  > 1916 年，莫奈在法国的花园里画睡莲；同一年，香农在美国出生。
- cl01-05 | And the third Claude? We'll tell you later.
  > 第三个 Claude 是谁？先卖个关子，后面再告诉你。
- cl01-06 | Let's start with the painter.
  > 我们先从画家开始。

## CL02 · The first Claude: Monet takes redundancy away

Section tone: 

- cl02-01 | The year before Monet was born, photography was revealed to the world.
  > 莫奈出生的前一年，照相术刚刚公开问世。
- cl02-02 | A camera can keep every leaf and every ripple, exactly as it is.
  > 照相机能把每一片叶子、每一道水波，都原原本本地留下来。
- cl02-03 | But Monet wanted to paint something else: the light and colour he saw at first glance.
  > 莫奈想画的，却是另一样东西：他第一眼看到的光和颜色。
- cl02-04 | In 1872, he painted a harbour at dawn, and called it Impression, Sunrise.
  > 1872 年，他画了一幅清晨的港口，名字叫《印象·日出》。
- cl02-05 | A critic made fun of it: that's not a painting, it's just an "impression"!
  > 有个评论家看了，嘲笑说：这哪是画，不过是个「印象」！
- cl02-06 | And the name stuck. That's how the Impressionists got their name.
  > 结果，「印象派」这个名字，就这么留了下来。
- cl02-07 | Let's see how much he left out. On the left, the little Japanese-style bridge in his garden; on the right, his painting.
  > 来看看他到底省掉了多少。左边，是他花园里那座日本式小桥的样子；右边，是他画的。
- cl02-08 | Every leaf, every rail, every detail on the water: he didn't paint them one by one.
  > 每一片叶子、每一根栏杆、水面上的每一个细节，他都没有一笔一笔去画。
- cl02-09 | If I paint only from my impression and leave the details out, can you still recognise it?
  > 如果我只凭印象画，去掉细节，你还认得出来吗？
- cl02-10 | Yes, you can. So the details he left out are <strong>redundancy</strong>: your eyes fill them in.
  > 认得出来。那么，去掉的那些细节，就是<strong>冗余</strong>：你的眼睛自己能补上。
- cl02-11 | Let's try it ourselves: hand some everyday places to Monet's eyes.
  > 我们也来试试：把身边的景色，交给莫奈的眼睛。
- cl02-12 | Lots of detail is gone, yet you know them at a glance: a street, a playground, the seaside.
  > 细节少了很多，可你一眼就认得出：这是街道，这是操场，这是海边。
- cl02-13 | He also painted haystacks in the same field, more than twenty times.
  > 他还画过同一片田里的干草堆，一画就是二十多幅。
- cl02-14 | The haystacks hardly change; you can guess them at a glance. What he really wanted to show you was the light, different every time: early morning, sunset, after snow.
  > 草堆每次都差不多，你一看就猜得到。他真正想告诉你的，是每一幅里不一样的光：清晨、黄昏、雪后。
- cl02-15 | What you can guess, he paints in a stroke. The light you can't guess is the <strong>information</strong>.
  > 猜得到的，他一笔带过；猜不到的光，才是这幅画里的<strong>信息</strong>。
- cl02-16 | But what if he took away too much? If only a few patches of colour were left... you wouldn't recognise it.
  > 可是，去掉太多会怎样？如果只剩下几块颜色……你就认不出来了。
- cl02-17 | Take away the redundancy, and the picture is still there. Take away the information too, and the picture is gone. So how much can you take away? For that, we ask the second Claude.
  > 去掉冗余，画还在；连信息也去掉，画就没了。那到底能去掉多少？这个问题，要问第二个 Claude。

## CL03 · The second Claude: Shannon measures redundancy

Section tone: 

- cl03-01 | Shannon was a playful scientist. He liked to ride a unicycle while juggling.
  > 香农是个很好玩的科学家。他喜欢一边骑独轮车，一边抛球杂耍。
- cl03-02 | He once ran an experiment: take a book, cover what comes next, and ask someone to guess it, one letter at a time.
  > 他做过一个实验：拿一本书，遮住后面的字母，让人一个一个地猜。
- cl03-03 | We made a <strong>guess-the-letters</strong> game inspired by that idea: fill in English one letter at a time, and Chinese one character at a time. Each time, choose from four options.
  > 我们照着这个想法，做了一个<strong>猜字</strong>游戏：英文一个字母一个字母地补，中文一个字一个字地补。每次都从四个选项里选一个。
- cl03-04 | In English above, we finish world in two steps: first L, then D. The lower panel shows the same idea in Chinese, one character at a time.
  > 上面的英文把 world 分两步补完：先 L，再 D。下方中文展示相同的玩法，一次补一个汉字。
- cl03-05 | We aren't choosing a whole word yet: the options are single letters. The words before the gap, For God so loved the, help us predict world, and then its next letter.
  > 现在选的还不是整个词，选项是一个个字母。空格前面的 For God so loved the 帮我们预测 world，再猜它的下一个字母。
- cl03-06 | Keep going: letter by letter in English, character by character in Chinese. If you know this verse by heart, you can fill almost every blank on the first try.
  > 再一路往后补，英文逐个字母，中文逐个字。如果你背过这节经文，几乎每个空都能一次补对。
- cl03-07 | That doesn't mean the verse isn't important. Just the opposite: you've kept it in your heart, so you can fill it in, letter by letter.
  > 这不是说这节经文不重要。恰恰相反：你把它记在了心里，所以才能一个字一个字地补出来。
- cl03-08 | Try a verse you've never read, and it's not so easy: suddenly, many more letters take two or three tries.
  > 换一节你没读过的经文，就没那么容易了：猜了两次、三次的字，一下子多了起来。
- cl03-09 | So how much information a sentence carries depends not only on the sentence, but on what the listener already knows.
  > 所以，一句话里有多少信息，不只看这句话，还要看听的人已经知道什么。
- cl03-10 | With games like this, Shannon measured something surprising: about <strong>half</strong> of written English is redundancy.
  > 香农用这样的游戏，量出了一个惊人的数字：英文里，大约<strong>一半</strong>是冗余。
- cl03-11 | In his words: when we write English, half of what we write is determined by the structure of the language, and half is chosen freely.
  > 他是这么说的：我们写英文的时候，一半是由语言的规律决定的，只有一半是自由选的。
- cl03-12 | He noticed something fun, too: with no redundancy at all, any jumble of letters would be a sentence; with too much, nobody could make a big crossword puzzle.
  > 他还说过一件好玩的事：要是一点冗余都没有，随便乱拼的字母都算一句话；要是冗余太多，就编不出大的填字游戏。
- cl03-13 | So why does language keep so much redundancy? Try this sentence with a few letters muddled.
  > 那为什么语言保留这么多冗余？试着读这句有几个字母乱序的英文。
- cl03-14 | The ltitle dog ran aorund the gadren.
  > 小狗在花园里跑来跑去。
- cl03-15 | Did you still recognise the sentence? Familiar words and context help you fill in the gaps. It won't work for every jumble, but a few typos, or a few words lost on a bad phone line, don't always destroy the message.
  > 你还认得出这句话吗？熟悉的词和上下文能帮你补全。并不是每种乱序都有效，但几个错字、电话里漏掉几个词，不一定会破坏整个消息。
- cl03-16 | Redundancy is like a backup. It helps a message get through the <strong>noise</strong>.
  > 冗余就像备份，帮消息扛过<strong>噪声</strong>。
- cl03-17 | So Shannon tells us: take redundancy out, and a message gets shorter; keep some in, and it gets stronger. A good code thinks about both.
  > 所以香农告诉我们：去掉冗余，消息更短；留下一些冗余，消息更结实。好的编码，两件事都要想。
- cl03-18 | In 1948, Shannon did one more thing: he counted which words tend to follow which in English, then followed those counts to chain words together, one at a time.
  > 1948 年，香农还做了一件事：他统计英文里一个词后面常跟着哪些词，再照着统计，一个词一个词地往下接。
- cl03-19 | The sentences sounded like English, but made no sense at all.
  > 接出来的句子，读起来很像英文，意思却乱七八糟。
- cl03-20 | You could call it a very, very early "language model". More than seventy years later, that idea grew up.
  > 那可以算是很早很早的「语言模型」。七十多年后，这个想法长大了。

## CL04 · The third Claude: learning to talk from redundancy

Section tone: 

- cl04-01 | So who is the third Claude? Here's a secret: the words you're hearing right now were written by him.
  > 第三个 Claude 是谁？告诉你一个秘密：你现在听到的这段话，就是他写的。
- cl04-02 | He's an AI made by Anthropic, and his name is widely seen as a tribute to Shannon.
  > 他是 Anthropic 做的人工智能，名字被普遍认为是在致敬香农。
- cl04-03 | For this part, let's hear it from him.
  > 下面这段，就让他自己来说。
- cl04-04 | Hi, I'm Claude. How did I learn to talk? We were filling in one letter or character at a time. Now let's try something different: <strong>guess the next word</strong>.
  > 大家好，我是 Claude。我是怎么学会说话的？刚才，我们一个字一个字地补。现在换个玩法：<strong>猜下一个词</strong>。
- cl04-05 | This time, each sentence gives you its first few words. At every step after that, you guess a whole word from four options. Come on, let's play a few rounds.
  > 这次每句话先给你开头几个词，后面的每一步，都从四个选项里猜一整个词。来，一起玩几步。
- cl04-06 | When I first learned language, I practised predicting what would come next from the text before it, too. But I had far more than four possibilities, and far more practice: guess, check, adjust myself a little, then guess the next one.
  > 我最初学语言，练的也是根据前文预测后面会出现什么，只是候选远不止四个，练习的次数也多得多：猜一个，对一下，把自己调一调，再猜下一个。
- cl04-07 | I could learn only because language has redundancy. If every word were impossible to guess, there would be no patterns to learn.
  > 我能学会，正是因为语言有冗余。如果每个词都完全猜不到，那就没有规律可学。
- cl04-08 | The ruler that measures how well I guess is Shannon's "surprise": the more likely I thought the word that actually appeared was, the smaller the surprise. The less I expected it, the bigger the surprise.
  > 衡量我猜得好不好的那把尺子，用的正是香农的「意外」：我越觉得真正出现的词可能出现，意外就越小；越没想到它，意外就越大。
- cl04-09 | Before I guess the next word, I look back at every word so far and ask: which one helps me guess right now?
  > 猜下一个词之前，我会回头看前面的每一个词，问自己：现在，哪个词最能帮我猜？
- cl04-10 | Then I give each one a score, and look harder at the ones that score high. This is called <strong>attention</strong>.
  > 然后给它们打分，分数高的，多看几眼。这叫<strong>注意力</strong>，Attention。
- cl04-11 | For example: Maya lent Ben a book. He read it on the train. To work out who that he refers to, the earlier name Ben matters.
  > 比如：玛雅借给本一本书。他在火车上读了它。要明白这个“他”指谁，前面的名字“本”很重要。
- cl04-12 | In 2017, a famous paper about this idea gave itself a very bold title: Attention Is All You Need.
  > 2017 年，一篇很有名的论文讲的就是这个办法，题目起得很大胆：注意力，就是你需要的一切。
- cl04-13 | But I have my flaws. The first: sometimes I say too much.
  > 不过，我也有毛病。第一个：我有时候会说得太多。
- cl04-14 | AIs like me are often rewarded in training for answers that are long and thorough, so we tend to keep talking.
  > 像我这样的 AI，训练时常常因为回答又长又周全而得到更高的分，于是容易越说越多。
- cl04-15 | Much of the extra is redundancy: it sounds careful, but it doesn't tell you anything new.
  > 多出来的话，很多是冗余：听起来很认真，其实没多告诉你什么。
- cl04-16 | The second flaw matters more: every word I say is one I think is likely to come next.
  > 第二个毛病更要紧：我说出的每个词，都是我觉得很可能接在后面的词。
- cl04-17 | So even when I'm wrong, I can still sound smooth. Like this: Claude Shannon was born in France in 1840, and he was an Impressionist painter.
  > 所以就算我说错了，听起来也可能很通顺。比如这句：克劳德·香农，1840 年生在法国，是一位印象派画家。
- cl04-18 | Sounds smooth, right? But it mixes up two Claudes. Language patterns help it sound fluent; fluency is <strong>not the same as truth</strong>.
  > 听起来很顺吧？可它把两个 Claude 搞混了。语言规律让它流利，流利却不等于真实。
- cl04-19 | So when you listen to me, ask what Shannon would ask: how much of this is new? And how much of it is true?
  > 所以，听我说话的时候，也请像香农一样问一问：这里面，有多少是新的？有多少是真的？
- cl04-20 | Not all repetition is bad, though. A teacher saying the key point twice, me writing out every step: that's redundancy on purpose, so you don't miss anything, and so you can check it.
  > 当然，也不是所有的重复都不好。老师把重点说两遍，我把步骤一步一步写出来，都是故意留的冗余：让你不容易漏掉，也方便你检查对不对。

## CL05 · Three Claudes, one idea

Section tone: 

- cl05-01 | Now, let's put the three Claudes side by side.
  > 现在，把三个 Claude 放在一起。
- cl05-02 | Monet took redundancy away, and kept the light.
  > 莫奈把冗余去掉，留下了光。
- cl05-03 | Shannon measured it, and told us how much we can take away, and how much to keep.
  > 香农把冗余量了出来，告诉我们能去掉多少，该留下多少。
- cl05-04 | The third Claude learned to talk from redundancy, and reminds us: smooth is not the same as true.
  > 第三个 Claude 从冗余里学会了说话，也提醒我们：通顺，不等于对。
- cl05-05 | Claude Monet and Claude Shannon sharing a name is just a coincidence. But Claude Monet, Claude Shannon, and Claude the AI all help us ask the same question: what could you already guess, and what is truly new?
  > 克劳德·莫奈和克劳德·香农同名只是巧合。可克劳德·莫奈、克劳德·香农和 AI Claude 都帮我们问同一个问题：哪些你已经能猜到，哪些才是真正新的？
- cl05-06 | Next time you look at a painting, read a sentence, or listen to an AI, you can ask yourself that question too.
  > 下次你看一幅画、读一句话、听 AI 说话的时候，也可以问问自己这个问题。
- cl05-07 | We started with a few patches of colour. Now, step back... and there's the whole pond.
  > 我们从几块颜色开始。现在，往后退一步……你看到的，是整个池塘。

## CL06 · Easter egg: the fourth Claude

Section tone: 

- cl06-01 | Wait! How many Claudes do you know now? Three? There's a fourth.
  > 等一下！你认识几个 Claude 了？三个？其实还有第四个。
- cl06-02 | All the music in this episode was written by Claude Debussy, like Clair de Lune, which you're hearing now. He was born in France in 1862: after Monet, before Shannon.
  > 这一集的背景音乐，都是克劳德·德彪西写的，比如你现在听到的《月光》。他 1862 年生在法国，比莫奈晚，比香农早。
- cl06-03 | His music is often called Impressionist, just like Monet's paintings.
  > 他的音乐，常被人叫作「印象派」，就像莫奈的画。
- cl06-04 | He, too, took away the parts you could guess. By the old rules, a run of chords always walks back to the note you're waiting for; Debussy often doesn't, and leaves you colour, light and mood instead.
  > 他也在去掉你猜得到的部分：按老规矩，一串和弦总要走回你等着听的那个音；德彪西常常偏不，留下的是颜色、光和气氛。
- cl06-05 | From 1916 to 1918, all three human Claudes were alive at once: one painting, one composing, and one just born.
  > 1916 年到 1918 年，三位人类 Claude 同时活在这个世界上：一个在画画，一个在作曲，一个刚出生。
- cl06-06 | By the way, the fourth Claude—Debussy—was brought up by the third Claude—the AI—while writing this script. See? Saying a little more can pay off sometimes.
  > 说起来，这第四个 Claude——德彪西，是第三个 Claude——AI 写稿的时候提起来的。你看，多说一句，有时候也有好处。

## CL07 · The closing question

Section tone: 

- cl07-01 | So, with so much AI-generated information around us today, how do you tell what is new? What is true? What matters? What can you leave aside? These are questions we learn and think about together at Lucas Academy.
  > 那么，在今天这个充满 AI 生成信息的时代，你怎么分辨哪些是新的？哪些是真的？什么是重要的？什么可以忽略？这也是我们在 Lucas Academy 一起学习、一起思考的问题。
