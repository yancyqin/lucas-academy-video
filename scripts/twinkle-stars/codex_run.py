#!/usr/bin/env python3
"""Codex image jobs for the Twinkle Variations drawing film (owner 2026-10-16: "你自己调用 codex cli").

  codex_run.py sample        the theme + Variation 1 drawings, the desk, the crayon (pictures/)

One style prompt for every drawing, so line and fill separate the same way in each. Codex runs non-interactively in
a workspace-write sandbox rooted at the data folder; log + last message in codex-runs/.
"""
import os, subprocess, sys

DATA = "/Users/yqin/repo/playground/lucas-academy-video-data/twinkle-stars"

PRE = ("这是自动运行，没有人能回答问题：不要提问，直接把下面每一张都做完。"
       "用内置的图像生成工具生成。生成的图会先存在 ~/.codex/generated_images 里，请把每张复制到要求的输出路径，"
       "并在 pictures/generated-assets.json 里登记（文件名、提示词、尺寸）。最后一条消息列出每张的输出路径和实际尺寸。\n\n")

STYLE = ("画风（每一幅都一样）：儿童蜡笔画，像一个 7 岁孩子用蜡笔认真画的，但构图干净、好看。"
         "所有东西都用粗黑色蜡笔勾边：线条连续、粗细差不多、轮廓闭合，黑线和色块之间没有缝。"
         "黑线以内用蜡笔平涂颜色，看得见蜡笔的笔触和纸的纹理；不要渐变、不要写实阴影、不要高光、不要发光效果。"
         "夜空用深蓝色蜡笔涂满（是深蓝，不是黑色），看得见涂抹的笔触。画在米白色的画纸上，画面铺满整张纸，没有留白边框。"
         "横幅 3:2（1536×1024）。不要任何文字、字母、数字、签名、边框。"
         "主角小星星：一颗胖胖圆圆的五角星，柠檬黄色，黑色轮廓，简单的笑脸（两个小黑点眼睛、弯弯的嘴、两团粉色脸蛋），"
         "五个角圆圆的，像软软的。")

SAMPLE = [
    ("pictures/p00-theme.png",
     STYLE + "\n这一幅（主题）：夜晚，小星星刚刚醒来，在弯弯的月亮旁边开心地眨眼睛（一只眼睛闭着）。"
     "小星星在画面中间偏上，比较大（高度约占画面的三分之一），月亮在它左边。"
     "画面下方是四五座圆圆胖胖的小房子和一棵圆树，窗户亮着暖黄色的灯，屋顶有红有绿。"
     "天上还有七八颗更小的黄色星星（没有脸），大小不一，散开。"),
    ("pictures/p01-v1.png",
     STYLE + "\n这一幅（第 1 变奏）：同一颗小星星（就是 pictures/p00-theme.png 里的那颗，脸和颜色都一样，请把那张作为参考图）"
     "从一道彩虹滑梯上飞快地滑下来，两只上面的角举起来像在欢呼，嘴巴张开在笑。"
     "彩虹从画面左上方弯下来到右下方，七种颜色的宽条纹，每条都有黑色轮廓。"
     "小星星身后拖着一串五六颗很小的黄色星星。彩虹下面是几朵白色的圆云。"),
    ("pictures/desk.png",
     "一张真实的照片（不是画）：从正上方俯视一张浅色木头书桌的桌面，晚上，一盏台灯的暖光从左上方照下来，右下角偏暗。"
     "桌面中间空出一大块（宽约画面的 80%、高约 90%），什么都不放（之后会把一张画纸合成在那里）。"
     "只在边缘零零星星放几支蜡笔（红、蓝、绿）和半个铅笔盒，不要挡住中间。柔和、温暖、安静。"
     "横幅 16:9（1920×1080 或最接近的尺寸）。不要文字。"),
    ("pictures/crayon.png",
     "一张真实的照片：一支白色的蜡笔，外面包着白色纸皮（纸皮上没有任何文字或图案），笔尖已经用过、有点圆钝。"
     "蜡笔斜放，笔尖朝左下方、笔尾朝右上方，大约 45 度，整支完整地在画面内，长度约占画面对角线的 70%。"
     "俯视角度稍微斜一点，能看出是圆柱体。背景是纯品红色 #FF00FF，均匀、没有阴影、没有渐变。"
     "正方形 1024×1024。不要文字。"),
]


def run(tag, prompt, images=()):
    os.makedirs(f"{DATA}/codex-runs", exist_ok=True)
    open(f"{DATA}/codex-runs/{tag}.prompt.md", "w").write(prompt)
    cmd = ["codex", "exec", "--skip-git-repo-check", "-s", "workspace-write", "-C", DATA,
           "--enable", "image_generation", "-c", 'model_reasoning_effort="medium"',
           "-o", f"{DATA}/codex-runs/{tag}.last.md"]
    for im in images: cmd += ["-i", im]
    cmd += ["-"]
    with open(f"{DATA}/codex-runs/{tag}.log", "w") as log:
        r = subprocess.run(cmd, input=prompt, text=True, stdout=log, stderr=subprocess.STDOUT)
    print(tag, "exit", r.returncode)
    return r.returncode


def main():
    os.makedirs(f"{DATA}/pictures", exist_ok=True)
    if sys.argv[1] == "sample":
        lines = [f"{i + 1}. 输出到 {path}：{text}" for i, (path, text) in enumerate(SAMPLE)]
        sys.exit(run("sample", PRE + "按顺序做（第 2 张要用第 1 张做参考图）：\n\n" + "\n\n".join(lines)))


if __name__ == "__main__":
    main()
