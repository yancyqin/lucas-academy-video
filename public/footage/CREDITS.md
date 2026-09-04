# 素材出处

这个目录的媒体文件不进仓库,所以这份记录是唯一的来源追溯。**每加一条第三方素材就补一行。**

## 实拍(第三方)

| 文件 | 来源 | 搜索词 | 原始规格 | 处理 |
|---|---|---|---|---|
| `cc0-sunrise-a.mp4` | Pexels | `sunrise clouds mountain` | 1920×1080 / 30fps / 40s | 取 0–20s,慢放 1.5× |
| `cc0-sunrise-b.mp4` | Pexels | 同上(同一素材) | 同上 | 取 20–40s,慢放 1.5× |
| `cc0-birds.mp4` | Pexels | `flock of birds sky silhouette` | **1080×1920 竖屏** / 30fps / 16s | 裁 `crop=1080:608:0:960` 转 16:9,放大到 1080p,慢放 2.2× |

> **TODO(需要补):** 上面三条缺具体的 Pexels 页面 URL 和作者名。Pexels 许可不强制署名,
> 但发布前应当把 URL 记下来,以备日后核查。下载这几条的人补一下。

**许可:** Pexels 素材按 [Pexels License](https://www.pexels.com/license/) 可免费用于商业和
非商业用途,无需署名,但不得原样转售、也不得把可识别的人物用于负面语境。本片属于常规使用。

## 生成(本机)

`sh01`–`sh17` 系列由本机的 Wan 2.1(见 [t2v/README.md](../../t2v/README.md))生成,
prompt 记在 git 历史里。无第三方权利问题。

`fast-grass` 同上,用蒸馏版 `--backend fastwan` 生成。

## 音频

歌曲本身由 Suno 生成,人声翻唱见 [voice-cover/](../../voice-cover/README.md)。
音频文件同样不进仓库。
