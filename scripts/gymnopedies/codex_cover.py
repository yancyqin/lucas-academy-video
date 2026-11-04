#!/usr/bin/env python3
"""The dance-class cover background: the owner's still (Muse dance-class frame 22, owner 11-03 「use the above … you can
call codex to generate for 封面」) is nearly square, and a 16:9 crop loses the mirror and the tutu, so Codex widens it.
Codex's whole picture is the background: pasting the real frame back over its middle cut the hands of the dancers at the
joins (owner 11-03: 「第二个封面舞者的手要显示全，不要 cut off」), and Codex redraws every figure whole.

Owner 11-03 later: 「封面文字放到右上井字格构图点，这样构图比较有美感」 — on both pictures that point fell on a face (her crown,
the teacher's head), so `thirds` has Codex recompose each cover: same people and poses, every hand whole, the dancers in the
left two-thirds and the upper-right third left as quiet backdrop or wall for the title.

usage: .venv-reframe/bin/python scripts/gymnopedies/codex_cover.py run      Codex -> covers/dance-class-wide.png (1536x1024)
       .venv-reframe/bin/python scripts/gymnopedies/codex_cover.py crop     -> covers/bg-dance-class.png (16:9)
       .venv-reframe/bin/python scripts/gymnopedies/codex_cover.py thirds etoile|dance-class   -> covers/thirds-<id>.png
"""
import subprocess, sys
import cv2

DATA = "/Users/yqin/repo/playground/lucas-academy-video-data/satie-gymnopedies"
FRAME = f"{DATA}/covers/dance-class-f22.png"
WIDE = f"{DATA}/covers/dance-class-wide.png"

PROMPT = ("这是自动运行，没有人能回答问题：不要提问，直接做完。用内置的图像生成工具，参考图就是附带的这张照片（1870 年代巴黎歌剧院"
          "舞蹈课的写实剧照）。把它向左右两边延伸成横幅：原图的全部内容放在画面正中间，大小、位置都不变，每个人的脸、姿态、服装、"
          "头上的花、光线和颜色都保持原样，不要重画、不要美化、不要移动任何人；只在左右两边补出同一个排练厅合理的延续——左边：浅绿色"
          "的墙、钢琴和坐在钢琴边的舞者、木地板；右边：墙、几个站着或坐着休息的穿白纱裙的舞者、木地板。透视、光线、颗粒感和原图连续，"
          "看不出接缝；照片级写实、彩色，不要油画感，不要文字、水印、边框。用最大的横幅尺寸（1536×1024），保存成 PNG 到 "
          "covers/dance-class-wide.png。做完自己检查：中间的人物有没有被改动、两边新补的人脸和手有没有变形、接缝自不自然；不合格就重画。"
          "最后一条消息写输出路径和实际尺寸。")

def run():
    cmd = ["codex", "exec", "--skip-git-repo-check", "-s", "workspace-write", "-C", DATA, "--enable", "image_generation",
           "-c", 'model_reasoning_effort="medium"', "-o", f"{DATA}/codex/runs/cover-dance-class.last.md", "-i", FRAME, "-"]
    open(f"{DATA}/codex/runs/cover-dance-class.prompt.md", "w").write(PROMPT)
    with open(f"{DATA}/codex/runs/cover-dance-class.log", "w") as log:
        r = subprocess.run(cmd, input=PROMPT, text=True, stdout=log, stderr=subprocess.STDOUT)
    print("codex exit", r.returncode)

THIRDS = {   # id: (reference image, what the picture is, which figures go where)
    "etoile": (f"{DATA}/covers/etoile-f12-full.png",
               "巴黎歌剧院舞台上的首席舞者（1870 年代的写实剧照）：她仰头闭眼，头戴花环、系黑色颈带，右臂高高举起，左臂向侧面伸出，"
               "白色纱裙上点缀着花；左后方侧幕边站着穿黑色燕尾服的男人和一个舞者，后面还有几个舞者的纱裙和腿，背景是画着树林和石桥的布景。",
               "首席舞者放在画面左边三分之二里，身体从举起的手一直到纱裙下摆都在画面里；黑衣男人和其他舞者放在她左后方。"),
    "dance-class": (f"{DATA}/covers/dance-class-wide.png",
                    "1870 年代巴黎歌剧院排练厅里的舞蹈课（写实剧照）：浅绿色的墙、木地板、墙上的大镜子；前景正中低头整理纱裙的舞者，"
                    "钢琴边背对我们的舞者，椅子上系鞋带的舞者，拄着手杖的白发老教师，台阶上一群舞者和穿黑衣的母亲们，窗边的几个舞者。",
                    "所有人物放在画面左边三分之二和下半部分：前景整理纱裙的舞者偏左，老教师在中间偏右的下方；台阶上的那群人移到画面中部、不要伸进右上角。"),
}

def thirds(cid):
    ref, scene, layout = THIRDS[cid]
    small = f"{DATA}/codex/refs/cover-{cid}.jpg"
    im = cv2.imread(ref); k = 2048 / max(im.shape[:2])
    if k < 1: im = cv2.resize(im, None, fx=k, fy=k, interpolation=cv2.INTER_AREA)
    cv2.imwrite(small, im, [cv2.IMWRITE_JPEG_QUALITY, 92])
    prompt = ("这是自动运行，没有人能回答问题：不要提问，直接做完。用内置的图像生成工具，参考附带的这张图，生成一张 YouTube 封面用的"
              f"横幅照片（1536×1024）。场景：{scene}人物的脸、表情、发型、服装、姿势都和参考图一样，不要换人。构图：{layout}"
              "画面右上三分之一（右上角那一格，也就是标题要放的地方）要安静、留白：只有布景、墙或天花板，没有人物、没有手、没有脸、没有镜子或画框。"
              "每个人的手都完整地在画面里，不要被边缘切掉；手和脸形状自然正确。照片级写实、彩色、暖色的光，不要油画感，不要文字、水印、边框。"
              f"保存成 PNG 到 covers/thirds-{cid}.png。做完自己检查：右上角那一格是不是空的、人物和参考图像不像、手是否完整；不合格就重画。"
              "最后一条消息写输出路径和实际尺寸。")
    open(f"{DATA}/codex/runs/cover-thirds-{cid}.prompt.md", "w").write(prompt)
    cmd = ["codex", "exec", "--skip-git-repo-check", "-s", "workspace-write", "-C", DATA, "--enable", "image_generation",
           "-c", 'model_reasoning_effort="medium"', "-o", f"{DATA}/codex/runs/cover-thirds-{cid}.last.md", "-i", small, "-"]
    with open(f"{DATA}/codex/runs/cover-thirds-{cid}.log", "w") as log:
        r = subprocess.run(cmd, input=prompt, text=True, stdout=log, stderr=subprocess.STDOUT)
    print(cid, "codex exit", r.returncode)

def crop(y0=120):
    """16:9 band of Codex's 3:2 picture: from just under the mirror's top to the front dancer's shoes — every hand inside."""
    wide = cv2.imread(WIDE); h = round(wide.shape[1] * 9 / 16)
    cv2.imwrite(f"{DATA}/covers/bg-dance-class.png", wide[y0:y0 + h])
    print("bg-dance-class.png", wide.shape[1], h, "from y", y0)

if __name__ == "__main__":
    if sys.argv[1] == "thirds": thirds(sys.argv[2])
    else: {"run": run, "crop": crop}[sys.argv[1]]()
