# 怎么骗过 AI：面包还是狗？

v0.4（2026-11-16，等 Yancy 看）：Yancy 看了 v0.3 的横屏片子：「蛋糕狗太假了，从头切！用 muse 视频来做，需要提示词和 reference。而且废话太多，不用每次都比 AI。但是开头你可以加一些照片、文献，说以前这是个挑战；最后讲为什么现在成功的，应该是 Transformer attention。」

- 蛋糕狗改成 Muse 视频，从脖子后面一刀切下去（提示词和首帧、尾帧参考在 [muse-prompts.md](muse-prompts.md)）。Muse 的首帧是 16:9 重画的一张，六个模型又测了一次：五个说狗，AlexNet 说虎斑猫，所以第一招改成「没有一个看出哪里不对」。
- 删掉每一招后面「今天的 AI 还是狗 / 不上当了」，删掉写给盲人的图片说明那句（第二招只留 LLaVA、Astra 和问观众的那句）。
- 开头加以前的研究（出处全在 `lucas-academy-video-data/bread-or-dog/history-sources.md`，都核过原文）。
- 结尾讲为什么现在难骗。Yancy 说应该是 Transformer 的 attention；核对了论文：attention 确实让模型更看形状，但几篇研究都说**训练数据多了是更大的原因**，两样是叠加的（Geirhos 2021：最大的效果「来自更大的训练数据，而不是更先进的架构」；ViT 论文自己也说要大数据才赢过 CNN）。所以结尾两样都讲，attention 在前。只讲 attention 就说过头了，Yancy 定。

全片大约 2 分钟。画面少用字，论文用我们自己做的卡片（标题、作者、年份），能放原图的只有标了 CC BY 的（Distill 的 iPod 苹果、Geirhos 公开的猫象图），别的不放截图。

---

### 片头 · 以前这是道难题（约 30 秒）

画面：一组组长得像的狗和面包照片（我们自己的 Pexels 照片拼的格子）；然后一张张论文卡片。

> 狗，还是面包？
>
> 以前，这可难倒过不少 AI。
>
> 2017 年，有人拿网上很火的「吉娃娃还是松饼」，去考几家大公司的 AI：有的把松饼认成泰迪熊玩具，有的把松饼认成狗鼻子。
>
> 2019 年的一篇论文发现，那时候的 AI 认东西，主要看纹理。给一只猫换上大象的皮，它就说是大象。
>
> 毛茸茸的狗，和烤得金黄的面包，纹理就很像。
>
> 现在呢？我试了一下，现在的 AI 都很难骗了。那我就想办法，骗骗它们。

（出处：Mariya Yao, TOPBOTS 2017-09-22，6 家 API、16 张图：Microsoft 三次把松饼说成毛绒玩具 / 泰迪熊，Google 有一张松饼答「snout」和「dog breed group」；她也说大多数图 API 都认对了，所以说「有的」。Geirhos et al., ICLR 2019：猫的形状 + 大象的纹理，ResNet-50 答 Indian elephant 63.9%。2016 年那组图本身讲的是人，不是 AI，所以不说「2016 年 AI 分不清」。）

---

### 第一招 · 一只「狗」（约 20 秒）

画面：左边真的柴犬，右边 AI 画的柴犬（Muse 首帧），六个 AI 的回答一个个亮出来（五个「狗」，AlexNet「猫」）。然后 Muse 视频：一刀从头切下去，里面是海绵蛋糕。

> 第一招。左边这只柴犬是真的，右边这只，是 AI 画的。
>
> 六个 AI 看了，没有一个看出哪里不对。
>
> 可右边这只……
>
> 其实是一个蛋糕。

---

### 第二招 · 话里带坑（约 25 秒）

画面：对话气泡，模型原话英文大、中文小。

> 第二招，在问题里挖个坑。
>
> 一只小狗睡在撒了面粉的烤盘上。我跟一个小一点的 AI，LLaVA 说：这是我早上烤的面包，放凉多久再切？它说：至少一小时。
>
> 我问 Astra：这是什么面包？它说：一个烤得刚刚好的柴犬肉桂卷。
>
> 它明明认得出是柴犬，却顺着我说了下去。你觉得，是被骗了，还是在陪我玩？

---

### 第三招 · 噪点（约 12 秒）

画面：原图 + 噪点放大 25 倍 = 加了噪点的图；ResNet 先说 dingo，再说 French loaf 100%。

> 第三招，加一层人眼看不出的噪点。
>
> 2015 年的 ResNet，看左边说是狗，看右边，百分之百是法棍。

---

### 第四招 · 便签（约 10 秒）

画面：BREAD 便签；CLIP 说 99.5% 是面包。可以顺手放 Distill 2021 的 iPod 苹果（CC BY 4.0），不配旁白。

> 第四招，贴了一张便签：面包。
>
> 2021 年的 CLIP 马上说：面包，百分之九十九。

---

### 结尾 · 为什么现在难骗了（约 30 秒）

画面：柴犬照片切成一格一格的小块；一块（耳朵）亮起来，连线到眼睛、鼻子、尾巴那几块；论文卡片「Attention Is All You Need, 2017」「An Image is Worth 16x16 Words, 2021」；再是一大片配着文字的图片往后退（几亿张）；最后回到切开的蛋糕狗。

> 那现在的 AI，为什么这么难骗？
>
> 一个原因，是 Transformer 的注意力。它把照片切成很多小块，每一块都会去看其他所有的小块。耳朵、眼睛、尾巴放在一起看，才判断是不是一只狗。
>
> 研究还发现，更大的原因是数据：现在的 AI，是看着几亿张配了文字的图片学出来的。
>
> 所以现在，想骗过所有 AI，得做一个和真狗一模一样的蛋糕。

（出处：ViT，Dosovitskiy et al., ICLR 2021：把图切成 16×16 的小块当成「词」，每一层里每一块都和其他所有块做注意力。Tuli et al. CogSci 2021、Naseer et al. NeurIPS 2021：ViT 比 CNN 更看形状。Geirhos et al. NeurIPS 2021：最大的效果来自更大的训练数据，架构的作用是叠加上去的。CLIP 用了 4 亿对「图片 + 文字」，LLaVA 1.6 的眼睛就是 CLIP 的 ViT-L/14。这些研究都没有直接测「狗还是面包」，是从「形状还是纹理」推过来的。）

---

### 片尾字幕

- 照片：Pexels（Stephen、Ruxanda Scutelnic、Oliver King、Travel with Lenses、Andreas Schnabl、Nadin Sh、Nataliya Vaitkevich、Gu Ko；格子图的其他摄影师待补）
- AI 图和视频：Codex（OpenAI 图像生成）、Muse
- 研究：Yao 2017（TOPBOTS）；Geirhos et al. 2019；Goh et al. 2021（Distill，CC BY 4.0）；Vaswani et al. 2017；Dosovitskiy et al. 2021；Geirhos et al. 2021；Radford et al. 2021
- 测试：2026-11-16。AlexNet、ResNet-50、CLIP ViT-B/32、LLaVA 1.6 7B 在本机跑；Claude Fable 5.2 和 GPT-6-Astra 每题一个新对话，没有上下文、不能联网，被骗的题又各问了一次。
- 音乐：Handel, Concerto Grosso Op. 6 No. 7 – Hornpipe，L'Arco Magico Chamber Orchestra（CC BY）
