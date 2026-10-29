#!/usr/bin/env python3
"""Codex image jobs for the Mozart sketchbook: one test picture per new medium, and the tools that draw them.

  codex_media.py pictures     4 test pictures (watercolour, oil, Chinese ink and colour, coloured pencil) -> pictures/
  codex_media.py tools        brushes / pencil on #FF00FF -> tools/

Every picture uses the theme drawing (twinkle-stars/pictures/p00-theme.png) as the reference for the little star, so the
character holds across media. Runs non-interactively; log + last message in codex-runs/.
"""
import os, subprocess, sys

DATA = "/Users/yqin/repo/playground/lucas-academy-video-data/mozart-sketchbook"
STAR_REF = "/Users/yqin/repo/playground/lucas-academy-video-data/twinkle-stars/pictures/p00-theme.png"

PRE = ("这是自动运行，没有人能回答问题：不要提问，直接把下面每一张都做完。用内置的图像生成工具生成。"
       "生成的图会先存在 ~/.codex/generated_images 里，请把每张复制到要求的输出路径，并在对应文件夹的 generated-assets.json "
       "里登记（文件名、完整提示词、尺寸、参考图）。最后一条消息列出每张的输出路径和实际尺寸。\n\n")

STAR = ("主角小星星：就是参考图（已附上）里那颗小星星——胖胖圆圆的柠檬黄五角星，圆圆的角，两个小黑点眼睛、弯弯的笑嘴、"
        "两团粉色脸蛋；在这一幅里用这一幅的画法画它，但脸和样子保持一样。")
COMMON = "横幅 3:2（1536×1024）。画面铺满整张纸，没有边框。不要任何文字、字母、数字、签名。构图干净，主体清楚，适合孩子看。"

PICTURES = [
    ("pictures/m20-1-watercolour.png",
     "儿童水彩画（像 9 岁孩子认真画的，干净好看）：先用铅笔轻轻打的草稿线**清楚可见**——每个物体都有一圈细细的灰色铅笔轮廓，"
     "上面是透明水彩：颜色有晕染、水痕、边缘略深的水渍，留出一些白纸，看得见水彩纸的纹理。**不要黑色粗轮廓，不要描边笔。**"
     "这一幅（莫扎特嬉游曲 K.138，上午的花园）：明亮的上午，浅蓝的天空和大太阳，小星星躺在花园的草地上伸懒腰，"
     "旁边有几朵大花（红、黄、紫）、一个小水壶、一道矮矮的木篱笆。" + STAR + COMMON),
    ("pictures/m01-1-oil.png",
     "儿童油画（像 10 岁孩子学画时画的厚涂油画）：笔触很明显、一笔一笔看得出方向，颜料厚，天空和风用旋转的笔触（有一点梵高的感觉），"
     "颜色浓。**没有黑色轮廓线**，形状靠颜色和笔触分开。"
     "这一幅（莫扎特第40号交响曲，大风的傍晚）：傍晚的天空是橙色和紫色，大风把树吹弯，树叶和一顶小红帽在空中打转，"
     "小星星顶着风往前飞，脸上有点着急但很勇敢；远处小山坡上有几座小房子。" + STAR + COMMON),
    ("pictures/m07-1-inkcolour.png",
     "中国彩墨画（水墨加淡彩）：画在宣纸上，墨线有浓淡、干湿、粗细变化，用毛笔勾的线；淡彩轻轻晕开，大量留白，安静。"
     "这一幅（莫扎特《大组曲》柔板，夜深了）：夜里安静的湖，湖面用淡淡的墨晕出来，岸边有一盏小纸灯笼亮着暖黄的光，"
     "几根芦苇，远处是淡墨的山；小星星坐在湖边一块圆石头上，安静地看着湖水，天上有几颗小星星。"
     "小星星本身用淡黄色（藤黄）晕染，轮廓是淡墨线。" + STAR + COMMON),
    ("pictures/m16-1-colourpencil.png",
     "儿童彩色铅笔画（彩铅）：所有东西先用深色彩铅（深棕或深蓝）勾出清楚、闭合的轮廓线，线比蜡笔细；里面用彩铅排线涂色，"
     "看得见一道道斜排的铅笔线和颜色叠加，白纸，干净好看。"
     "这一幅（莫扎特单簧管协奏曲回旋曲，下午的捉迷藏）：下午的草地，一棵大树，小星星站在树前用两只角捂着眼睛数数，"
     "一只白色小兔子躲在大树后面只露出两只耳朵，草地上有野花和一只蝴蝶，天空浅蓝有两朵白云。" + STAR + COMMON),
]

TOOLS = [
    ("tools/brush-round.png", "一支真实的水彩圆头毛笔（木头笔杆、银色笔箍、尖尖的貂毛笔头，笔头是干净的浅色），照片。"),
    ("tools/brush-flat.png", "一支真实的油画扁头笔（长木杆、银色笔箍、扁平的猪鬃笔头，笔头沾着一点白色颜料），照片。"),
    ("tools/brush-chinese.png", "一支真实的中国毛笔（竹子笔杆、白色羊毫笔头、笔头尖，笔杆上端有一小截挂绳），照片。笔杆上不要任何字。"),
    ("tools/pencil.png", "一支真实的白色彩色铅笔（木头削尖，笔芯是白色，笔杆涂成白色，没有任何文字或商标），照片。"),
]
MORE_TOOLS = [
    ("tools/marker.png", "一支真实的白色马克笔（笔帽已拔掉，圆头笔尖是白色的，笔杆白色，没有任何文字或商标），照片。"),
    ("tools/pen.png", "一支真实的黑色钢笔（笔帽已拔掉，金色笔尖朝下，笔杆黑色，没有任何文字或商标），照片。"),
    ("tools/pastel.png", "一支真实的白色软色粉笔（方形的粉笔条，一头已经用得斜斜的，没有纸套，没有文字），照片。"),
]
DESKS = [
    ("tools/desk-morning.png", "早上：清晨的阳光从左边窗户斜斜照进来，光线明亮偏冷白，桌面上有窗格的光影。"),
    ("tools/desk-day.png", "白天：明亮柔和的自然光，均匀，桌面干净。"),
    ("tools/desk-evening.png", "傍晚：夕阳从右边窗户照进来，暖橙色的光，影子长长的。"),
]
DESK_FMT = ("一张真实的照片（不是画）：从正上方俯视一张浅色木头书桌的桌面，和这张参考照片同一张桌子、同一个角度（附上的参考图），"
            "只是光线换成：{light}桌面中间空出一大块（宽约画面的 80%、高约 90%），什么都不放；只在边缘零零星星放几支蜡笔和半个铅笔盒。"
            "横幅 16:9（1920×1080 或最接近的尺寸）。不要文字。")

TOOL_FMT = ("斜放，笔尖朝左下、笔尾朝右上，大约 45 度，整支完整地在画面内，长度约占画面对角线的 75%。"
            "俯视稍斜，看得出是圆柱体。背景是纯品红色 #FF00FF，均匀、没有阴影、没有渐变。正方形 1024×1024。不要文字。")


def run(tag, prompt, images=()):
    os.makedirs(f"{DATA}/codex-runs", exist_ok=True)
    open(f"{DATA}/codex-runs/{tag}.prompt.md", "w").write(prompt)
    cmd = ["codex", "exec", "--skip-git-repo-check", "-s", "workspace-write", "-C", DATA,
           "--enable", "image_generation", "-c", 'model_reasoning_effort="medium"', "-o", f"{DATA}/codex-runs/{tag}.last.md"]
    for im in images: cmd += ["-i", im]
    cmd += ["-"]
    with open(f"{DATA}/codex-runs/{tag}.log", "w") as log:
        r = subprocess.run(cmd, input=prompt, text=True, stdout=log, stderr=subprocess.STDOUT)
    print(tag, "exit", r.returncode)
    return r.returncode


def main():
    for d in ("pictures", "tools"): os.makedirs(f"{DATA}/{d}", exist_ok=True)
    if sys.argv[1] == "pictures":
        lines = [f"{i + 1}. 输出到 {p}：{t}" for i, (p, t) in enumerate(PICTURES)]
        sys.exit(run("pictures-test", PRE + "附上的参考图就是小星星（每一张都参照它画小星星）。\n\n" + "\n\n".join(lines), [STAR_REF]))
    if sys.argv[1] == "more":
        lines = [f"{i + 1}. 输出到 {p}：{t}{TOOL_FMT}" for i, (p, t) in enumerate(MORE_TOOLS)]
        lines += [f"{len(lines) + i + 1}. 输出到 {p}：" + DESK_FMT.format(light=l) for i, (p, l) in enumerate(DESKS)]
        sys.exit(run("tools-more", PRE + "\n\n".join(lines), ["/Users/yqin/repo/playground/lucas-academy-video-data/twinkle-stars/pictures/desk.png"]))
    if sys.argv[1] == "tools":
        lines = [f"{i + 1}. 输出到 {p}：{t}{TOOL_FMT}" for i, (p, t) in enumerate(TOOLS)]
        sys.exit(run("tools", PRE + "\n\n".join(lines)))


if __name__ == "__main__":
    main()
