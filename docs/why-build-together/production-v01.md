# 家长介绍片 · 制作 v01

日期：2026-11-22。片名：孩子做项目，我们真正看重什么？

主人已授权应用顺句建议并制作完整视频。使用修订后的 `zh-script-v02.md`，中间完整嵌入九项目影片，展示后直接回到合作、负责、同伴与共同兴趣的结尾。

## 时间线

- 引子与理念：120.600 秒。
- 九项目原片：283.800 秒，原速、完整长度。
- 收束与邀请：30.167 秒。
- 总长：434.567 秒，约 7 分 15 秒；1920 × 1080，30 fps。

实际逐段时间线：`out/why-build-together-v01/timeline.json`。

## 文案与旁白

按主人确认顺好“内容能给孩子带来什么”“一点一点把作品做出来”、运动及音乐例子的词序，并将最后长段拆为三句。原稿中已不再使用的晚年马斯洛资料注记已删除。

中文旁白使用本地 Qwen3-TTS 1.7B CustomVoice 8-bit 生成演绎，再用本地 CosyVoice3 转为既有 `louise/zh` 音色。每段保留 Qwen 原始录音、Louise 转换、文本和来源哈希；换声临时加入首尾各一秒的上下文后按原时长移除，没有加快或拉长旁白。

15 段录音均作有限性、非空音频、峰值和独立 Whisper.cpp 转写检查。中文字幕使用缓存的本地 Whisper-small 对照批准文字作时间对齐；对齐本身不作为实际说出所有文字的独立证据。

开场前约 24 秒为纯旁白。之后的配乐沿用九项目片已经记录出处的 Jeannette Fang《雨滴》CC0 录音，并使用仓库 `music_ducking.py` 随旁白避让。项目展示段沿用原配乐。

## 新增影像

Muse 侧聊：`Lucas Academy video generation request`。完整请求见 [muse-request-v01.txt](muse-request-v01.txt)。六条均为本次新生成的独立镜头，原始视频 1280 × 720、24 fps、10 秒；交付附件已去除生成器附带的音轨。下载 originals 保存于 `out/why-build-together-v01/muse/`。

| 镜头 | 内容 | 使用说明 |
| --- | --- | --- |
| G01 | 现代人的布袋与古代山坡 | 现代衣着与古代环境形成穿越设定；人群仅为示意。 |
| G02 | 分享面饼 | 保留完整递食物动作，预算文字置于上方，避开手部。 |
| G03 | 同伴让出座位 | 表现接纳与共同兴趣；桌上彩色玩具为概念场景道具。 |
| G04 | 零食包装传送带 | 稍作绿色中间调校正，连接信息供给的比喻。 |
| G05 | 家长与孩子讨论草图 | 保留正常色彩，并另外制作局部白色轮廓、黑色背景的版本。 |
| G06 | 孩子共同搭建模型 | 表现合作与成人陪伴；不宣称是实际学生课堂记录。 |

已查看六条镜头在约 1、5、9 秒的画面，核对主要人物、手部、物品与动作。原生 24 fps 影像在原分辨率上作运动估计插帧，再放大至 1080p、30 fps，保持原速与十秒时长。转换参数、哈希和原图检查帧存于 `assets.json`、`assets/` 和 `muse-contact.jpg`。

需求金字塔、认可例子、内容流和构思线条使用可控动画。家庭黑白插画复用长期记忆视频的既有原创 `family-grid.png`，加上新的绘制动作；没有把此插画标成新生成的 Muse 录像。

## 原片与字幕

原片：`/Users/yqin/repo/playground/lucas-academy-video-data/curiosity-builds-20261118/v10/delivery/curiosity-builds.en.no-voice.mp4`。

原中文字幕：同目录 `curiosity-builds.en.no-voice.zh-CN.srt`，27 条，时间整体加上 120.600 秒。

新片中文字幕既包含新旁白，也包含展示段英文标签的中文翻译。采用默认中文软字幕轨，并另外交付 SRT/VTT；不烧录字幕。`打开预览.html` 使用默认开启的 VTT 字幕，供浏览器直接观看。

## 重建

```bash
../lucas-academy-media/.venv-tts-comparison/bin/python scripts/why-build-together/narrate.py tts
../lucas-academy-media/.conda/bin/python scripts/why-build-together/narrate.py vc
.venv-align/bin/python scripts/why-build-together/align.py
.venv-align/bin/python scripts/why-build-together/prepare.py
.venv-align/bin/python scripts/why-build-together/assets.py
node scripts/why-build-together/render.cjs
.venv-align/bin/python scripts/why-build-together/deliver.py
.venv-align/bin/python scripts/why-build-together/verify.py
node scripts/why-build-together/verify-player.cjs
```

渲染结果位于 `out/why-build-together-v01/delivery/`。最终验收记录以该目录 `verification.json` 为准。所有 YouTube 描述均先列真实时间线章节，再放介绍、来源、署名与标签；本次不上传或修改已发布影片。

## 交付与验收

首版已完成。总长 434.567 秒，1920 × 1080，恒定 30 fps，完整解码 13,037 帧通过。AAC 编码尾部补样已按段的准确样本数截齐，旁白和原片保持原速。

验收核对 60 条中文字幕的外部 SRT 与 MP4 默认字幕轨一致，其中原片 27 条字幕保留原文和相对时间。新片 16 个章节写入 MP4，描述首行从 `0:00` 开始，并按真实播放顺序列出全部章节。项目段在五处抽帧对照原片，灰度像素平均差均小于 0.1 / 255；六段 Muse 标准化镜头以及成片开场和绘制动画均检查了连续帧的动作。全片音频有限、非空，无检测到的削波。

浏览器预览另外检查旁白段与项目段的默认字幕、实际播放和画面尺寸，结果见 `player-check.json`；画面抽检记录见 `final-contact.jpg`。以上为完整解码、字幕一致性及画面抽检，未将自动转写或文字对齐视作全片人工逐秒听审。

完整交付和素材归档：`/Users/yqin/repo/playground/lucas-academy-video-data/why-build-together-20261122/v01/`，其中 `delivery/打开预览.html` 默认显示中文字幕，`delivery/why-build-together.zh-v01.mp4` 为成片。`source-snapshot/` 保存本次文案和制作代码。
