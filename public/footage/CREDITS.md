# 素材出处

这个目录的媒体文件不进仓库,所以这份记录是唯一的来源追溯。**每加一条第三方素材就补一行。**

## 实拍(Pexels)

来源 URL 与本地文件**逐字节核对过**(`Content-Length` 与下载文件大小完全一致),不是靠搜索词猜的。

| 文件 | Pexels 源 | 原始规格 | 本片中的处理 |
|---|---|---|---|
| `cc0-sunrise-a.mp4`<br>`cc0-sunrise-b.mp4` | [`video-files/11342250/11342250-hd_1920_1080_30fps.mp4`](https://videos.pexels.com/video-files/11342250/11342250-hd_1920_1080_30fps.mp4)<br>29,587,883 bytes | 1920×1080 / 30fps / 40.107s<br>拍摄于 2022-03-02 | 切成 0–20s 和 20–40s 两段,各慢放 1.5× |
| `cc0-birds.mp4` | [`video-files/36774926/15583977_1080_1920_30fps.mp4`](https://videos.pexels.com/video-files/36774926/15583977_1080_1920_30fps.mp4)<br>9,005,213 bytes | **1080×1920 竖屏** / 30fps / 16.133s | `crop=1080:608:0:960` 裁成 16:9(取下半部,地平线落在上三分之一),lanczos 放大到 1080p,慢放 2.2× |

**下载过但未使用:** `video-files/38976213/16581180_1920_1080_30fps.mp4`(17,585,663 bytes)。

> **待补:** 上面两条的 Pexels 页面地址和作者名。页面有 Cloudflare 拦截,脚本抓不到,
> 需要在浏览器里打开 `pexels.com/video/<id>/` 记录。

**许可:** Pexels 素材按 [Pexels License](https://www.pexels.com/license/) 可免费用于商业和
非商业用途,无需署名,但不得原样转售、也不得把可识别的人物用于负面语境。本片属于常规使用。

## 生成(本机)

`sh01`–`sh17` 系列与 `fast-grass` 由本机的 Wan 2.1 生成(见 [t2v/README.md](../../t2v/README.md)),
用蒸馏版 `--backend fastwan`,prompt 记在 git 历史里。无第三方权利问题。

## 音频

歌曲本身由 Suno 生成,人声翻唱见 [voice-cover/](../../voice-cover/README.md)。
音频文件同样不进仓库。
