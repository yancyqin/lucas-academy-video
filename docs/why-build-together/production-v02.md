# 家长介绍片 · 制作 v02

日期：2026-11-22。片名：孩子做项目，我们真正看重什么？

本版执行主人最新四项修订：项目原片播完即结束，删除“05 合作与陪伴”；重做信息内容句的配音；Muse 镜头改为白底铅笔素描；新增画面标签使用中文在前、英文在后的相同字号双语排列。v01 成片、文案和代码快照保留。

## 文案与时间线

正式文案为 [zh-script-v03.md](zh-script-v03.md)，生成规格为 [approved-script-v02.json](approved-script-v02.json)。共有 12 段引子旁白，原来的 n013–n015 不进入新片。

- 引子：116.533 秒，3,496 帧。
- 完整项目原片：283.800 秒，8,514 帧，原速播放。
- 总长：400.333 秒，12,010 帧，约 6 分 40 秒。
- 原片最后一帧就是新片最后一帧，不追加结尾。

实际时间线：`out/why-build-together-v02/timeline.json`。章节和中文字幕按新时间线重排。

## 配音修复

主人指出的句子是：“游戏、图片、短视频，要多少有多少。但这些内容，能给孩子带来什么？”

v01 的 Qwen 原始演绎和 Louise 换声都是 11.28 秒，说明换声没有将这句拉慢。原始演绎将列举词读得较长，词间数处停顿约 0.4 秒，两句之间约 0.76 秒。

仅为这句重新生成本地 Qwen3-TTS 1.7B CustomVoice 8-bit 演绎，要求连贯列举、短暂停顿，再用既有 Louise 中文参考作本地 CosyVoice3 换声。新演绎及换声均为 7.20 秒，没有通过变速压缩。TTS 输入简化了标点，正式文案和字幕的文字不变。独立 Whisper.cpp 转写覆盖整句，另用本地 Whisper-small 对齐字幕。

其余 11 段 Qwen 和 Louise 音频均与 v01 逐文件哈希一致。修复记录：`out/why-build-together-v02/n008-repair.json`。本版没有调用云端配音。

## 画面与标签

本版沿用已有 Muse 镜头的动作，将 G01–G05 转为白底石墨铅笔效果；G06 随结尾删除而不再使用。影像采用灰度、局部亮度素描和固定纸面交叉排线，低亮度区域作柔化，避免黑衣物成为大块纯黑。影像保持原速及十秒时长，不重新生成镜头。

需求金字塔、认可例子、内容流和构思线条继续采用黑底白线动画，保留重点层的淡色强调。新增镜头的字改用深色，避免白底上失去对比。

新增标签集中在 `src/videos/why-build-together-v02/labels.json`。每组由共同 `Pair` 组件依次放置中文和英文，两行继承相同字号、字重和字体。品牌专名 `Lucas Academy` 保留原名。既有九项目影片内的画面标签不改。

逐段静帧同时读取实际浏览器排版，35 组新增双语标签均通过中文在前、字号和字重一致、文字不溢出及边界位于画面内的核对。结果见 `delivery/label-check.json`。构思动画的关键词提前出现，使最后的“带领与合作 / Leadership & teamwork”留有约三秒阅读时间。

## 原片、字幕和配乐

原片仍使用本机 1080p 原版：`/Users/yqin/repo/playground/lucas-academy-video-data/curiosity-builds-20261118/v10/delivery/curiosity-builds.en.no-voice.mp4`。

原片 27 条中文字幕按 116.533 秒的插入点整体平移，保留文字和相对时序。新片共 53 条中文字幕，交付默认中文软字幕轨及独立 SRT/VTT。`打开预览.html` 默认开启中文字幕，不将字幕烧入成片。

引子配乐和避让策略沿用 v01，随新旁白时间线重算；项目段保留原配乐和音量。上传描述首行仍从 `0:00` 开始列出完整真实章节，后接介绍、来源及署名。本次没有上传或修改已发布影片。

## 重建与验收

```bash
../lucas-academy-media/.venv-tts-comparison/bin/python scripts/why-build-together-v02/narrate.py tts --only n008
../lucas-academy-media/.conda/bin/python scripts/why-build-together-v02/narrate.py vc --only n008
.venv-align/bin/python scripts/why-build-together-v02/check_voice.py
.venv-align/bin/python scripts/why-build-together-v02/align.py
.venv-align/bin/python scripts/why-build-together-v02/prepare.py
.venv-align/bin/python scripts/why-build-together-v02/assets.py
node scripts/why-build-together-v02/render.cjs
.venv-align/bin/python scripts/why-build-together-v02/deliver.py
.venv-align/bin/python scripts/why-build-together-v02/verify.py
node scripts/why-build-together-v02/verify-player.cjs
```

最终完整解码、字幕一致性、原片抽帧对照、素描亮度和连续动作检查以 `delivery/verification.json` 为准；浏览器字幕与实际播放记录见 `delivery/player-check.json`，不将自动识别等同于全片人工逐秒听审。

本版验收已通过：全片解码 12,010 帧，53 条内嵌中文字幕与 SRT 一致，原片 27 条字幕保留，14 个章节与新时间线一致。六处原片画面对照（含末尾）平均像素差均低于 0.1 / 255。五段素描均为明亮纸面及中性灰度，连续动作检查通过。浏览器实际播放旁白段、项目段及结尾，确认默认中文字幕显示，并播放至 400.333 秒正常触发结束。

交付目录：`/Users/yqin/repo/playground/lucas-academy-video-data/why-build-together-20261122/v02/delivery/`。源代码和本轮文案快照存于同版 `source-snapshot/`。
