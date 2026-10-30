# 小星星变奏曲 · 画画版

音乐：莫扎特《小星星变奏曲》K. 265，Simone Renzi 演奏（CC BY 3.0，和《报数为什么说幺》同一份录音，
`lucas-academy-video-data/twinkle-stars/music/mozart-k265-renzi.mp3`）。

**只做两幅（owner 2026-10-28：「这两个 picture 已经很好了，不用太多了，太多速度就太快了」）**：主题 + 第 1 变奏，1:31。
原先计划的 13 幅（每段变奏一幅）不做了。

| 段 | 时间 | 画 |
|---|---|---|
| 主题 | 0:04–0:48 | 小星星在夜空里醒来，月亮旁边，下面是亮着灯的小房子 |
| 第 1 变奏 | 0:49–1:30 | 小星星从彩虹滑梯上一路滑下来 |

每一幅按音乐的结构画（A A B A′ B A′）：先用黑色蜡笔勾轮廓（主角小星星先画），从某个乐句的开头起涂颜色
（物件 → 天空 → 天上的小星星，一条连续的笔路按拍子切开，匀速），每一笔都从一个音开始。
**画完留 3–5 秒（owner：「每幅画完要有 3-5 秒左右让星星闪一闪，跟着节奏来」）**：画在最后一个音前约 3.6 秒完成，
之后每拍两颗星闪、大星星的角每两拍亮一次、最后一个音所有星星一起闪；蜡笔退到一边；下一张纸等最后一个音之后才滑进来。

另做一个竖屏短视频：只有主题（48.6 秒），画纸在中间，下面一行中英文问题
「一闪一闪亮晶晶，能画出来吗？ / Can you draw “Twinkle, Twinkle”?」。

## 怎么重做

代码在 `scripts/twinkle-stars/`，用 `/Users/yqin/repo/playground/lucas-academy-video/.venv-reframe/bin/python` 跑：

1. `codex_run.py sample`：Codex 生成两幅画、书桌、蜡笔（`pictures/`，`generated-assets.json` 登记了提示词）
2. `../debussy-impressions/faune_onsets.py` → `beats.py`：每段的音符和拍子（`sample/onsets-*.json`、`beats-*.json`）
3. `crayon.py analyze` → `crayon.py plan`：线条、色块、每一笔的时间（`analysis/`、`sample/plan-*.json`）
4. `film.py sample/config.json OUT.mp4 --to 90.6`：长片；`film.py short/config.json OUT.mp4 --to 48.6` + `short/title.png` 叠字：短视频
5. `cover.py`：中英文封面；`youtube.py`：两份上传说明

上传包在桌面「小星星变奏曲-上传」。上传说明写明画面是 AI 生成的（Altered/synthetic = 是），音乐署名 Simone Renzi、CC BY 3.0。
