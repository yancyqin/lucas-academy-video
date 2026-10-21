# 你会算 7×8 吗？ · Can You Work Out 7 × 8?（趣味经济学 1 · 番外）

**来历（2026-10-15）**：Yancy 看《一根冰棍，要花多少钱？》（[FUN-ECONOMICS-01.md](FUN-ECONOMICS-01.md)）时说手指那条路
「有点难，分心了，单独做个视频吧」。主片里手指只剩一句（oc04-08），原理放到这里。Yancy 定的：加 10 × 10 网格那句；单独的视频，
副标题「趣味经济学 1 · 番外」；英文标题 Can You Work Out 7 × 8?

**稿子**：[中文](docs/fun-economics-01-7x8/zh-edit.md)、[英文](docs/fun-economics-01-7x8/en-edit.md)，10 句，编号 hx00-01…hx03-02。
六句和主片 v0.7 的手指七句一字不差，直接用当时的配音（`lucas-academy-video-data/fun-economics-01/finger-takes-v0.7/`，
`narration.py` 复制进来）；新配的四句：开头的问题、伸出两只手、网格那句、结尾的问题（6 × 7）。

**结构**（约 2 分钟）：
| 段 | 画面 |
| --- | --- |
| HX00 开场 | 纸上大字「7 × 8 = ?」→ 56 →「不背口诀，只用两只手？」；片名卡（你会算 7 × 8 吗？ / 趣味经济学 1 · 番外） |
| HX01 用手指算 | Yancy 拍的手，一条曲线变速，「左手」「右手」时手势到位；卡片同主片 v0.7 |
| HX02 为什么 | 算术网页第 3 场（手 + 式子），中间插第 6 场网格：划掉 3 列、2 行，右下角划掉两次、加回一次，剩下 8 行 × 7 = 56；然后 x、y 证明 |
| HX03 结尾 | 「从 10 往回看……这个过程，很宝贵」；纸上「6 × 7 = ?」，伸出几根？弯着几根？和口诀一样吗？ |

**做法**：和主片同一条流水线，`scripts/fun-economics-01-7x8/` 里每个脚本加载主片对应的脚本、换成这部片的路径和时间
（`common.py`）。网页用同一个 `pages/fun-economics-01/multiplication-roads.html`，`#solo` 去掉「第 3 条路」的编号。
narration.py → narrate.py zh|en → build_timeline.py → check.py → build_timeline.py → make_hands.py → 
`node scripts/fun-economics-01/record-roads.cjs [en] --film=fun-economics-01-7x8 --from=hx02-01 --to=hx03-01 --name=page --hash=solo`
→ build_timeline.py → render.py zh|en → quality.py → package.py（桌面「你会算7x8吗-上传」「你会算7x8吗-英文版-上传」）。
每部片都有中文和英文两份字幕。合成 `FunEconomics01ExtraZh/En`，封面 `FunEconomics01ExtraCoverZh/En`（手势照片 + 一个大问题）。

**音乐**：《G 大调小步舞曲》（Musopen，公有领域），和主片开头同一首。
