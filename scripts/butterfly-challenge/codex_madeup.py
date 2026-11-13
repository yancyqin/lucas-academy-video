#!/usr/bin/env python3
"""Round 2 (Yancy 2026-11-11): 10 made-up butterflies, not copies of the 10 real clips.

  codex_madeup.py specs            print the 10 random specs (fixed seed)
  codex_madeup.py run [rNN ...]    Codex draws them (5 parallel runs, 2 each) -> ai/rNN.png

「生成的蝴蝶不要和10个真实蝴蝶类似，随机生成」+「尽量做 made-up 但是接近真实的，让 AI 不好分辨」:
each picture is an invented species that could pass for real, in a random scene. Body plan, colours, pose, perch,
light and framing are drawn with a fixed seed so the set is random but reproducible. No reference images.
"""
import os, random, subprocess, sys
from concurrent.futures import ThreadPoolExecutor

DATA = "/Users/yqin/repo/playground/lucas-academy-video-data/butterfly-challenge"
SEED = 20261112

BODY = ["凤蝶类（后翅带尾突）", "蛱蝶类（翅缘略呈波浪）", "粉蝶类（翅形圆润）", "灰蝶类（小型，后翅有细尾）",
        "斑蝶类（翅长而圆）", "眼蝶类（翅上有小眼斑）", "弄蝶类（身体粗壮、翅小）", "蛱蝶类（前翅尖、翅形有棱角）"]
COLOR = ["铜橙色底，翅缘烟灰色，中间一条断续的奶白斑带", "柠檬黄底，宽黑色外缘，后翅几个橙点",
         "紫褐色底，前翅顶角一串小白点", "橄榄绿和赭石色交错的细斑纹", "砖红色底，黑色翅脉很明显",
         "象牙白底，翅基带一点淡紫色，外缘细黑线", "深巧克力色底，后翅一排天蓝色小斑", "灰白底，前翅有两条锯齿状深灰横带",
         "深墨绿色底，前翅散着金黄色小点", "浅肉粉色底，翅脉褐色，外缘有一圈小黑三角"]
POSE = ["翅膀完全平摊打开", "翅膀合拢、露出腹面、侧面看", "翅膀半张", "刚要起飞，翅膀微微动态模糊"]
PERCH = ["一簇野生小雏菊上", "一片宽大的绿叶上", "一块长着青苔的石头上", "溪边湿润的泥地上吸水", "一根枯草茎的顶端",
         "一朵粉色的马缨丹上", "一截粗糙的树皮上", "一颗熟透裂开的芒果上", "一簇紫色的薰衣草上", "一朵橙色的万寿菊上"]
LIGHT = ["正午很硬的阳光，阴影很深", "阴天的柔和光", "树林里斑驳的光斑", "逆光，翅膀边缘透亮", "傍晚的暖光"]
FRAME = ["特写，蝴蝶占画面宽度的一半左右", "中景，蝴蝶占画面宽度的四分之一左右，周围环境看得清"]

AVOID = ("不要像这十种真实蝴蝶：玻璃翼蝶（透明翅）、蓝摩门凤蝶（黑翅配浅蓝白后翅黑斑）、孔雀石蝶（绿色斑块）、"
         "豹纹蛱蝶（橙黄底黑圆斑）、孔雀蛱蝶（四个大眼斑）、眼灰蝶（灰色腹面橙色小月牙）、红斑紫蛱蝶（蓝黑金属光泽）、"
         "美洲黑凤蝶（黑底黄斑带）、红带袖蝶（黑底红带黄带）、鸟翼凤蝶（翠绿和黑）。")

PRE = ("这是自动运行，没有人能回答问题：不要提问，直接把下面每一张都做完。"
       "用内置的图像生成工具生成。生成的图会先存在 ~/.codex/generated_images 里，请把每张复制到要求的输出路径，"
       "并在要求的登记文件里登记（文件名、提示词、尺寸）。最后一条消息列出每张的输出路径和实际尺寸。\n\n")

RULE = ("每一张都是一种**自己编出来的、世界上不存在的蝴蝶**，但要让人（包括懂蝴蝶的人和 AI）以为是真的，"
        "像一段真实自然纪录视频里截下来的一帧：\n"
        "- 解剖结构完全合理：头、复眼、末端膨大的棒状触角、胸、腹各在该在的位置；蛱蝶类、斑蝶类、眼蝶类只画四条走路的腿"
        "（前足退化缩在胸前），其他类画六条；翅脉走向符合真实蝴蝶；左右翅花纹对称。\n"
        "- 花纹像自然演化出来的：有真实蝴蝶那种规律和小变化，不要几何图案、不要太鲜艳的霓虹色、不要奇幻元素。\n"
        "- 要有真实的小瑕疵：翅缘一点磨损或缺口、鳞片有一点掉、身上有细毛。\n"
        "- 像视频截图：自然的噪点、轻微的压缩感和柔焦，景深浅、背景自然虚化；不要过度锐化、不要过分干净、不要插画感、不要摆拍感。\n"
        "- " + AVOID + "\n"
        "- 不要任何文字、水印、边框。横幅 16:9，用工具能给的最大原生尺寸，不要用软件放大。")


def specs():
    rng = random.Random(SEED)
    perch = rng.sample(PERCH, 10); color = rng.sample(COLOR, 10)
    out = {}
    for i in range(10):
        out[f"r{i + 1:02d}"] = dict(body=rng.choice(BODY), color=color[i], pose=rng.choice(POSE), perch=perch[i],
                                    light=rng.choice(LIGHT), frame=rng.choice(FRAME))
    return out


def describe(s):
    return f"{s['body']}；颜色和花纹大致是：{s['color']}；{s['pose']}，停在{s['perch']}；{s['light']}；{s['frame']}。"


def run(tag, keys, sp):
    os.makedirs(f"{DATA}/codex-runs", exist_ok=True)
    lines = [f"{i + 1}. 输出到 ai/{k}.png：{describe(sp[k])}" for i, k in enumerate(keys)]
    prompt = PRE + RULE + f"\n\n登记文件：ai/generated-assets-{tag}.json。每一张：\n\n" + "\n".join(lines)
    open(f"{DATA}/codex-runs/{tag}.prompt.md", "w").write(prompt)
    cmd = ["codex", "exec", "--skip-git-repo-check", "-s", "workspace-write", "-C", DATA,
           "--enable", "image_generation", "-c", 'model_reasoning_effort="medium"',
           "-o", f"{DATA}/codex-runs/{tag}.last.md", "-"]
    with open(f"{DATA}/codex-runs/{tag}.log", "w") as log:
        r = subprocess.run(cmd, input=prompt, text=True, stdout=log, stderr=subprocess.STDOUT)
    print(tag, "exit", r.returncode, "made", [k for k in keys if os.path.exists(f"{DATA}/ai/{k}.png")], flush=True)


def main():
    sp = specs()
    if len(sys.argv) > 1 and sys.argv[1] == "specs":
        for k, s in sp.items():
            print(k, describe(s))
        return
    if len(sys.argv) < 2 or sys.argv[1] != "run":
        sys.exit(__doc__)
    keys = sys.argv[2:] or list(sp)
    os.makedirs(f"{DATA}/ai", exist_ok=True)
    batches = [keys[i:i + 2] for i in range(0, len(keys), 2)]
    with ThreadPoolExecutor(max_workers=5) as ex:
        list(ex.map(lambda b: run("madeup-" + "+".join(b), b, sp), batches))


if __name__ == "__main__":
    main()
