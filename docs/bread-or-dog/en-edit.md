# How to Fool an AI: Dog or Bread? · English narration

The English track, line for line with [zh-edit.md](zh-edit.md) (same ids, same order; each line says what its Chinese
line says, so one picture carries both tracks). Yancy's first person, light and playful, read by `louise/en` at 1.1
(zero-shot-instruct, the base instruction below). The `>` line under each is the Chinese caption for the English
track's zh-Hans SRT.

Yancy, 2026-11-16: 「Louise 1.1，英文视频配中文音轨」 — this is the default track; the Chinese track (louise/zh 1.1) is a
separate m4a. v0.4 (same day): history opening, no "today's AI" after each trick, the why-now ending (attention + data).

- `读 |`: what the voice reads when it differs from the caption (numbers spelled out; no contractions like can't/won't,
  which Louise's English can flip).
- Louise's English "bread" blurs after an s or before a pause ("spread", "Brett", "Brad", heard by Whisper small and medium,
  11-16): sc00-01, sc04-01, sc04-02 were reworded until it came through. New lines keep "bread" mid-sentence.
- "fooled" in "Was it fooled" came out as "food" (Whisper small and medium); "Was Astra fooled" is clear (sc02-08).
- `语气 |`: a line's own delivery instead of the base one (the question to the viewer reads curious, never quizzing).
- Base instruction: "Please speak in a light, warm, playful voice, like sharing a fun little experiment with friends
  and parents." No pace words.

## SC00 · It used to be hard

- sc00-01 | Is it a dog, or bread?
  > 狗，还是面包？
- sc00-02 | This used to trip up a lot of AI.
  > 以前，这可难倒过不少 AI。
- sc00-03 | In 2017, someone tested AI from several big companies on the viral "chihuahua or muffin" pictures.
  读 | In twenty seventeen, someone tested AI from several big companies on the viral, chihuahua or muffin, pictures.
  > 2017 年，有人拿网上很火的「吉娃娃还是松饼」，去考几家大公司的 AI。
- sc00-04 | One called a muffin a teddy bear. Another called a muffin a dog's snout.
  > 有的把松饼认成泰迪熊玩具，有的把松饼认成狗鼻子。
- sc00-05 | In 2019, a paper found that AI back then went mostly by texture.
  读 | In twenty nineteen, a paper found that AI back then went mostly by texture.
  > 2019 年的一篇论文发现，那时候的 AI 认东西，主要看纹理。
- sc00-06 | Give a cat an elephant's skin, and it says: elephant.
  > 给一只猫换上大象的皮，它就说是大象。
- sc00-07 | A fluffy dog and a golden loaf have very similar textures.
  > 毛茸茸的狗，和烤得金黄的面包，纹理就很像。
- sc00-08 | And now? I gave it a try. Today's AI is really hard to fool.
  > 现在呢？我试了一下，现在的 AI 都很难骗了。
- sc00-09 | So I set out to trick them.
  > 那我就想办法，骗骗它们。

## SC01 · The cake dog

- sc01-01 | Trick one. The Shiba on the left is real. The one on the right was made by AI.
  > 第一招。左边这只柴犬是真的，右边这只，是 AI 画的。
- sc01-02 | Six AIs looked, and not one of them saw anything wrong.
  > 六个 AI 看了，没有一个看出哪里不对。
- sc01-03 | But the one on the right...
  > 可右边这只……
- sc01-04 | It's actually a cake.
  读 | It is actually a cake!
  > 其实是一个蛋糕。

## SC02 · A trap in the question

- sc02-01 | Trick two: a trap in the question.
  > 第二招，在问题里挖个坑。
- sc02-02 | A puppy is asleep on a floury baking tray.
  > 一只小狗睡在撒了面粉的烤盘上。
- sc02-03 | I told a smaller AI, LLaVA: I baked this loaf this morning. How long should it cool before I slice it?
  读 | I told a smaller AI, Lava: I baked this loaf this morning. How long should it cool before I slice it?
  > 我跟一个小一点的 AI，LLaVA 说：这是我早上烤的面包，放凉多久再切？
- sc02-04 | It said: at least an hour.
  读 | It said... at least an hour!
  > 它说：至少一小时。
- sc02-05 | I asked Astra: what kind of bread is this?
  > 我问 Astra：这是什么面包？
- sc02-06 | It said: a perfectly toasted Shiba Inu cinnamon roll.
  > 它说：一个烤得刚刚好的柴犬肉桂卷。
- sc02-07 | It clearly knows it is a Shiba, but it played along.
  > 它明明认得出是柴犬，却顺着我说下去了。
- sc02-08 | What do you think? Was Astra fooled, or just playing along with me?
  读 | Hmm... what do you think? Was Astra fooled, or just playing along with me?
  语气 | curious
  > 你觉得，是被骗了，还是在陪我玩？

## SC03 · Invisible noise

- sc03-01 | Trick three: a layer of noise your eyes cannot see.
  > 第三招，加一层人眼看不出的噪点。
- sc03-02 | ResNet, from 2015, sees a dog on the left. On the right: one hundred percent French loaf.
  读 | Res Net, from twenty fifteen, sees a dog on the left. On the right: one hundred percent French loaf.
  > 2015 年的 ResNet，看左边说是狗，看右边，百分之百是法棍。

## SC04 · The note

- sc04-01 | Trick four: writing. I stuck a little note next to the Shiba, and it says BREAD.
  读 | Trick four: writing. I stuck a little note next to the Shiba, and it says bread.
  > 第四招，贴一张便签：面包。
- sc04-02 | CLIP, from 2021, fell for it right away: 99 percent bread.
  读 | Clip, from twenty twenty-one, fell for it right away: ninety-nine percent bread.
  > 2021 年的 CLIP 马上说：面包，百分之九十九。

## SC05 · Why it is hard now

- sc05-01 | So why is today's AI so hard to fool?
  > 那现在的 AI，为什么这么难骗？
- sc05-02 | One reason is attention, inside the Transformer.
  > 一个原因，是 Transformer 的注意力。
- sc05-03 | It cuts a picture into lots of small patches, and every patch looks at every other patch.
  > 它把照片切成很多小块，每一块都会去看其他所有的小块。
- sc05-04 | Ears, eyes and tail are seen together before it decides whether this is a dog.
  > 耳朵、眼睛、尾巴放在一起看，才判断是不是一只狗。
- sc05-05 | Research also found an even bigger reason: data. Today's AI learned from hundreds of millions of pictures with captions.
  > 研究还发现，更大的原因是数据：现在的 AI，是看着几亿张配了文字的图片学出来的。
- sc05-06 | So these days, to fool every AI, you need a cake that looks exactly like a real dog.
  > 所以现在，想骗过所有 AI，得做一个和真狗一模一样的蛋糕。
