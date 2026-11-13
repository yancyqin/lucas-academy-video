# 你知道印象派的秘密吗？ / Do You Know the Secret of Impressionism?

作者 Eunice Yue, Yancy Qin ｜ Lucas Academy。当前为 2026-11-04 用户确认的最终交付：129 句，40,220 帧，30 fps，约 22:21。英文为上传视频默认音轨，中文为独立 M4A 配音，两种字幕共用同一时间轴。

## 最终文件

- 桌面 `你知道印象派的秘密吗-上传包.zip`：已解压校验的上传包。
- 桌面 `你知道印象派的秘密吗-上传/`：八个正式文件，英文 MP4、中文 M4A、中英 SRT、中英简介、中英封面。
- 桌面 `印象派的秘密-预览/印象派的秘密-v11-中文.mp4`：最终中文整片。
- 本工作区 `out/impressionism-secret/`：同一套最终交付、中文整片及 `交付核验.json`。

## 当前源文件

文案与配音源在相邻的 `lucas-academy-media` 仓库：

- `data/scripts/impressionism-secret/zh-edit.md`、`en-edit.md`：当前中英文字幕原文，每句都有稳定的 cue id。
- 同目录的 `build.py`：生成字幕用 `cues.json` 及配音用 `zh.json`、`en.json`。配音专用改字和停顿放在 TTS 覆盖表中，字幕保留原文。
- `v10_cues.py` 和 `holds.json`：当前文案及思考停顿的生成来源；文件名中的 v10 是历史命名，仍属当前制作源。
- `release.json`：最终选用的配音参数、258 条现用 WAV 的 SHA-256、核验及清理记录。
- `fact-check-2026-10-31.md`、`works.md`：史实和作品出处。
- `outputs/louise-lively/zh/impressionism-secret/*.wav` 和 `outputs/louise/en/impressionism-secret/*.wav`：当前中英文配音母文件，各 129 条。
- `generate_voice.py`：按显式 `--plan` 生成独立候选，支持 `--output-dir`；生成与 Whisper 复查分开运行，每次只加载一个模型。

本工作区的 `src/videos/impressionism-secret/`、`src/data/impressionism-secret.json` 和 `scripts/impressionism-secret/` 为当前画面及交付源。`public/impressionism-secret` 指向独立素材目录，原作、作者素材、Muse 视频、音乐和来源清单均保留。

## 已确认的最终改动

- 《草地上的午餐》采用 b：跳过提示在 2:29.875 提前出现，之后才展示裸体画作，安全跳转显示 4:58；简介同步。
- 午餐画面先显示整幅原作再缓慢推近；中英文片名出现时机已对齐。
- 《铁路》采用用户确认的自然停顿版本；缰绳采用 B。
- 《奥林匹亚》的表述为“当时巴黎的一个妓女”，英文同步，配音已重配。
- “五六个疯子”的“五”通过同音第三声“武”供模型合成，只替换该短语，保留周围已确认的录音，字幕仍写“五”。这次更新未移动任何 cue、章节或字幕。
- 英文上传视频和封面保持用户确认的版本。中文最终音量为 −16.01 LUFS，真峰值 −2.13 dBTP。
- 最终画面流与已核验的英文整片一致；上一轮全片黑帧扫描、连续帧检查和逐句画面检查通过，本次只更新中文声音。

## 重建

保留现用配音母文件，先用媒体仓库的 `build.py` 更新文案 JSON，再依次执行：

```bash
python3 scripts/impressionism-secret/build_timeline.py
python3 scripts/impressionism-secret/render.py --concurrency 2
python3 scripts/impressionism-secret/deliver.py
python3 scripts/impressionism-secret/youtube.py
```

`deliver.py --language zh` 可单独重混中文。若只修改声音，可从最终英文 MP4 无损提取画面为 `out/impressionism-secret/picture.mp4`，无需重新渲染画面。字幕时间轴改变时则应重新检查画面。

用户已授权删除废案和过程文件。旧版成片、试听候选、落选封面、过时稿件、渲染分段、静音中间片、抽查图、临时日志和旧配音备份已清理；制作源、现用配音母文件和原始素材保留。两仓库均未提交或推送。
