# Can 0 and 1 Talk? · 剧情浓缩版

2026-11-06，用户确认 9:16 竖屏，要求尽量多用 Muse，并把结尾延伸到互联网、AI 和「今天你想分享什么」。当前 1080×1920 / 30 fps，56.90 秒、1,707 帧。六条已保存的 Muse 原件全部使用，动态 Muse 画面 51.40 秒，占 90.3%。原 40.23 秒版本的前七段和 14 条选用配音保持不变。

默认英文配音，中文为独立音轨；每种语言各 11 条独立 SRT。画面使用简短英文剧情标签，不烧录旁白字幕、不留字幕条、不叠角落来源说明。

## 交付

- `out/family-ai-lab-02/orbital-v2/short/delivery/family-ai-lab-02.short.bilingual.mp4`
- 同目录 `en.srt`、`zh-Hans.srt`，以及新结尾审核片 `ending-internet-ai.mp4`
- `out/family-ai-lab-02/orbital-v2/short/cover/family-ai-lab-02.short.en.png`、`.zh.png`：1080×1920 竖屏封面，桌面交付为 `03-封面/Shorts-英文封面.png` 与 `Shorts-中文封面.png`
- 桌面 `0和1能聊天吗-交付/02-竖屏短片/`：完整短片、结尾审核片、独立字幕和从最终影片无损提取的中英文 M4A
- [中文文案](short-script.zh.md)、[English](short-script.en.md)、[时间线](short-timeline.json)、[素材区间](short-clips.json)、[成片检查](verification.json)

## 剧情与结尾

| 时间 | 情节 | 画面 |
|---|---|---|
| 0.00–6.20 秒 | 纸条太大，邀请怎么送过去？ | G1b，先看纸条和接口，再跟到米娅的表情。 |
| 6.20–11.43 秒 | 金色一，蓝色零。 | G1a，跟随金色信号，叠两个状态标记。 |
| 11.43–16.03 秒 | Yes！邀请送到了。 | G2，里奥的反应；四个字母按各自八位编码出现。 |
| 16.03–20.63 秒 | 十个箱子里藏着礼物。 | G3，走向货舱。 |
| 20.63–25.03 秒 | 四个回答，找出七号箱。 | 准确的十箱与四问动画，依次保留 5 → 3 → 2 → 1 个候选。 |
| 25.03–30.03 秒 | 是西瓜，轮到里奥回信。 | 先听到答案，再接 G4 举起、咬西瓜。 |
| 30.03–35.83 秒 | 按下 Send，发回「收到」。 | G5，金色回程信号。 |
| 35.83–39.53 秒 | 小管子连起两个朋友。 | G1b 尚未使用的尾段，加两个人之间的信号。 |
| 39.53–43.10 秒 | 互联网连起全世界。 | G1a 尾段，加动态网络球和零、一数据包。 |
| 43.10–48.50 秒 | 视频、消息、AI 聊天都用零和一。 | G5 尾段，三个简短英文标签；图形避开角色脸部。 |
| 48.50–56.90 秒 | 好玩的故事？新游戏？今天分享什么？ | G4 后段继续吃西瓜，带开放问题和课程二维码。 |

主画面来自十段连续向前、互不重叠的素材区间。新增结尾使用既有原件中尚未使用的尾段；没有再生成或保存 Muse 原件。画面不循环或倒放，速度约 0.52–1.34 倍。结尾部分使用缓慢动作，适配较长的中文问题；配音使用完整原始 take，不拉伸语音。

结尾英文：

> Our tiny pipe connects two friends. The internet connects the world! Videos, messages, even chats with AI—all use zeros and ones. A funny story? A new game? What will you share today?

中文：

> 两个朋友，就用小管子传话。互联网连起全世界！视频、消息、AI聊天，全都用零和一。一个好玩的故事？一个新游戏？今天你想分享什么？

中文实际读「人工智能聊天」，外置字幕保留短写 AI。这里用小管子的故事连接到数字通信，没有声称真实互联网经过同一根管道。

## 声音

22 条选用语音中，4 条直接复用长片已核对的开头和回信；其余 18 条是短片专用。Louise 默认速度 1.1，复用的英文首句和新版英文末句为 1.0。共保留 26 个新原始 take，包括未选候选，均有文字、设置及 SHA256。

新增结尾逐条核对听写，英文 AI 句用 medium 确认完整的「all use zeros and ones」，AI 被识别为一个简短的连续词，未加字母间隔。中文两句重写为清楚的「两个朋友，就用小管子传话」和「视频、消息、人工智能聊天，全都用零和一」。英文末句另录，放慢三个问题的节奏。原始听写保留标点、数字格式、繁简及同音字差异：[small](short-asr.json)、[medium](short-asr.medium.json)、[选用决定](short-voice-review.json)、[结尾修改记录](ending-revision.json)。

音乐沿用原创电子和弦与脉冲配方，逐句使用仓库 ducking：语音下低 20 dB，至少 0.8 秒空隙低 9 dB，提前 0.35 秒退下，0.8 秒恢复。原 Muse 声轨静音，另外加入到达、回答提示音。两条混音目标为 −16 LUFS / −1 dBTP；实际成片值见检查记录。

## 来源与重建

原件、imagegen 场景、课程事实和二维码沿用长片的已归档输入。[主制作记录](../orbital-production.md)、[六条 Muse 原件](../clips.json)。来源和生成记录留在文档中。短片使用独立输出目录，验证时另核对长片 SHA256。

恢复数据备份后，可直接使用选定 WAV 重建：

```sh
npm run fal02:short:build
npm run fal02:short:mix
npm run fal02:short:stills
npm run fal02:short:final
npm run fal02:short:check
.venv-align/bin/python scripts/family-ai-lab-02/short_cover.py
python3 scripts/family-ai-lab-02/youtube.py
python3 scripts/family-ai-lab-02/deliver.py
npm run fal02:backup
```

重录才需要私有 Louise profile；正常重建无需再生成 Muse 素材或语音。全部原始短片配音单独保存在数据备份的 `raw-narration-short/`，附设置与 SHA256SUMS。[恢复核对](backup.json)。

Shorts 封面沿用已确认片名：**Can 0 and 1 Talk? / 0和1，能聊天吗？**。中英文各一张，1080×1920。底图直接取最终竖屏视频第 0 帧，标题放在上方空位，手、纸条与管口所在区域保持原画面。[封面记录](cover.json)。

YouTube 长片与 Shorts 各有中英文标题、简介和 tags，默认标签来自 `scripts/youtube_tags.py`。文案是同一影片的语言本地化资料：[English long](../../youtube/long.en.txt)、[中文长片](../../youtube/long.zh.txt)、[English Shorts](../../youtube/short.en.txt)、[中文 Shorts](../../youtube/short.zh.txt)。

实际成片核对：1,707 帧、双 AAC 默认标记、零字幕轨、每语言 11 条外置字幕、无黑场。英语 -16.17 LUFS / -0.95 dBTP，中文 -16.00 / -0.98。二维码在原尺寸和 720 像素宽版本均可解码。最终英语 AAC 的 11 条旁白经 medium 复核，归一化标点与数字格式后逐词一致；原始整轨 ASR 在配乐尾段多识别一个 you，原样保留并注明旁白实际结束时间：[成片听写](mixed-asr.en.json)。长片与两张封面保持原交付。
