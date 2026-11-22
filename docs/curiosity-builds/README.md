# Curiosity Builds 归档索引

先读仓库根目录的 [CURIOSITY-BUILDS.md](../../CURIOSITY-BUILDS.md)。
最终版本为 v10；这个目录是可脱离桌面交付文件夹阅读的文字归档。

## 目录

| 路径 | 用途 |
| --- | --- |
| [lessons.md](lessons.md) | 下次制作可复用的经验 |
| [rebuild.md](rebuild.md) | 输入恢复、录制、剪辑、配乐和校验步骤 |
| [archive-files.json](archive-files.json) | 归档文件的字节数、SHA-256 和来源；不包含清单自身 |
| [media-inventory.json](media-inventory.json) | 清理前只读盘点的媒体路径、哈希、软链接和流信息；没有媒体内容 |
| [music-sources.json](music-sources.json) | 当时选用的具体录音、来源、署名和许可记录 |
| [youtube.json](youtube.json) | 最后交付的中英标题、简介、章节、标签与上传设置 |
| [youtube-description.en.txt](youtube-description.en.txt)、[youtube-description.zh.txt](youtube-description.zh.txt) | 可直接阅读的最终发布文案 |
| [delivery](delivery) | 桌面交付中的全部 SRT 和说明、提示词、署名等文字副本；排除磁盘清理报告 |
| [covers](covers) | 英文封面 v1–v6、中文封面 v1 的提示词与历史记录；没有图片 |
| [records/v10](records/v10) | 最终工作目录中的 JSON、FFmpeg filter 文本和历史补丁；排除日志、截图与清理记录 |
| [records/capture-metadata](records/capture-metadata) | 原始录制的时序和事件记录 |
| [records/initial](records/initial) | 最初需求、应用提交号和录制状态 |
| [runtime](runtime) | 制作时的包清单和锁文件、工具版本、早期音乐恢复脚本所需的来源记录 |

代码在 [scripts/curiosity-builds-v10](../../scripts/curiosity-builds-v10) 和
[src/videos/curiosity-builds-v10](../../src/videos/curiosity-builds-v10)。
`curiosity-builds`（无后缀）表示 v1，`curiosity-builds-v2` 至 `-v9` 保留历史实现。
代码及原始文字按原样保存；归档说明和盘点清单是本次新增。

## 最终记录与继承记录

| 文件 | 如何使用 |
| --- | --- |
| [revision-design.json](records/v10/revision-design.json) | v10 标题缩放、两阶段布局和最终片长 |
| [verification.json](records/v10/verification.json) | 当时完成的成片检查；本次没有重新渲染或重新执行整套视频校验 |
| [chapters.json](records/v10/chapters.json)、[subtitles.json](records/v10/subtitles.json) | 最终 8514 帧时钟及 27 条字幕 |
| [music-cues.json](records/v10/music-cues.json) | 最终音乐取段、增益、转场和来源 WAV |
| [unchanged-timing.json](records/v10/unchanged-timing.json) | v9→v10 未变动音乐及字幕时钟；只重做标题动画 |
| [title-motion-pixels.json](records/v10/title-motion-pixels.json) | 当时从渲染视频提取的标题位移证据 |
| [provenance.json](records/v10/provenance.json) | 继承的 v8 记录；其中 revision、帧数和部分标题不代表 v10 |
| [title-process-timing-verification.json](records/v10/title-process-timing-verification.json) | 继承旧数据；36 条字幕、旧 Cube 标题、步骤链不是最终状态 |
| [source-checkouts.json](records/v10/source-checkouts.json) | 较早录制阶段的提交号；Balanced Chess 后续名称发布另见 `is-*-verification.json` |

音乐许可和站点信息是制作时记录的来源，本次未重新查询外部站点。
肖邦夜曲的演奏者署名在原音乐记录中存在待核对项，见 `music-sources.json` 的
`chopin.credit_note`；归档没有把它改写为已解决的结论。

`verification.json` 中 `audio_loudness.input_*` 是对交付文件的测量。
`output_*` 是当时 `loudnorm` 分析命令的模拟输出，不表示最终文件做过动态响度压缩。
实际混音方式由 `classical_mix.py` 和 `music-cues.json` 记录。

## 检查归档是否完整

在仓库根目录执行以下只读检查；不需要媒体或第三方 Python 包：

```bash
python3 - <<'PY'
from pathlib import Path
import hashlib, json
root = Path.cwd()
manifest = json.loads((root / 'docs/curiosity-builds/archive-files.json').read_text())
for item in manifest['files']:
    data = (root / item['file']).read_bytes()
    assert len(data) == item['bytes'], item['file']
    assert hashlib.sha256(data).hexdigest() == item['sha256'], item['file']
print(f"Verified {len(manifest['files'])} archived text files")
PY
```

文件哈希验证的是归档文字是否齐全。恢复媒体、重新生成画面或重新录制应用后，
仍须按 [rebuild.md](rebuild.md) 的验收项检查新成片。
