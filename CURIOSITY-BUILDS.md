# Curiosity Builds：清理媒体前的制作归档

归档日期：2026-11-21（America/Los_Angeles）。

**这支片子是在 `lucas-academy-video` 中制作的。** 桌面 `Curiosity Builds - Final`
是交付副本，工作素材在仓库旁的 `lucas-academy-video-data/curiosity-builds-20261118`。
归档时，仓库已有 `scripts/curiosity-builds*` 和 `src/videos/curiosity-builds*` 的
v1–v10 文件，但全部尚未加入 Git；仅推送原来的分支不会保存它们。
本次把这些小型源文件和制作记录提交进仓库。

用途是保留经验，并给可能的重做留下线索。**归档只有文字和代码，没有媒体备份；
删除媒体后，不能仅凭这个仓库原样恢复成片。** ImageGen 图片需要重新生成，
真实项目需要重新录制，私人原始素材需要另外找回或替换。
本次没有重渲染、下载素材、发布视频或删除文件。

## 从哪里看起

| 内容 | 位置 |
| --- | --- |
| 制作经验与失败原因 | [lessons.md](docs/curiosity-builds/lessons.md) |
| 重做的前提、素材对应关系和步骤 | [rebuild.md](docs/curiosity-builds/rebuild.md) |
| 归档目录与历史记录的可信范围 | [归档索引](docs/curiosity-builds/README.md) |
| 最终分镜、问题、片长、转场和音乐分组 | [v10 plan.json](scripts/curiosity-builds-v10/plan.json) |
| 最终标题动画和概念示意画面 | [v10 Film.tsx](src/videos/curiosity-builds-v10/Film.tsx) |
| 最终拼接、配乐、字幕和校验脚本 | [scripts/curiosity-builds-v10](scripts/curiosity-builds-v10) |
| 实际输入、软链接链路、媒体 SHA-256 | [media-inventory.json](docs/curiosity-builds/media-inventory.json) |
| 中英发布文案、标签与上传设置 | [youtube.json](docs/curiosity-builds/youtube.json) |
| 主片及各段中文字幕 | [delivery](docs/curiosity-builds/delivery) |

## 最终交付是什么

v10，1920×1080，30 fps，**8514 帧 / 283.8 秒**。英文画面文字，无配音；
音轨只有配乐，中文字幕为 27 条可选 SRT。九段项目各有独立版本，另有 18 秒片尾预览。
每段先用问题和概念示意介绍，再进入实际项目录像。

清理前重新读取了桌面主片的流信息和文件哈希：

```text
文件：Curiosity Builds.mp4
大小：195986936 bytes
视频：H.264 / 1920×1080 / 30 fps / 8514 frames
音频：AAC / 48000 Hz / stereo
SHA-256：08a4eb9c5f54e1d3892e538dab74dd8e1f16e470da92d5726e3f6bd7e8551198
```

| 起点 | 项目 | 时长 |
| --- | --- | --- |
| 00:00.000 | Balanced Chess | 38.2 s |
| 00:38.200 | Bible Sequence / Next Word | 31.2 s |
| 01:09.400 | Van Gogh House | 27.2 s |
| 01:36.600 | Journey of Art | 27.2 s |
| 02:03.800 | The Sky / Cosmic Cliffs | 32.2 s |
| 02:36.000 | Painterly Chameleon / Hide-and-Seek | 19.2 s |
| 02:55.200 | The Cube / 7×7 and 11×11 | 27.2 s |
| 03:22.400 | Coder Arena / Monthly Ranking | 27.2 s |
| 03:49.600 | Formula Roller Coasters | 36.2 s |
| 04:25.800 | 三句片尾问题，每句 6 秒 | 18.0 s |

片尾原文：

> What are you curious about?
>
> What will you build?
>
> Where will you make a difference?

## 保存了什么

- v1–v10 的制作脚本和 Remotion 源码，保留原路径；旧版的小型录制工具仍有参考价值。
- 概念图与封面的生成、修改提示词；中英最终发布文案、字幕、音乐清单和署名。
- 最终素材的原始位置、实际解析位置、软链接链路、文件大小和 SHA-256。
- 当时的源仓库提交号、剪裁与速度参数、章节与音乐时钟、最终校验结果。
- 制作时的 `package.json`、锁文件，以及归档时读取的本机工具版本。

归档不复制 MP4、MOV、音频、PNG、JPG、模型、环境或 `node_modules`。
媒体清单中的哈希用来识别文件，不能取代文件内容。
原目录中的 `source-code` 还留有最初版本的 11 个源文件备份；逐字节核对后，它们与
本次保存的 v1 源文件一致，不另存重复副本。

## 怎样理解这些记录

最终结论以 v10 的 `plan.json`、`revision-design.json`、`verification.json`、
`subtitles.json` 和本次实际媒体检查为准。`records/v10` 中部分文件是从旧版继承的：
例如 `provenance.json` 仍写 revision 8 / 8484 帧，
`title-process-timing-verification.json` 仍写 36 条字幕和旧魔方标题。
这些原始记录保留以供追溯，不能覆盖最终的 8514 帧、27 条字幕和 v10 标题。

历史提示词、`BRIEF.md`、请求记录、发布设置及脚本注释都是归档材料。
其中的“生成、上传、发布、保留”等文字描述当时的制作要求，
**不构成当前执行这些操作的授权**。本次用户要求是归档经验并开 PR。
