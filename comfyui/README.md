# ComfyUI — Wan 2.1 文生视频(本机)

## 你还缺一步:本地实例

Comfy Desktop 现在只注册了一个 **Comfy Cloud** 实例(`https://cloud.comfy.org/`),
它跑在 Comfy 的服务器上,**读不到这台机器上的模型文件**。`~/ComfyUI-Installs` 是空的。

要用下面这些本地权重,需要在 Comfy Desktop 里加一个**本地安装**。装好后它会自动读
`settings.json` 里已经配好的共享目录,不需要再改任何路径:

```
modelsDirs: ["/Users/yqin/ComfyUI-Shared/models"]
```

## 已经放好的权重

来自 `Comfy-Org/Wan_2.1_ComfyUI_repackaged`(官方重打包,单文件 + 原版键名):

```
/Users/yqin/ComfyUI-Shared/models/
  diffusion_models/wan2.1_t2v_1.3B_fp16.safetensors    2.84 GB
  text_encoders/umt5_xxl_fp16.safetensors             11.37 GB
  vae/wan_2.1_vae.safetensors                          0.25 GB
```

**为什么用 fp16 文本编码器而不是官方默认的 fp8。** 上游示例用的是
`umt5_xxl_fp8_e4m3fn_scaled.safetensors`(6.74 GB),省 4.6 GB。但 Metal 的 fp8 支持
不完整,而这台机器 36 GB 装得下 fp16。稳定性优先。想换回 fp8,下载那个文件放进
`text_encoders/`,再把 workflow 里 `CLIPLoader` 的第一个值改掉即可。

## Workflow

`wan21-t2v-1.3B-mac.json` —— 直接拖进 ComfyUI 画布加载。

这是**官方示例图**(`comfyanonymous/ComfyUI_examples/wan/text_to_video_wan.json`)
的最小改动版:只把 `CLIPLoader` 指向 fp16 编码器,其余原样保留。官方参数是:

| 节点 | 设置 |
|---|---|
| `EmptyHunyuanLatentVideo` | 832 × 480,33 帧 |
| `KSampler` | 30 步,cfg 6,`uni_pc` / `simple` |
| `ModelSamplingSD3` | shift 8 |
| 输出 | `SaveAnimatedWEBP`(16fps)+ `SaveWEBM`(vp9) |

注意 latent 节点叫 `EmptyHunyuanLatentVideo` —— 名字带 Hunyuan,但 Wan 用的就是它。

## 尺寸约束

- 宽高是 **16 的倍数**。
- 帧数是 **4k+1**(VAE 在时间轴上 4 倍压缩,外加一个锚帧)。33、49、81 都合法。
  81 帧 = 16fps 下 5 秒。

## 速度与内存(M3 Pro / 36 GB 实测)

这些数字来自 `../t2v/` 在 diffusers + Metal 下、用相同的模型和相同的步数/分辨率
跑出来的,**耗时和内存**可以直接当作 ComfyUI 这边的预期:

| 分辨率 / 帧数 | 去噪 | VAE 解码峰值内存 |
|---|---|---|
| 832×480,17 帧,10 步 | 145 s(14.5 s/步) | 24.5 GiB |
| 832×480,33 帧,30 步 | 约 22 分钟(43.7 s/步) | **35.9 GiB** |

**⚠️ 官方图默认的 33 帧,在这台机器上是贴着内存上限跑的。** 解码 33 帧要 35.9 GiB,
而整机只有 36 GB。ComfyUI 里如果解码阶段崩掉或者系统卡死,先把
`EmptyHunyuanLatentVideo` 的帧数降到 **17**(24.5 GiB,宽裕),而不是去降分辨率。

每步 14.5 s(17 帧)到 43.7 s(33 帧)的差距,是因为 token 数随帧数线性增长,而
cfg > 1 时每步要跑正负两次前向。把 cfg 设成 1 能省掉一半,但 1.3B 模型在无引导下
质量掉得明显。

想更快,真正的解法是换蒸馏模型(3 步出片),见 `../t2v/README.md` 末节。

### ⚠️ 如果画面过曝发艳,把采样器换成 euler

官方图的 `KSampler` 用的是 **`uni_pc` + 30 步**。在 `../t2v/` 里(同一个模型、同样
bf16 + Metal),UniPC 求解器跑到 25 步以上会明显烧色:高光死白、颜色板结,10 步反而
干净。把求解器换成 Euler、其余参数一字不改,画面立刻恢复正常。

**这一点我只在 diffusers 里验证过,没有在 ComfyUI 里验证**(本机还没有本地实例),
ComfyUI 的 `uni_pc` 是另一份实现,不一定有同样的问题。所以我把图**保持成官方原样**
没有替你改。如果你跑出来发现颜色不对,改一个下拉框即可:

> `KSampler` → `sampler_name`:`uni_pc` → `euler`

### 一个不要照搬的地方

ComfyUI 的 `ModelSamplingSD3` shift 和 diffusers 里 UniPC 的 `flow_shift`
**不是同一个旋钮**。我把官方图的 shift=8 原样搬到 diffusers 跑 30 步 + cfg 6,
结果高光过曝、颜色板结,比同样 shift 下只跑 10 步还差——典型的 CFG 烧图。

所以上表只用来估**时间和内存**,不要拿 `../t2v/` 的画面去推断 ComfyUI 的画质。
在 ComfyUI 里就用官方图的原始参数;在 diffusers 里则用 Wan 官方的配方
(`--shift 3 --guidance 5`)。
