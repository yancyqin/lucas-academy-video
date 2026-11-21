# 怎么骗过 AI：面包还是狗？· 中文旁白和字幕（中文音轨）

定稿原文，来自 [script.zh.md](script.zh.md) v0.4，一句一个编号。字幕和 SRT 只用这里的字；怎么读在 [voice-direction.md](voice-direction.md)。
每句下面的 `>` 是英文翻译。Yancy 2026-11-16：「Louise 1.1，英文视频配中文音轨」，所以英文是默认音轨（[en-edit.md](en-edit.md)），这里是中文音轨，单独做成 m4a。

- v0.4（2026-11-16）：Yancy「蛋糕狗太假了，从头切，用 Muse 视频」「废话太多，不用每次都比 AI」「开头加照片、文献，说以前这是个挑战；最后讲为什么现在成功」，结尾 attention + 数据「没问题」。编号重排了；没改字的句子沿用 v1 的配音。
- 「可右边这只……」「其实是一个蛋糕」还是两句：Muse 视频里那一刀落在两句中间。

## SC00 · 以前这是道难题

- sc00-01 | 狗，还是面包？
  > Is it a dog, or bread?
- sc00-02 | 以前，这可难倒过不少 AI。
  > This used to trip up a lot of AI.
- sc00-03 | 2017 年，有人拿网上很火的「吉娃娃还是松饼」，去考几家大公司的 AI。
  > In 2017, someone tested AI from several big companies on the viral "chihuahua or muffin" pictures.
- sc00-04 | 有的把松饼认成泰迪熊玩具，有的把松饼认成狗鼻子。
  > One called a muffin a teddy bear. Another called a muffin a dog's snout.
- sc00-05 | 2019 年的一篇论文发现，那时候的 AI 认东西，主要看纹理。
  > In 2019, a paper found that AI back then went mostly by texture.
- sc00-06 | 给一只猫换上大象的皮，它就说是大象。
  > Give a cat an elephant's skin, and it says: elephant.
- sc00-07 | 毛茸茸的狗，和烤得金黄的面包，纹理就很像。
  > A fluffy dog and a golden loaf have very similar textures.
- sc00-08 | 现在呢？我试了一下，现在的 AI 都很难骗了。
  > And now? I gave it a try. Today's AI is really hard to fool.
- sc00-09 | 那我就想办法，骗骗它们。
  > So I set out to trick them.

## SC01 · 蛋糕狗

- sc01-01 | 第一招。左边这只柴犬是真的，右边这只，是 AI 画的。
  > Trick one. The Shiba on the left is real. The one on the right was made by AI.
- sc01-02 | 六个 AI 看了，没有一个看出哪里不对。
  > Six AIs looked, and not one of them saw anything wrong.
- sc01-03 | 可右边这只……
  > But the one on the right...
- sc01-04 | 其实是一个蛋糕。
  > It's actually a cake.

## SC02 · 话里带坑

- sc02-01 | 第二招，在问题里挖个坑。
  > Trick two: a trap in the question.
- sc02-02 | 一只小狗睡在撒了面粉的烤盘上。
  > A puppy is asleep on a floury baking tray.
- sc02-03 | 我跟一个小一点的 AI，LLaVA 说：这是我早上烤的面包，放凉多久再切？
  > I told a smaller AI, LLaVA: I baked this loaf this morning. How long should it cool before I slice it?
- sc02-04 | 它说：至少一小时。
  > It said: at least an hour.
- sc02-05 | 我问 Astra：这是什么面包？
  > I asked Astra: what kind of bread is this?
- sc02-06 | 它说：一个烤得刚刚好的柴犬肉桂卷。
  > It said: a perfectly toasted Shiba Inu cinnamon roll.
- sc02-07 | 它明明认得出是柴犬，却顺着我说下去了。
  > It clearly knows it is a Shiba, but it played along.
- sc02-08 | 你觉得，是被骗了，还是在陪我玩？
  > What do you think? Was Astra fooled, or just playing along with me?

## SC03 · 噪点

- sc03-01 | 第三招，加一层人眼看不出的噪点。
  > Trick three: a layer of noise your eyes cannot see.
- sc03-02 | 2015 年的 ResNet，看左边说是狗，看右边，百分之百是法棍。
  > ResNet, from 2015, sees a dog on the left. On the right: one hundred percent French loaf.

## SC04 · 便签

- sc04-01 | 第四招，贴了一张便签：面包。
  > Trick four: writing. I stuck a little note next to the Shiba, and it says BREAD.
- sc04-02 | 2021 年的 CLIP 马上说：面包，百分之九十九。
  > CLIP, from 2021, fell for it right away: 99 percent bread.

## SC05 · 为什么现在难骗了

- sc05-01 | 那现在的 AI，为什么这么难骗？
  > So why is today's AI so hard to fool?
- sc05-02 | 一个原因，是 Transformer 的注意力。
  > One reason is attention, inside the Transformer.
- sc05-03 | 它把照片切成很多小块，每一块都会去看其他所有的小块。
  > It cuts a picture into lots of small patches, and every patch looks at every other patch.
- sc05-04 | 耳朵、眼睛、尾巴放在一起看，才判断是不是一只狗。
  > Ears, eyes and tail are seen together before it decides whether this is a dog.
- sc05-05 | 研究还发现，更大的原因是数据：现在的 AI，是看着几亿张配了文字的图片学出来的。
  > Research also found an even bigger reason: data. Today's AI learned from hundreds of millions of pictures with captions.
- sc05-06 | 所以现在，想骗过所有 AI，得做一个和真狗一模一样的蛋糕。
  > So these days, to fool every AI, you need a cake that looks exactly like a real dog.
