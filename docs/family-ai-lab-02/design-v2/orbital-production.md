# 小管子的消息 · 深空隔舱审核版

当前交付为 **Can 0 and 1 Talk? / 0和1，能聊天吗？**，4:24.73、7,942 帧、1920×1080 / 30 fps。六条用户在 Muse 手动生成的单镜头全部接入。开场先放 7.5 秒米娅塞纸条，22.4 秒再放 1.8 秒管内发射，24.2 秒回到教学画面，先说 “Yes!”／「可以！」再讲解。教学部分继续使用同一隔舱材质和光色，数字、字母、珠子、箱号与问题树由代码绘制。

英文开头原为 “The note won't fit! How can Mia invite Leo to play?”，用户反馈不清楚。现为 “This note is too big. How can Mia invite Leo to play?”，用 1.0 速度重新生成，5.4 秒，短句后留停顿。发射后的首句重录为 “Yes! Start with one little ball. It has just two possible values.”，中文对应「可以！先看一颗珠子。它只有两种可能。」。英语 Yes 在这一句最前面，约 0.42 秒，随后约半秒停顿，再开始说明。

其余 69 条选用配音（包括 35 条中文）文件不变；S2–S8 除新增肯定回答的第一句外，31 条镜头内容与时长均保留。对比证据见 [opening-revision.json](opening-revision.json)。

英文音轨默认播放，中文为独立音轨。画面使用简短英文标签，不烧录字幕、不留字幕条、不叠右下角来源或版权说明。中英文 SRT 各 36 条，单独交付。

## 当前文件

- 全片：`out/family-ai-lab-02/orbital-v2/delivery/family-ai-lab-02.bilingual.mp4`
- 开头预览：同目录 `opening-yes.mp4`，完整 S1 加肯定回答和第一句讲解，30 秒 / 900 帧，720p，保留两条音轨；文件名区分上一次审核片。
- 独立音轨：`out/family-ai-lab-02/orbital-v2/audio/en.m4a`、`zh.m4a`
- 独立字幕：交付目录的 `en.srt`、`zh-Hans.srt`
- 实际成片检查：[orbital-verification.json](orbital-verification.json)
- 当前文本：[English](orbital-script.en.md)、[中文](orbital-script.zh.md)
- 素材与许可：[credits.md](credits.md)
- 中英文封面：`out/family-ai-lab-02/orbital-v2/cover/family-ai-lab-02.en.png`、`family-ai-lab-02.zh.png`，1280×720，均小于 2 MB。

## 首帧封面

用户明确确认的标题为 **0和1，能聊天吗？ / Can 0 and 1 Talk?**。两张封面均直接解码最终影片的第 0 帧，只等比缩放至 1280×720。右上方用代码排标题，留出米娅的脸、手和纸条；文字区域以外与原帧缩放图逐像素相同。不另生成底图、不改构图、不加系列条。标题卡同步用英文标题。原帧、成品 SHA256、字体和文字边界见 [cover.json](cover.json)。

42 秒无声 `style-study.mp4` 保留为先前的风格审核片，已去掉角落标注。旧 `out/family-ai-lab-02/delivery/` 属于绘本版历史参考。

## 六条剧情镜头

完整原件保存在 `public/family-ai-lab-02/muse-v2/`，每条均记录原始 SHA256、尺寸、帧率、实际时长与动作观察。原始生成声轨不进入成片。详见 [clips.json](clips.json)。

| 镜头 | 原件时长 | 使用的原片范围 | 处理与插入位置 |
|---|---:|---|---|
| G1a 信号 | 10 秒 | 0.8–6.6 秒 | 单向压缩为 1.8 秒，放在 22.4–24.2 秒，两种语言的问题均已讲完。 |
| G1b 纸条 | 10 秒 | 0.2–7.7 秒 | 不变速，作为开头完整播放 7.5 秒；先纸条受阻，再看到女孩的反应。 |
| G2 接收 | 6 秒 | 1.0–6.0 秒 | 避开开头重构，32 比特全部到达后，男孩看到邀请。 |
| G3 货舱 | 6 秒 | 0.2–6.0 秒 | 男孩走向关闭的箱子，随后切准确的十箱动画。 |
| G4 西瓜 | 10 秒 | 0.2–5.2 秒 | 实际动作包含举起与咬西瓜；必须等水果答案讲完才出现。 |
| G5 回信 | 10 秒 | 0.0–2.4 秒 | 只取清楚的按键动作，随后代码画金色信号反向返回。 |

编辑副本统一为 1080p/30 fps、仅视频。每条仅一个向前片段；旁白较长时停在该片段最后一张真实帧，不倒放、不循环。实际时间线及所有副本 SHA256 见 [story-clips.json](story-clips.json) 与 [orbital-timeline.json](orbital-timeline.json)。

## 配音与声音

Louise，默认速度 1.1，本次重录的英文首句为 1.0。72 条选用配音中，61 条与 v1 文件完全相同；11 条用于隔舱改写和明确的肯定回答。开场保持轻快和好奇，讲解用原来较平稳的语气。首句在米娅镜头开始后 0.4 秒进入，发射及音效后置到 22.4 秒，肯定回答在 24.3 秒进入。

本轮共保留 14 个新原始 take，包括本次重新录制的英文首句，以及新增肯定回答的中英文句子。中文「管道连接」与「收到啦」采用第二版措辞，避免听写中细管／吸管、人名等歧义。所有选用决定和原始小模型听写均保存，有歧义的人名另保留 medium 听写。中文新句的 棵／颗、猪／珠 为同音转写，保留原听写和正确字幕。记录见 [orbital-voice-review.json](orbital-voice-review.json)、[orbital-asr.json](orbital-asr.json) 和 [orbital-asr.medium.json](orbital-asr.medium.json)。

统一画面容纳两种语言中较长的实际语音，不拉伸或截断旁白。G4 的五秒剧情发生在水果答案的语音之后。

新版配乐由 `orbital_mix.py` 合成固定和弦、轻电子脉冲、管道飞掠、八位收齐与回答提示音。配方可重建。音乐遵循仓库逐句 ducking：语音下低 20 dB，至少 0.8 秒空隙低 9 dB，提前 0.35 秒退下，0.8 秒恢复。最终 MP4 中英语 AAC 为 -16.05 LUFS、-0.97 dBTP，中文为 -16.06 LUFS、-0.95 dBTP；无削波。

## 检查

实际成片验证了 7,942 帧、两条 AAC 时长、英语默认标记、零字幕轨和零黑场。开场顺序另核对了纸条在第 0 帧、发射在问题语音之后、紧接发射先肯定回答再讲解。课程二维码在实验室、学习单和片尾三处，均从最终影片的 1080p 帧及缩小到 720p 的帧解码成功。

13 个冻结课程输入、13 张设计与制作原图、72 条选用语音及明确选用决定的 SHA256 全部通过。36 对字幕与本轮文字一致。十箱路径为 5 → 3 → 2 → 1，PLAY 接收按真实到达的 32 颗信号更新；水果答案之后才露出真实西瓜。36 个关键画面已逐页检查，TypeScript、Node 语法和 diff 检查通过。

## 重建与备份

当前合成是 `FamilyAiLab02Orbital`、`view: full`。从数据备份恢复后，使用现成配音和剪辑副本重建：

```sh
npm run fal02:orbital:build
npm run fal02:orbital:mix
npm run fal02:orbital:full:stills
npm run fal02:orbital:final
npm run fal02:orbital:opening
npm run fal02:orbital:cover
npm run fal02:orbital:check
npm run fal02:backup
```

`fal02:orbital:clips` 仅在需要从 Muse 原件重做编辑副本时使用。恢复后的正常重建无需再次生成图片、视频或配音。`fal02:orbital:preview` 是 42 秒旧样片；`fal02:final` 是绘本版，不是当前交付。

备份位置：`../lucas-academy-video-data/family-ai-lab-02/`，含六条完整 Muse 原件、所有原图、选用 WAV、v1/v2 全部原始 take 与设置、课程输入及制作记录。附 SHA256SUMS 和整批预检、拒绝覆盖不同目标文件的 `restore.py`。视频与媒体不提交 Git。恢复核对记录见 [orbital-backup.json](orbital-backup.json)。
