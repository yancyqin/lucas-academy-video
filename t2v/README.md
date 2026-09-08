# t2v — 命令行文生视频(diffusers + Metal)

跟 `../comfyui/` 是同一个模型的两种用法:

- **ComfyUI** —— 图形工作流,手调参数,看中间结果。
- **这里** —— 命令行,可脚本化、可批量、可被仓库里的 Remotion 流程调用。

Remotion 那套是**确定性**渲染(代码画什么就是什么),这里是**扩散采样**(给一句话,
采出像素)。两者互不干扰。

## 两条路共用一份权重

关键点:**文本编码器不重复下载**。ComfyUI 的
`umt5_xxl_fp16.safetensors` 用的就是标准 HuggingFace 键名,可以直接加载进
diffusers 的 `UMT5EncoderModel`——不需要任何键名映射:

```bash
--text-encoder /Users/yqin/ComfyUI-Shared/models/text_encoders/umt5_xxl_fp16.safetensors
```

省掉了 Wan 官方 diffusers 仓库里那份 **22.7 GB 的 fp32 副本**。本目录只保留 ComfyUI
格式装不下的两样东西:diffusers 版的 transformer 和 VAE(共 5.8 GB)。

```
.venv/     独立 Python 3.12 环境(不碰仓库的 node 工具链)
models/    HF_HOME —— diffusers 版 transformer + VAE
outputs/   生成的 mp4
```

## 用法

```bash
cd t2v
./.venv/bin/python generate.py \
  --text-encoder /Users/yqin/ComfyUI-Shared/models/text_encoders/umt5_xxl_fp16.safetensors \
  --backend wan --steps 25 --guidance 5 --shift 3 \
  --scheduler euler \
  --width 832 --height 480 --frames 17 --fps 16 \
  --prompt "a paper boat drifting down a rain gutter, rushing water, autumn leaves"
```

`--shift 3 --guidance 5` 是 **Wan 官方的 diffusers 配方**。`--scheduler euler` 是默认值,
理由见下面那条最重要的坑。

另外不要照搬 ComfyUI 图里的 `ModelSamplingSD3 shift=8`——那是另一套采样器的旋钮,
含义跟这里的 `--shift` 不同。

尺寸约束:宽高是 16 的倍数;帧数是 `4k+1`(VAE 时间轴 4 倍压缩 + 1 个锚帧)。
81 帧 = 16fps 下 5 秒。

看结果(不用播放器,顺便检查是不是跑崩了):

```bash
./.venv/bin/python contact_sheet.py outputs/<clip>.mp4
```

会拼一张抽帧网格,并打印平均像素值和帧间变化量——全黑、全白、或者"根本不动"
在这两个数字上立刻暴露。

## 实测(M3 Pro / 36 GB)

| 步骤 | 数字 |
|---|---|
| transformer 单次前向(832×480,2 潜在帧) | 2.26 s |
| 去噪 17 帧 / 10 步 / cfg 6 | 145 s(14.5 s/步) |
| 去噪 33 帧 / 30 步 / cfg 6 | 约 22 分钟(43.7 s/步) |
| VAE 解码 17 帧 | 68 s,峰值 **24.5 GiB** |
| VAE 解码 33 帧 | 142 s,峰值 **35.9 GiB** |

33 帧解码的 35.9 GiB 贴着 36 GB 上限。想留余量就用 17 帧。

去噪结果会先写到 `<name>.latents.pt` 再解码,所以解码失败不会毁掉几十分钟的去噪:

```bash
./.venv/bin/python decode.py outputs/<name>.latents.pt            # 重试(MPS)
./.venv/bin/python decode.py outputs/<name>.latents.pt --device cpu  # 内存不够时的退路
```

## 这台机器上踩到的坑

- **UniPC 求解器在 bf16 + Metal 下会把颜色烧掉。** 这是本次最花时间的一个坑。
  症状:步数越多画面越艳、高光越死——10 步干净,25 步开始过曝,30 步整片板结。
  排查过程中先后排除了 `flow_shift`(3 和 8 都烧)和 `guidance`(5 和 3 都烧),
  最后把求解器从 `UniPCMultistepScheduler` 换成 `FlowMatchEulerDiscreteScheduler`,
  **其余参数一字不改**,画面立刻恢复正常写实。原因是 UniPC 是二阶多步法,要用前几步
  的模型输出做外推,bf16 的舍入误差在这条历史链上累积;Euler 是一阶、不带历史。
  所以 `--scheduler` 默认是 `euler`。
- **不要开 `vae.enable_tiling()`。** 跟直觉相反:这个 VAE 的分块解码路径会把每块
  的结果和卷积缓存全部留在内存里,峰值冲到 **45 GiB 直接 OOM**;而不分块的路径本身
  就是**逐潜在帧**解码的(`autoencoder_kl_wan.py` 的 `_decode`),峰值只有 24.5 GiB
  并且能跑完。开分块在这里是纯粹的劣化。
- **`export_to_video` 会把 uint8 帧整体反相。** 本次最贵的一个坑,因为它**不报错**:
  片子能播、运动正确,只有颜色是反的——金色变蓝、日出变成地平线上一个黑洞、
  圣殿幔子看着像 X 光片。原因在 `diffusers/utils/export_utils.py`:只要传进去的是
  numpy,它就无条件执行 `(frame * 255).astype(np.uint8)`,因为它假设你给的是 [0,1]
  的浮点。传 uint8 就等于乘 255 再回卷,而 255 ≡ −1 (mod 256),于是每个值 v 变成
  256 − v,正好是反相。**排查它的唯一可靠办法是拿旧管线的成品对比**:我一开始只比了
  自己的两条新路径(流式解码 vs 一次性解码),两边都过同一个转换函数,所以差值是 0,
  bug 被验证"通过"了。拿 `outputs/sh16-hills.mp4` 一比就立刻现形——均值 63 对 192,
  两个数加起来正好 255。写 uint8 直接用 `imageio.get_writer`,不要走 `export_to_video`。
- **长片要流式解码,不要 `vae.decode()` 一次到底。** upstream 那条路径本身已经是
  **逐潜在帧**解码的,但它用 `torch.cat` 把所有已解码的像素帧留在 GPU 上,峰值因此随
  片长增长——33 帧 35.9 GiB 就贴到天花板,81 帧根本跑不出来。`decode_stream.py` 复刻
  同一个循环(同权重、同 conv cache、同顺序,像素**逐位相同**),但每块解完立刻转
  uint8 搬回主机,峰值稳定在 22 GiB 且**不再随片长增长**,81 帧因此可行(解码 269 s)。
- **蒸馏版的时间步在 euler 上也要钉。** `pin_dmd_timesteps` 原本只在 unipc 分支调用,
  于是 `--backend fastwan --scheduler euler` 会落在 `[1000, 751.1, 8.9]` 而不是训练位置
  `[1000, 757, 522]`——最后一步几乎什么都不做。两个 scheduler 都接受自定义 sigmas 且都会
  再做一次 flow shift,所以同一套反解逻辑通用,现在对 fastwan 无条件生效。
- **1.3B 只画得动大尺度题材,提示词越长越糊。** 把"山谷+田野+海+前景+雾+光斑"堆在一条
  提示词里,细节多的前景会长出彩色噪点(青/洋红颗粒),而干净的天空没事;压成"一个大尺度
  主体"就稳定得多。另外 **fastwan 不做 CFG,`--negative` 完全不生效**——蒸馏版没有无
  引导分支,想排除什么只能写进正向提示词,或者改用 `--backend wan`。
- **Xet 传输会卡死。** HF 新的分块传输通道在这个网络下大文件 0 字节不动(端点本身
  可达,不是 DNS 问题)。设 `HF_HUB_DISABLE_XET=1` 走普通 CDN,立刻恢复 ~12 MB/s。
- **11 GB 的编码器必须在去噪前释放。** 光是 33 帧的 VAE 解码峰值就有 35.9 GiB,
  编码器再驻留就必然溢出。脚本先 `encode_prompt`,再 `pipe.text_encoder = None`
  并 `empty_cache()`,然后才进采样循环。
- **`assign=True` 加载后要手动重新绑权重。** `encoder.embed_tokens.weight` 与
  `shared.weight` 共享存储,checkpoint 里只存一份;不手动绑就会留在 meta 设备上,
  报 `Cannot copy out of meta tensor`。
- **VAE 必须 fp32。** Wan 的 VAE 在 bf16 下数值不稳,官方也是这么做的;只有
  transformer 和文本编码器用 bf16。
- **`PYTORCH_ENABLE_MPS_FALLBACK=1`。** 个别算子还没有 Metal 内核,让它回落 CPU。
- **`set_timesteps(sigmas=...)` 的类型标注是错的。** 签名写 `list[float]`,实现里做
  numpy 运算,传 list 直接 `TypeError`;而且它会对传入的 sigma **再做一次 flow
  shift**,要传反解过的值。

## 关于蒸馏版(未下载)

`FastVideo/FastWan2.1-T2V-1.3B` 是同一模型的 sparse-distill 版本,3 步出片、不做 CFG,
一次生成只要 **3 次前向**(官方版 30 步 × cfg = 60 次)。`--backend fastwan` 的代码
路径已经写好并验证了时间步固定逻辑(钉在 `[1000, 757, 522]`,否则 UniPC 会把 3 步
均匀撒在 linspace 上,不是模型训练的位置)。只差 6 GB 的 transformer 没下。

在 Mac 上这个差距是决定性的,想要快就补这一步。
