# 如需重做 Curiosity Builds

此文记录最终 v10 的制作配方。归档只保留文字；下面的命令是将来恢复输入后的步骤，
本次没有执行渲染或素材获取。仅有本仓库不能保证重做出逐帧、逐字节一致的视频。

## 先恢复哪些东西

原视频仓库：`/Users/yqin/repo/playground/lucas-academy-video`。
数据根目录：`/Users/yqin/repo/playground/lucas-academy-video-data/curiosity-builds-20261118`。
最终数据目录：数据根下的 `v10`；桌面交付目录为
`/Users/yqin/Desktop/Curiosity Builds - Final`。

[media-inventory.json](media-inventory.json) 列出 139 个最终直接输入，以及原始录像、
图像参考、原件、封面和交付媒体。105 张 Sweet Home 帧图按文件逐一记录。
`exists_at_archive` 只代表 2026-11-21 盘点时存在；媒体内容没有进入仓库。
`symlink_chain` 保留每一级链接，`resolved_path` 是当时真正的落点。

| 输入 | 如何找回或重做 |
| --- | --- |
| `captures/jesus-background.mp4` | 用用户原件 `Downloads/Jesus, Joy of Man's Desiring.mp4` 的 6.5–24.5 秒画面制作虚化背景；不用其音轨。原件 SHA 在 `records/v10/v4-sources.json`。原件丢失只能找回或换一段背景。 |
| 三张概念图 | 按 `src/videos/curiosity-builds-v10/assets` 的原始、编辑提示词重新生成 `cube-draft.png`、`vangogh-gallery-concept.png`、`journey-gallery-concept.png`，放进 `v10/captures`。ImageGen 没有保留可确定复现的随机状态；原图和编辑参考都未备份。 |
| Sweet Home 3D 过程画面 | 原设计 `Desktop/assect/Eunice/room_design/The Art of Progression - approved-concept-v3.sh3d`，SHA `bd7de8a2e83a48ebbd17266076c3468b4f18b9ac2acddb35e990aa1c565b2803`。从原来选定相机录制；原 `.sh3d` 和相机状态未进入 Git。 |
| 真实项目录像 | 按最终分镜重新录制 Inception Space、Bible Sequence、Painterly Chameleon、Coder Arena；使用历史脚本作参考，适配新页面选择器和调试接口。 |
| Journey 成片中的实景 | 原片 `journey-original-walk.mp4` 的 23.5–43.5 秒，原速 20 秒；清单记录了链接最终落点。找不到原录像时必须重新录制。 |
| Monthly Ranking | 原件 `whole-person-01/public/footage/snake-ranking.mp4`，SHA `4750d959becfed10fcce4a10f1d5ad508de1fcdadecd394d7e31b0f6ca81d8d8`。这是历史服务器对战，无法由当前在线榜单复原。 |
| Cosmic Cliffs | 原录制引用 `sky-panorama-lab/out/background10.jpg`，SHA `0e6000333bc61bea1005c1a82589572bdc0d1927be5fb0b0393512044718df2c`。天空来源署名记录为 NASA/ESA/CSA/STScI；图片未进入 Git。 |
| 五首具体音乐录音 | 来源、录音版本和许可记录见 [music-sources.json](music-sources.json)，切点与增益见 [music-cues.json](records/v10/music-cues.json)。恢复对应录音并转为 48 kHz 双声道 PCM WAV，更新 `sources.json` 的 WAV 路径。 |
| 中英最终封面 | 原图分别在 `covers-v6/02-ideas-to-worlds-neutral-white-v6.png`、`covers-zh-v1/02-ideas-to-worlds-zh-v1.png`；提示词与修改链在 [covers](covers)。图片需找回或重新生成。 |

许可字段是当时的来源记录；肖邦夜曲演奏者署名的未决项也原样保留。
旧脚本 `music_sources.py` 只恢复早期三首录音，并依赖其他项目的 JSON，
不会完整恢复 v10 的五首音乐。所需历史 JSON 已放进 `runtime/music-history`，
仍不能替代音频文件。最终不使用旧的 BWV 846 Prelude，Bach 只用于 Sky 的《Air》。

## 运行环境与路径

- Node 20；Remotion、renderer、bundler 实测为 4.0.484，Playwright 实测为 1.59.1。
- Python 3.12 环境需要 NumPy、Pillow；原环境是 `.venv-align/bin/python`。
  不要仅用 `python3` 的名字推断版本：归档时系统 `python3` 已是另一版本。
- FFmpeg / FFprobe、macOS Google Chrome、系统 Georgia / Helvetica Neue / Arial 字体。
  原录制还使用 Sweet Home 3D 和 Swift 的本机窗口捕获辅助程序。
- [runtime/environment.json](runtime/environment.json) 是归档时读取的版本，
  不能断言每个工具都是制作当天同一构建。包清单和锁文件在同一目录。

历史脚本保留了 `/Users/yqin/...` 绝对路径、Chrome 应用路径和
`/Users/yqin/repo/ai-testing/node_modules/playwright` 的直接引用。
在另一台机器上，先在单独工作副本统一改路径，再运行；不要把原始归档当作跨机器的一键工具。
根目录 `package.json` 随其他项目演进，制作时的快照另存于 `runtime/package.json`。
本片的入口是 `src/videos/curiosity-builds-v10/Film.tsx`，不是根目录默认的 MonkeySociety。

恢复目录 `v10/{captures,builds,edit,delivery,records,music}`，将所需文字记录从
`records/v10`、`records/capture-metadata` 放回对应数据位置。
将 `music-sources.json` 恢复成 `v10/music/sources.json` 并修正 WAV 路径。
先恢复或生成实际输入，再考虑复用缓存收据；旧 `.mux.json`、`.dissolves.json` 的
digest 包含路径、mtime 等信息，在新机器上不构成可直接复用的证明。

## 录像与剪辑对应关系

最终 [plan.json](../../scripts/curiosity-builds-v10/plan.json) 定义顺序、源片段名、
起点、速度和成片时长。`v10/render.py` **只拼接已经处理好的 `edit/*.mp4`**，
不会自动恢复原始捕获或执行全部旧版裁剪。

| 项目 | 录制 / 处理的参考 |
| --- | --- |
| Chess | `curiosity-builds-v5/capture-live.cjs` 配 `weekly.cjs` 录规则；实际走子事件在 `records/v10/chess-play-events.json`。v5 `assemble.py` 包含规则标签覆盖图和棋盘裁剪。 |
| Bible | v5 `bible-modes.cjs`、`bible-natural.cjs`、`capture-live.cjs` 和 `serve-bible.cjs`。WEB 的 Psalm 119:105；页面选择 Sequence / Next Word，成功完成后再收尾。最终四段输出 3、8、2.5、10.5 秒，约 2 倍速。 |
| Van Gogh / Journey | 历史 `capture-is.cjs` 和 `live.cjs`；Journey 实景使用旧片 23.5–43.5 秒。Sweet Home 原生录屏辅助程序见 v5 `sweet-motion.swift`，只裁下方 3D 模型。 |
| Sky | v10 `capture-sky.cjs`，一条完整 25 秒连续录像。原本机 Chrome CDP 为 9238，应用预览为 5192；录制专用 Vite 禁用自动重载，避免中途刷新。 |
| Chameleon | v5 `capture-live.cjs` / `live.cjs`；最终 paint 从源 4 秒起取 6.5 秒，seek 从 2 秒起取 5.5 秒；旧版 `assemble.py` 保存画面组合方法。 |
| Cube / Roller | v7 `capture-is.cjs` / `capture-ice.cjs`；以 `records/v10/new-footage-processing.json` 为最终覆盖，不能沿用 v5 对魔方的裁剪。Cube 两段各 300 帧。 |
| Coder | 实际竞技场取源 8 秒起 10 秒，历史八 bot 对战取源 5 秒起 10 秒；v5 `assemble.py` 保存左画面、右大标签的处理。 |

初期应用提交号见 `records/initial/source-checkouts.json`，较后阶段见
`records/v10/source-checkouts.json`。它们不能证明包含了全部未提交的应用改动；
Balanced Chess 后续命名发布另有 `is-release-verification.json` 等记录。
这次没有把其他应用仓库的代码复制到视频仓库。

Sweet Home 最终模型裁剪：`crop=1480:520:260:560`，保留 105 帧。
原生窗口录像及原选定相机需要恢复；裁剪后的结果放为
`v10/captures/sweet-home-v3-model-only.mp4`，然后执行下面的帧提取。

## 输入齐全后的渲染顺序

下面假设当前目录为已修正路径的视频仓库，原 `.venv-align` 已恢复。
先确保输出目录存在，所有最终 `edit` 片段已按分镜处理完成：

```bash
.venv-align/bin/python scripts/curiosity-builds-v10/prepare-house-frames.py
node scripts/curiosity-builds-v10/render.cjs
node scripts/curiosity-builds-v10/render.cjs ending
.venv-align/bin/python scripts/curiosity-builds-v10/render.py
.venv-align/bin/python scripts/curiosity-builds-v10/subtitles.py
.venv-align/bin/python scripts/curiosity-builds-v10/verify.py
```

第一步得到 105 张 `sweet-home-model-frames/frame-001.jpg` 等图片。
第二步绘制九段 216 帧介绍，第三步单独生成 540 帧片尾。
`render.py` 创建章节、居中叠化、配乐及主片；`subtitles.py` 生成 27 条中文标签字幕。
`verify.py` 还要求完整录制证明、源概念图路径、原生材质记录和关键截图。
重录素材时应重新生成这些证明，不能复制旧检查结果声称新片通过。

如只检查一个新改动，可先 `node scripts/curiosity-builds-v10/render.cjs chess --stills`
生成关键帧。完整验收后才生成上传包；`youtube.py` 会写仓库文案和桌面的 `YouTube` 目录，
并读取最终封面、配乐署名和章节。它不会自动上传视频。

原 `desktop_delivery.py` 依赖 v9 的 `desktop-delivery.json` 和仍存在的旧桌面目录，
并通过改名备份旧目录来替换交付。清理后应重新编写简单的交付复制步骤，
不能直接运行这段历史打包器。只需保存经验时，无须运行任何制作或打包脚本。

## 最终验收

1. 视频 1920×1080、30 fps、H.264，音频 AAC；主片恰好 8514 帧 / 283.8 秒。
2. 九段章节起点与根目录总表相符，片尾 18 秒，每个问题 6 秒。
3. 每段先有单独标题；同一标题连续缩放移动，先消失再出现制作文字；不加第三种过程布局。
4. Bible 完整视窗和成功操作；Cube 保留整页、顶部步骤和右面板；Sky 连续 750 帧；过山车原生冰蓝外观。
5. 27 条字幕、11 个 SRT 文件，最后一条结束于第 8514 帧；无字幕烧入主片。
6. 音乐顺序、原速、2 秒换曲淡变和片尾终曲正确；没有应用音轨或旁白。
7. 不只看进程成功退出：检查输出文件数量、帧数，完整解码，抽查关键帧和试听转场。

保留原片长只是重做原片的验收条件。如果重新录制使时长变化，必须重新编排章节、
音乐和字幕，并把新版本作为新交付记录；不要为通过旧断言而假装时钟未变。
