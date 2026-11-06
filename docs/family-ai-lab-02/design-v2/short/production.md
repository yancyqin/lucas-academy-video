# Can 0 and 1 Talk? · 剧情浓缩版

2026-11-06，用户要求在长片完成后制作浓缩剧情短视频，尽量多用 Muse。当前按推荐的 9:16 竖屏制作，1080×1920 / 30 fps，40.23 秒、1,207 帧。六条已保存的 Muse 原件全部使用，动态 Muse 画面 34.73 秒，占 86.3%。

默认英文配音，中文为独立音轨；每种语言各 8 条独立 SRT。画面使用简短英文剧情标签，不烧录旁白字幕、不留字幕条、不叠角落来源说明。

## 交付

- `out/family-ai-lab-02/orbital-v2/short/delivery/family-ai-lab-02.short.bilingual.mp4`
- 同目录 `en.srt`、`zh-Hans.srt`
- `out/family-ai-lab-02/orbital-v2/short/audio/en.m4a`、`zh.m4a`
- [中文文案](short-script.zh.md)、[English](short-script.en.md)、[时间线](short-timeline.json)、[素材区间](short-clips.json)、[成片检查](verification.json)

## 八个情节

| 时间 | 情节 | 画面 |
|---|---|---|
| 0–6.20 秒 | 纸条太大，邀请怎么送过去？ | G1b，先看纸条和接口，再跟到米娅的表情。 |
| 6.20–11.43 秒 | 两边约好：金色一，蓝色零。 | G1a，跟随金色信号，叠两个状态标记。 |
| 11.43–16.03 秒 | Yes！邀请到了：PLAY。 | G2，里奥的反应；四个字母按各自八位编码出现。 |
| 16.03–20.63 秒 | 十个箱子里藏着礼物。 | G3，走向货舱。 |
| 20.63–25.03 秒 | 四个回答，找出七号箱。 | 准确的十箱和四问动画，依次保留 5 → 3 → 2 → 1 个候选。 |
| 25.03–30.03 秒 | 是西瓜，轮到里奥回信。 | 先听到答案，再接 G4 举起、咬西瓜的动作。 |
| 30.03–35.83 秒 | 按下 Send，发回「收到」。 | G5，保留按键后抬头微笑的动作；金色回程信号叠在画面下部。 |
| 35.83–40.23 秒 | 换你，会给朋友说什么？ | G4 后段继续吃西瓜，带开放问题和课程二维码。 |

主画面来自七段连续向前的素材区间。G4 分为两个互不重叠的区间，始终从前往后；其余各用一个区间。选定画面不循环或倒放。镜头按实际中英文语音时长适配，速度约 1.0–1.34 倍；配音使用完整原始 take，未拉伸。竖屏取景分别跟随纸条、信号和角色，保留关键动作。

## 声音

16 条选用语音中，4 条直接复用长片已核对的开头和回信；其余 12 条为短片重写。Louise 默认速度 1.1，复用的英文首句为 1.0。共保留 15 个新原始 take，包含中文两次重写的候选，均有文字、设置及 SHA256。

英文 screen says play 和中文颜色数字用 medium 听写复核。中文接收句改为「可以！邀请送到了。一起玩吧！」，找箱子句改为「四个回答，七号箱找到了！」，避免不清楚的人名与术语。原始听写和逐条选用决定见 [short-asr.json](short-asr.json)、[short-asr.medium.json](short-asr.medium.json)、[short-voice-review.json](short-voice-review.json)。

音乐沿用原创电子和弦与脉冲配方，逐句使用仓库 ducking：语音下低 20 dB，至少 0.8 秒空隙低 9 dB，提前 0.35 秒退下，0.8 秒恢复。原 Muse 声轨静音，另外加入到达、回答提示音。两条混音目标为 −16 LUFS / −1 dBTP，最终 AAC 测量记录在 [verification.json](verification.json)。

## 来源与重建

原件、imagegen 场景、课程事实和二维码沿用长片的已归档输入。[主制作记录](../orbital-production.md)、[六条 Muse 原件](../clips.json)。来源和生成记录留在文档中；画面没有角落署名。短片使用独立输出目录，验证时另核对长片 SHA256，确保长片保持原交付。

恢复数据备份后，可直接使用选定 WAV 重建：

```sh
npm run fal02:short:build
npm run fal02:short:mix
npm run fal02:short:stills
npm run fal02:short:final
npm run fal02:short:check
npm run fal02:backup
```

重录才需要私有 Louise profile；正常重建无需再生成 Muse 素材或语音。全部原始短片配音单独保存在数据备份的 `raw-narration-short/`，附设置与 SHA256SUMS。恢复核对见 [backup.json](backup.json)。

实际成片已通过：1,207 帧、双 AAC 默认标记、零字幕轨、无黑场。英语为 −16.13 LUFS / −0.98 dBTP，中文 −16.04 LUFS / −0.99 dBTP。末尾课程二维码在原分辨率和 720 像素宽版本均可解码。混音后的整段英语用 medium 听写逐词核对，含开头、Yes、颜色数字、四问与七号箱；仅数字格式及标点作归一化。长片 SHA256 保持原交付。
