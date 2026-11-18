# 怎么骗过 AI · Muse 提示词

Yancy 2026-11-16：「蛋糕狗太假了，从头切！用 muse 视频来做，需要提示词和 reference」。

图都在 `lucas-academy-video-data/bread-or-dog/muse/frames/`（Codex 画的，提示词和日志在 `muse/codex/`）：

| 文件 | 用途 |
|---|---|
| `M01_first.png` | **首帧**（1672×941，16:9）。和测试用的那张蛋糕柴犬（k1）是同一个场景，Codex 放宽成 16:9 时重画了一点，所以又拿六个模型测了一次：五个说狗，AlexNet 说虎斑猫，没有一个看出是蛋糕 |
| `M01_end_a.png` | **尾帧参考 a（推荐）**：从脖子后面一刀切下去，头那一块往前推开几厘米，两个切面都是海绵蛋糕；刀放在地毯上 |
| `M01_end_b.png` | 尾帧参考 b：刀还插在切口里，只看得到刀身和刀柄的上端 |

Muse 能用尾帧就用 a；不能用尾帧，就只放首帧，尾帧当参考看。片子里大概只用切下去前后的 4–5 秒。

**手**：按以前的规矩，画面里不出现手（2026-11-11 Yancy 不喜欢生成的手）。所以提示词写的是「刀从画面上边进来，只看得到刀身和刀柄上端」。如果 Muse 生成的刀自己在动、看着别扭，再试最下面的 C（戴黑手套的手，只到手腕）。

---

## M01 · 从头切（10 秒）

**Prompt**

```
Static camera, locked off. A cozy sunlit living room. A hyperrealistic cake, sculpted and frosted to look exactly like a Shiba Inu puppy, lies curled up in a fluffy grey pet bed. It is a cake: it never moves, never breathes, its eyes stay closed, its fur does not stir.
After about two seconds, a large chef's knife comes down from the top edge of the frame — only the steel blade and the top of the black handle are visible, no hand, no arm — and slices slowly and cleanly straight down through the neck, just behind the head, all the way to the bottom of the bed.
The knife lifts out and away, and the head piece slides a few centimetres forward, revealing the inside: soft, moist golden vanilla sponge cake in even layers with thin white buttercream between them, wrapped in a thin fur-textured frosting shell only a few millimetres thick. A few cake crumbs fall onto the grey bed.
Realistic food-video look, like the reveal on the TV show "Is It Cake?", natural warm window light, shallow depth of field, no camera movement.
```

**Negative prompt**（Muse 有这一栏就填）

```
blood, red, pink flesh, meat, bone, gore, real animal, breathing, moving puppy, opening eyes, tail moving, hand, fingers, arm, person, text, watermark, cartoon, camera shake
```

## M01-B · 刀停在切口里（10 秒，备选）

```
Static camera, locked off. A cozy sunlit living room. A hyperrealistic cake, sculpted and frosted to look exactly like a Shiba Inu puppy, lies curled up in a fluffy grey pet bed. It is a cake: it never moves, never breathes, its eyes stay closed.
After about two seconds, a large chef's knife comes down from the top edge of the frame — only the blade and the top of the handle are visible, no hand — and slices slowly straight down through the neck, just behind the head. The knife stops, buried in the cut, and the cut opens slightly on both sides of the blade, showing golden vanilla sponge cake layers with white buttercream and a thin fur-textured frosting shell. A few crumbs fall.
Realistic food-video look, natural warm window light, shallow depth of field, no camera movement.
```

## C · 刀自己动着别扭时再试（有手）

把 M01 里的 "only the steel blade and the top of the black handle are visible, no hand, no arm" 换成：

```
held by a hand in a black kitchen glove that enters from the top edge of the frame, visible only up to the wrist
```

Negative prompt 里去掉 `hand, fingers, arm`。
