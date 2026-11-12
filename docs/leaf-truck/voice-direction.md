# 一片落叶 · 配音说明（v0.1，2026-11-11）

声音：Yancy 选定中英文都用 Louise（11-11 「都用 Louise」）。

- **中文**：louise/zh，zero-shot-instruct，所有句子 1.1 倍。
- **英文**：louise/en，zero-shot-instruct，所有句子 1.1 倍。

基准语气全片只用一种，沿用《你爱听 AI 说是的吗》：

- 中文：请用真诚、温暖、有感情的语气，像跟朋友、跟家长聊天那样说。
- 英文：Speak in a sincere, warm, heartfelt voice, like talking with friends and parents about something you care about. Natural pace.

问观众的话要读得好奇，不能像在责备，靠标点和留白做到，不换语气指令：

- lf02-05、lf04-04、lf06-01、lf07-02、lf07-04、lf07-06 这几句后面留 1.2 秒以上的安静。
- lf04-04 问完之后，画面停住让观众猜，至少再留 2 秒。

## 实际念的字（字幕不变）

| 句 | 字幕 | 实际念 | 原因 |
|---|---|---|---|
| lf07-02 | 下落太快 | 下洛太快 | 落是多音字 |
| lf04-06、lf06-04（英） | lidar | lie-dar | 避免逐个字母念 |

## 为了念准，稿子做过的改动

**中文**
- 「急刹」改「急刹车」：Whisper 把「急刹」听成「击杀」。
- 「每刹一次」改「每一次急刹车」：Louise 把刹读成 chà。
- 「为人停的」改「因为人停的」：为字两读。
- 「调得迟钝」改「别那么敏感」：调字两读。
- 「车得分清」改「车要分清」：得字两读。
- 「归为」改「当作」：为字两读。

**英文**
- "route" 改 "trip / street"：被读成 "root"。
- "braked" 改 "hit the brakes"：被听成 "break"。
- "missed" 改 "did not see"。
- 否定词一律写全，用 cannot / could not / did not。

## 复用的试音

LF01、LF02 共十句直接用 11-11 的试音（out/leaf-truck/voice-test/louise-{zh,en}），不重配。

## 每句都要核对

- 用 Whisper medium 听写，和稿子逐字比对。
- 句子之间不能多出额外的字词。
- 句尾不能多出含糊的尾音。
- 开头不能有咔哒声。
