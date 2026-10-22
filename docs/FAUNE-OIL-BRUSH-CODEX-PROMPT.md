# 牧神午后试样 · 仿真油画笔触 · Codex 提示词

主人 2026-10-17：「现在的笔触有点太机械，你看看你做还是 codex 来进步」「用仿真的画笔，仿真的笔刷，一笔笔在画板上画出来」。笔触模拟交给 Codex 做成独立模块，Claude 负责把它接进画家时间线、画架场景和镜头里。

---

请写一个**仿真油画笔触**的 Python 模块，用在一支音乐短片里：画布上一支画笔按音乐一笔一笔把莫奈的画画出来。现在的笔触（附图 `now-detail.jpg`、`now-sheet.jpg`）主人觉得**太机械**：像有规则条纹的带子，边缘和粗细太均匀，没有油画颜料的厚度和笔毛的感觉。请做出像真实油画（最好是印象派、莫奈那样的笔触）的效果。

**位置和环境**
- 新文件：`/Users/yqin/repo/playground/lucas-academy-video/.claude/worktrees/information-theory-video-plan-d0f6c2/scripts/debussy-impressions/oil_brush.py`。**不要改** 同目录的 `lazy_painter.py` 和其他文件（Claude 来接）。
- Python 环境：`/Users/yqin/repo/playground/lucas-academy-video/.venv-reframe/bin/python`（有 numpy、scipy、opencv、scikit-image、numba）。
- 参考画（reveal 用）：`/Users/yqin/repo/playground/lucas-academy-video-data/debussy-impressions/faune/sample-seine/target.png`（1440×1272）。

**接口（请照这个设计，可以加可选参数）**
```python
class OilCanvas:          # rgb (H,W,3 float32 0..1)、height（颜料厚度 H,W）、wet（湿度 H,W），ground 是米白画布底色
    def __init__(self, W, H, ground=(0.925, 0.894, 0.831), seed=0): ...
def stroke_geometry(points, width, seed, pressure=None): ...
    # points: [(x,y),...] 笔的中心路径；width: 笔头宽（像素）；pressure: 可选，沿路径的压力曲线（0..1）。
    # 返回可以预先算好的几何（重采样路径、每段宽度、笔毛集合……）。
def paint(canvas, geom, p0, p1, colour, load=1.0): ...
    # 增量地把笔从路径进度 p0 画到 p1（0..1）。每帧调用一次，所以颜料是笔经过时才放上去的。
    # colour：固定 RGB，或 callable(xs, ys) -> rgb（例如从参考画取色 = 把画“画出来”，或从模糊的色调图取色 = 打底）。
def brush_tip(geom, p): ...   # -> (x, y, angle_rad, pressure)：此刻笔头在哪里、朝向、压力（用来放画笔的图片）。
def shade(canvas, light=(-0.5, -0.7), strength=1.0): ...   # -> 显示用的 rgb：按颜料厚度做浮雕光照，不改 canvas.rgb。
```
- 结果要确定：同样的调用得到同样的画面（用 seed，不用无种子的随机）。
- 性能：1440×1272 的画布，一笔宽 250、长 800 像素，每帧增量 `paint` 要在 50 ms 左右（可以用 numba）。`shade` 每帧调用一次也要够快。

**“像真的油画笔触”具体要做到**
- **笔毛**：笔头由很多根笔毛（几十到上百根）组成。每根笔毛位置、含颜料量、长短都不一样，留下细细的、不规则的笔毛痕。不能是周期性的条纹。
- **压力**：落笔时压得重（笔头展开、颜料多，起笔可以有一小团），中段轻一些，收笔时提起（变窄、断续）。宽度和颜料量都跟着压力变。
- **颜料越用越少**：一笔走下去颜料递减；颜料少时出现干笔飞白，只在画布布纹的高点留下颜料。
- **厚度（impasto）**：颜料有厚度，笔毛边缘有小脊，起笔和收笔有堆积。`shade` 用固定方向的光照出立体感，有很小的高光，但不要像塑料。
- **颜色**：同一笔里有轻微的冷暖、明暗变化，像没有完全调匀的颜料。湿颜料上再画会带起、混合下面的颜色（湿画法），沿笔的方向拖出一点混色。
- **边缘和两端**：边缘不规则，有软有硬；两头不是方的，也不是完美的圆，是笔真正落下和提起的形状。
- **印象派**：短而有方向的笔触叠在一起时，应该像莫奈的画面，而不是一条条塑料带子。

**自己测试、自己看**
- 写一个 `demo` 命令：`python oil_brush.py demo OUT_DIR`，输出几张 PNG：
  1. 一组笔触样张：直的、弯的、颤动（trill）的、短促的点、长扫，以及固定颜色的笔触；
  2. 用参考画取色的 reveal 笔触，有 `shade` 和没有 `shade` 的各一份；
  3. 同一笔在进度 25%、50%、75%、100% 时的样子，用来检查笔头前端；
  4. 很多短笔触叠成一小块画面的效果。
- 每改一轮都打开这些图看，和附图（太机械的现状）比，直到你自己觉得像真的油画。也可以对照真实油画笔触的特征。
- 完成后告诉我：接口说明、每帧耗时、样张路径、还有哪些已知局限。不要提交。
