#!/usr/bin/env python3
"""Codex jobs for the 焰火 film (owner 2026-10-18: "可以让 codex 出光变暗之前写实的图"; "火柴，蜡烛…点亮画面";
"注意这次没有画笔画架了").

  feux_codex_run.py real    realistic photos of five scenes BEFORE the light dims  -> feux/real/<id>-before.png
  feux_codex_run.py tools   seven painted lighting tools on #FF00FF, flame not lit  -> feux/tools/<id>-tool.png
  feux_codex_run.py redo    round 2: composition-locked edits                     -> feux/real/<id>-before-v2.png

Montorgueil reuses real/aligned/fire-2.png (already daylight); Beijing uses the owner's blue-hour photo
(clair/frames/beijing-tower.png). Flames, embers and sparks are drawn by the compositor so they can flicker.
Codex runs non-interactively in a workspace-write sandbox rooted at the debussy data folder; logs in feux/codex-runs/.
"""
import os, subprocess, sys

DATA = "/Users/yqin/repo/playground/lucas-academy-video-data/debussy-impressions"
FEUX = f"{DATA}/feux"

PRE = ("这是自动运行，没有人能回答问题：不要提问，直接把表里每一张都做完。"
       "用内置的图像生成工具生成（参考图已经附在这条消息里，按表里写的对应关系使用）。"
       "生成的图会先存在 ~/.codex/generated_images 里，请把每张复制到表里要求的输出路径，再登记到 {reg}"
       "（JSON 列表，每项 name / source / prompt / size）。用工具能给的最大原生尺寸，不要软件放大。"
       "每张生成后自己检查一遍，不符合要求就重画。最后一条消息列出每张的输出路径和实际尺寸。\n\n")

REAL_RULES = ("共同要求：真实照片的质感（像一台好相机拍的照片，不是油画、不是插画、不是 3D 渲染），"
              "构图必须和参考图完全一致：同一个机位、同样的取景范围和透视，每座建筑、每棵树、每个人、每条船都在参考图里的位置，"
              "地平线/水岸线高度一致，画面宽高比和参考图一样。时代照原画（19 世纪末到 20 世纪初）：不要汽车、电线、现代建筑、现代路灯、广告字。"
              "任何招牌、旗子上都没有可读的字。这是光线变暗之前的那一刻：比参考画里的时刻早二三十分钟，天还亮，所以整体比原画明亮。"
              "天上没有焰火、没有烟。")

REAL = [
    ("venice", ["art/feux-sangiorgio.jpg"],
     "参考图 = 莫奈《暮色中的圣乔治马焦雷岛》。1908 年秋天的威尼斯，从总督宫前的岸边隔着潟湖看圣乔治马焦雷岛。"
     "左边是圣乔治教堂的穹顶和高高的钟楼，岛的轮廓低低地横在画面中线稍下；下面约四成是平静的潟湖水面。"
     "太阳正落到岛的后面，天空从地平线的金橙色过渡到上方的淡青蓝，水面映出一道金色的光和教堂的倒影。"),
    ("parliament", ["art/feux-parliament.jpg"],
     "参考图 = 莫奈《国会大厦，日落》。1903 年伦敦，从泰晤士河南岸圣托马斯医院的阳台看对岸的威斯敏斯特宫。"
     "哥特式塔楼的剪影立在画面中间偏左（维多利亚塔）和右边（尖塔），太阳在塔楼后面偏右、低低地透过薄雾；"
     "天空是暖橙到玫瑰色，雾气让远处发灰；下面三分之一多是泰晤士河，水面有一条长长的暖色光带，一条小船的剪影。"
     "不要伦敦眼、不要现代建筑。"),
    ("montmartre", ["real/aligned/night-1.png", "art/night-1.jpg"],
     "参考图 1 = 我们已有的写实照片（同一构图，夜里），参考图 2 = 毕沙罗《夜晚的蒙马特大道》。"
     "把参考图 1 改成同一地点、同一机位的冬天傍晚，雨刚停，太阳刚落：天空还是明亮的灰蓝带一点暖色余晖，"
     "商店橱窗和路灯只有零星几盏刚点亮（大多数还没亮），湿路面映着天光。楼房、行道树、马车和行人的位置都和参考图 1 一样。"),
    ("rhone", ["real/aligned/night-2.png", "art/night-2.jpg"],
     "参考图 1 = 我们已有的写实照片（同一构图，夜里），参考图 2 = 梵高《罗纳河上的星夜》。"
     "把参考图 1 改成同一地点、同一机位的九月傍晚，太阳刚落：天空从地平线的橙粉色过渡到上方的淡蓝，还看不到星星；"
     "对岸城镇的煤气灯还没点亮或只亮了一两盏，河面映着晚霞。前景沙岸上那对散步的男女、岸边的小船都在原来的位置。"),
    ("rocket", ["real/aligned/fire-1.png", "art/fire-1.jpg"],
     "参考图 1 = 我们已有的写实照片（同一构图，夜里放焰火），参考图 2 = 惠斯勒《黑色与金色的夜曲：坠落的火箭》。"
     "把参考图 1 改成同一地点、同一机位的傍晚，1870 年代伦敦泰晤士河边的克里莫恩游乐园，焰火开始之前："
     "天空是暮色的灰蓝，还有一点亮光；左边的大树是深色剪影；河边有几盏刚点亮的小灯；岸上几个看焰火的人在原来的位置等着。"
     "天上没有焰火、没有火花、没有烟。"),
]

# Round 2 (2026-10-18): Montmartre came back at street level and Venice with a church too big (aligning it stretched the
# photo by a third), so these are EDITS of a fixed composition, written as -v2.
REDO = [
    ("venice", ["art/feux-sangiorgio.jpg", "feux/real/venice-before.png"],
     "参考图 1 = 莫奈原画（构图以它为准），参考图 2 = 上一版写实照片（光线和质感很好，但教堂画得太大、水岸线太低）。"
     "重画一张写实照片，光线、天色、质感照参考图 2，构图严格照参考图 1：钟楼尖顶几乎碰到画面顶边（在画面高度 4% 左右），"
     "钟楼在画面宽度 15%–19% 处，教堂和岛的轮廓横在画面宽度 4%–45% 之间、整体比参考图 2 小很多，"
     "岛的水岸线在画面高度 52% 处；右边远处画面宽度 75%–92% 处是另一座圆顶教堂（安康圣母教堂）在雾里的淡影，也坐在 52% 的水岸线上；"
     "下面 48% 全是潟湖水面，映着金色的光和钟楼的倒影。画面宽高比和参考图 1 一样。"),
    ("montmartre", ["real/aligned/night-1.png", "art/night-1.jpg"],
     "这一张请把参考图 1 当作编辑底图做图像编辑（edit），不是重新构图：机位（从旅馆高处的窗口往下看）、透视、"
     "大道的走向、每栋楼、每棵树、每辆马车和每个行人的位置一律保持参考图 1 的样子，只改光线和时间："
     "冬天傍晚，雨刚停，太阳刚落，天空是明亮的灰蓝带一点暖色余晖；商店橱窗和路灯只有零星几盏刚点亮，大多数还没亮；"
     "湿路面映着天光。整体比参考图 1 明亮得多。"),
    ("rhone", ["real/aligned/night-2.png", "art/night-2.jpg"],
     "这一张请把参考图 1 当作编辑底图做图像编辑（edit），不是重新构图：对岸城镇和河岸线的高度与形状、河面、前景沙岸、"
     "岸边的小船、右下角散步的那对男女，位置一律保持参考图 1 的样子，只改光线和时间：九月傍晚，太阳刚落，"
     "天空从地平线的橙粉色过渡到上方的淡蓝，还看不到星星；对岸的煤气灯还没点亮或只亮了一两盏，河面映着晚霞。整体比参考图 1 明亮得多。"),
]

TOOL_RULES = ("Use case: stylized-concept. Generate a single isolated hand-painted oil-painting prop for compositing into an "
              "Impressionist painting in a music film. Every part of the object is visibly MADE OF PAINTED BRUSHSTROKES, not a "
              "photographed object, not a 3D render, not a photo filter; slightly soft, dreamy and a little faded. Background must be "
              "mathematically uniform solid RGB(255,0,255), #FF00FF, edge to edge, including all holes. NO background texture, "
              "gradient, cast shadow, ground, vignette, noise or scenery. No magenta in the object, no magenta reflected light or edge "
              "contamination. Painterly softened contours but a clean silhouette for keying. No text, lettering, labels, signature, "
              "watermark, border, hands, people or extra props. The object is NOT LIT: no flame, no glow, no smoke, no sparks "
              "(the flame is added later). Diagonal at about 45 degrees with the LIGHTING END (where the flame will be) at LOWER LEFT "
              "(x 18%, y 82%) and the handle end at UPPER RIGHT (x 82%, y 18%). Whole object visible with generous margins. "
              "Square 1024x1024 or larger.\n")

TOOLS = [
    ("venice", "art/feux-sangiorgio.jpg",
     "Claude Monet's San Giorgio at dusk: warm orange, gold and teal broken strokes. ONE long old wooden kitchen match, pale "
     "unvarnished wood, an unlit rounded match head of dark red-brown sulphur at the lower-left end."),
    ("parliament", "art/feux-parliament.jpg",
     "Claude Monet's Houses of Parliament, Sunset: violet-blue and rose-orange strokes in fog. ONE Victorian lamplighter's pole: "
     "a long slender brass-and-wood pole whose lower-left end is a small brass wick holder with a short unlit cotton wick and a tiny hook."),
    ("montmartre", "art/night-1.jpg",
     "Camille Pissarro's Boulevard Montmartre at night: dense small strokes of ochre, slate blue and lamp-gold. ONE long thin "
     "cream-white wax taper candle held in a small brass taper holder with a turned wooden handle; the unlit wick tip is at the lower-left end."),
    ("rhone", "art/night-2.jpg",
     "Vincent van Gogh's Starry Night over the Rhone: thick swirling impasto strokes of ultramarine, cobalt and lemon yellow. "
     "ONE old-fashioned hand sparkler: a long thin iron wire, the lower-left two-thirds coated with a rough grey-brown sparkler "
     "paste, the bare wire end at the upper right is the handle."),
    ("beijing", "clair/paint/aligned/beijing-tower.png",
     "The Impressionist Beijing night painting given as reference: violet-blue sky strokes and warm orange tree strokes. ONE "
     "Chinese incense stick (线香): a thin reddish-brown incense stick on a slim bamboo core, the bare red-dyed bamboo handle at "
     "the upper right, the unlit incense tip at the lower-left end."),
    ("rocket", "art/fire-1.jpg",
     "James McNeill Whistler's Nocturne in Black and Gold: thin, dark, smoky tonal paint, deep green-black and muted gold. ONE "
     "Victorian pyrotechnician's portfire: a long thin rolled paper tube (muted grey-blue paper) fixed in a short wooden handle; "
     "the open unlit paper end is at the lower left."),
    ("montorgueil", "art/fire-2.jpg",
     "Claude Monet's Rue Montorgueil 1878: lively quick strokes of French blue, white and red with creamy daylight. ONE festive "
     "hand torch (flambeau): a turned wooden handle with a small round brass guard, the lower-left head wrapped in pale oiled "
     "cloth and cord, unlit."),
]

def run(tag, prompt, images):
    os.makedirs(f"{FEUX}/codex-runs", exist_ok=True)
    open(f"{FEUX}/codex-runs/{tag}.prompt.md", "w").write(prompt)
    cmd = ["codex", "exec", "--skip-git-repo-check", "-s", "workspace-write", "-C", DATA,
           "--enable", "image_generation", "-c", 'model_reasoning_effort="medium"',
           "-o", f"{FEUX}/codex-runs/{tag}.last.md"]
    for im in images: cmd += ["-i", f"{DATA}/{im}"]
    cmd += ["-"]
    with open(f"{FEUX}/codex-runs/{tag}.log", "w") as log:
        r = subprocess.run(cmd, input=prompt, text=True, stdout=log, stderr=subprocess.STDOUT)
    print(tag, "exit", r.returncode)
    return r.returncode

def main():
    job, keys = sys.argv[1], sys.argv[2:]
    if job == "real":
        rows = [r for r in REAL if not keys or r[0] in keys]
        os.makedirs(f"{FEUX}/real", exist_ok=True)
        imgs, lines, k = [], [], 0
        for rid, refs, text in rows:
            nums = []
            for ref in refs: imgs.append(ref); k += 1; nums.append(f"第 {k} 张")
            lines.append(f"- 输出 feux/real/{rid}-before.png（参考图：附件{'、'.join(nums)}，按这个顺序就是下文说的参考图 1、2）：{text}")
        reg = f"feux/real/generated-assets.{'-'.join(keys) or 'all'}.json"
        sys.exit(run("real-" + ("-".join(keys) or "all"), PRE.format(reg=reg) + REAL_RULES + "\n\n" + "\n".join(lines), imgs))
    if job == "redo":
        rows = [r for r in REDO if not keys or r[0] in keys]
        imgs, lines, k = [], [], 0
        for rid, refs, text in rows:
            nums = []
            for ref in refs: imgs.append(ref); k += 1; nums.append(f"第 {k} 张")
            lines.append(f"- 输出 feux/real/{rid}-before-v2.png（参考图：附件{'、'.join(nums)}，按这个顺序就是下文说的参考图 1、2）：{text}")
        reg = f"feux/real/generated-assets.redo-{'-'.join(keys) or 'all'}.json"
        sys.exit(run("redo-" + ("-".join(keys) or "all"), PRE.format(reg=reg) + REAL_RULES + "\n\n" + "\n".join(lines), imgs))
    if job == "tools":
        rows = [r for r in TOOLS if not keys or r[0] in keys]
        os.makedirs(f"{FEUX}/tools", exist_ok=True)
        imgs = [ref for _, ref, _ in rows]
        lines = [f"- 输出 feux/tools/{tid}-tool.png（风格参考：附件第 {i + 1} 张）：{text}" for i, (tid, _, text) in enumerate(rows)]
        reg = f"feux/tools/generated-assets.{'-'.join(keys) or 'all'}.json"
        sys.exit(run("tools-" + ("-".join(keys) or "all"), PRE.format(reg=reg) + "每张都用下面这段英文要求（共同部分 + 该行的描述）：\n\n"
                     + TOOL_RULES + "\n" + "\n".join(lines), imgs))

if __name__ == "__main__":
    main()
