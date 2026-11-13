# Challenge · 竖屏短视频（2026-11-12）

Yancy：「出短视频吧」。两条竖屏短视频，每条就是片子里的一组，挑两个 AI **都被骗**的那两组：

| 短视频 | 组 | 真的 | AI 画的 | 两个 AI |
|---|---|---|---|---|
| `blue-mormon` | 第 2 组 | 蓝摩门凤蝶（B，下面那张） | 钩粉蝶（A，上面那张） | 都选了 A，都错 |
| `leopard` | 第 4 组 | 豹纹蛱蝶 / 琶蛱蝶（A，上面那张） | 斑点木蝶（B，下面那张） | 都选了 B，都错 |

格式照「动物想什么？AI 知道吗？」的短视频：1080×1920，英文视频 + 中文音轨 m4a，字幕不烧进画面（en、zh-Hans 两个 SRT），每句一个时段（中英两条里长的那条）。画面照正片：图标多、字少，英文大、中文小，不署名。

**每条的节奏（约 30 秒）**

1. 顶上一直是问题：「Which One Is Real?」，下面小字「哪只是真的？」。两张图上下排，旁白 sh-intro。
2. 倒数 5 秒，不说话。
3. 公布：真的打绿勾，AI 打红叉；两个 AI 的小机器人放在它选的那张上；公布句。
4. 真视频放在中间一条（上下是它自己的模糊副本），下面是名字（英文大、中文小），讲这只蝴蝶的那句。
5. 音乐：肖邦 Op. 18 的开头一段，人声进来就让。

**旁白**（中英都是 Louise 1.1，正片的基准语气）

- sh-intro（新）｜一只是真的，一只是 AI 画的。你来猜：哪只是真的？
  > One is real, one was drawn by AI. Your turn: which one is real?
- 第 2 组：公布 = 正片 sc02-01「最厉害的 AI 大模型，也都被骗了……Fable 还说，真的这只翅膀中间有一条奇怪的花纹，不像真蝴蝶。」，介绍 = sc02-02，都用正片的那条配音。
- 第 4 组：正片 sc04-01 开头是「又是两个都错」，单独放不通，所以新配一句：
  - sh04-01（新）｜两个 AI 都选错了！AI 这张每个细节都清清楚楚，Fable 反倒嫌真的这只身子糊成一团。
    > Both AIs got it wrong! Every detail of the AI one is crisp, and Fable even said the real one's body was a smeared blob.
  - 介绍 = 正片 sc04-02。

脚本：`scripts/butterfly-challenge/narrate_shorts.py`（两句新的）、`build_short.py`、`render_short.py`、`package.py --shorts`；Remotion 合成 `ButterflyShort`。

**交付（2026-11-12）**：桌面「猜一猜哪些蝴蝶是真的-竖屏短视频-上传」：两条各一个英文 mp4（32 秒、33 秒）、中文音轨 m4a、en 和 zh-Hans 两个 SRT、中英上传文字（标题带 #shorts，简介写完整版的名字、这一条用的照片和视频出处）。配音：sh-intro 中英都一次过；sh04-01 中文第一条「真的这只」的「这」太弱（强制解码只高 0.9），在「真的这枝」两边加逗号重配，这次高 8.6；「糊」的音高比正片那条还更接近第二声。Whisper 查过两条成片的两条音轨。
