#!/usr/bin/env python3
"""Codex makes one AI butterfly picture per real frame (蝴蝶挑战：猜一猜哪些蝴蝶是真的).

  codex_fakes.py run [key ...]     all ten (5 parallel Codex runs, 2 pictures each), or only the given keys

Each real frame (real/<key>.png, picked from the owner's 10 clips) goes in as a reference image. Codex draws a new
picture of the same species in a similar shot and light from scratch (no edit or trace of the reference), so each pair
is a fair "which one is real?" question. Output ai/<key>.png; logs + prompts in codex-runs/.
"""
import os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor

DATA = "/Users/yqin/repo/playground/lucas-academy-video-data/butterfly-challenge"

# key: (species for the model, what the real frame shows)
ITEMS = {
    "g1-greta-oto-commons": ("玻璃翼蝶 glasswing butterfly (Greta oto)",
        "侧面停在一枝紫色小花上吸蜜，翅膀透明，透出背后虚化的绿叶，前翅有白色斑带、翅缘深褐色，背景明亮的绿色虚化"),
    "p08-2901459": ("蓝色美凤蝶 Blue Mormon (Papilio polymnestor)",
        "从正上方偏斜的角度看，翅膀完全张开，停在热带林下的一片绿叶上，周围是密密的野草和阔叶，自然日光"),
    "p15-5129671": ("绿帘蛱蝶 Malachite butterfly (Siproeta stelenes)",
        "停在一簇白色小花上，翅膀半张，黄绿色斑块和深褐色，背景是虚化的绿叶和一块暖棕色"),
    # first run guessed Common Leopard and drew an orange fritillary; the insect is pale yellow with square dark spots
    "p16-5241558": ("物种未定，照参考图的样子画：翅膀浅黄到橙黄色，布满黑褐色的方形和圆形斑点，后翅靠近身体处有白色斑块，"
                    "翅缘呈波浪状、带深色镶边，身体细长、灰褐色",
        "翅膀平展停在一片绿叶上，旁边有两朵白色小绒球花，背景是大片阔叶，明亮日光"),
    "p17-7855586": ("孔雀蛱蝶 European Peacock (Aglais io)",
        "停在一朵黄色蒲公英上，翅膀张开，四个眼斑清楚，背景是深绿色虚化的羽状叶"),
    "p18-8450772": ("普通眼灰蝶 Common Blue (Polyommatus icarus)，翅膀合起露出腹面",
        "侧面停在一根毛茸茸的绿色草穗上，翅膀合拢，灰褐色腹面带黑点和一圈橙色斑，翅基泛蓝，背景是虚化的草"),
    "p26-16001770": ("红斑紫蛱蝶 Red-spotted Purple (Limenitis arthemis astyanax)",
        "停在一块石头上，翅膀张开呈 V 形，蓝黑色带金属蓝光泽，背景是浅棕色虚化的卵石"),
    "p44-38657643": ("美洲黑凤蝶 Black Swallowtail (Papilio polyxenes)",
        "停在一朵紫锥菊上吸蜜，周围是更多紫锥菊和淡紫色的美国薄荷花，色调偏灰绿、柔和、低饱和"),
    "p67-36683557": ("红带袖蝶 Postman butterfly (Heliconius erato / melpomene)",
        "侧面停在一片大绿叶的边缘，翅膀合拢，黑色底、前翅一条红带、后翅一条奶黄色细带，背景是深绿色虚化"),
    "p69-37672883": ("凯恩斯鸟翼凤蝶 Cairns Birdwing (Ornithoptera euphorion) 雄蝶",
        "在蝴蝶园里停在一簇橙色的醉鱼草花旁边，翅膀张开，翡翠绿和黑色，黄色腹部，周围有蓝色小花和灰绿色叶子"),
}

PRE = ("这是自动运行，没有人能回答问题：不要提问，直接把下面每一张都做完。"
       "用内置的图像生成工具生成。生成的图会先存在 ~/.codex/generated_images 里，请把每张复制到要求的输出路径，"
       "并在要求的登记文件里登记（文件名、提示词、尺寸）。最后一条消息列出每张的输出路径和实际尺寸。\n\n")

RULE = ("参考图是一段真实自然视频里的一帧。请生成一张新的、以假乱真的照片，看起来像同一位摄影师用同一台相机、"
        "在同一个地方拍的另一帧：同一种蝴蝶，翅膀的形状和花纹按这个物种真实的样子画；"
        "构图、蝴蝶在画面里的位置和大小、景深和背景虚化、光线和色调都和参考图接近。"
        "但不要在参考图上修改、描摹或拼贴，要从头生成：叶子和花的具体形状和位置、蝴蝶翅膀的角度都可以和参考图稍有不同。"
        "要像真实拍摄的视频截图：自然的噪点和轻微的压缩感，不要过度锐化、不要过分干净、不要插画感。"
        "不要任何文字、水印、边框。横幅 16:9，用工具能给的最大原生尺寸，不要用软件放大。")


def run(tag, keys):
    os.makedirs(f"{DATA}/codex-runs", exist_ok=True)
    lines = []
    for i, k in enumerate(keys):
        species, shows = ITEMS[k]
        lines.append(f"{i + 1}. 参考图：real/{k}.png（{shows}）。物种：{species}。输出到 ai/{k}.png。")
    prompt = (PRE + RULE + f"\n\n登记文件：ai/generated-assets-{tag}.json。每一张都按上面的要求做：\n\n" + "\n".join(lines))
    open(f"{DATA}/codex-runs/{tag}.prompt.md", "w").write(prompt)
    cmd = ["codex", "exec", "--skip-git-repo-check", "-s", "workspace-write", "-C", DATA,
           "--enable", "image_generation", "-c", 'model_reasoning_effort="medium"',
           "-o", f"{DATA}/codex-runs/{tag}.last.md"]
    for k in keys:
        cmd += ["-i", f"{DATA}/real/{k}.png"]
    cmd += ["-"]
    with open(f"{DATA}/codex-runs/{tag}.log", "w") as log:
        r = subprocess.run(cmd, input=prompt, text=True, stdout=log, stderr=subprocess.STDOUT)
    done = [k for k in keys if os.path.exists(f"{DATA}/ai/{k}.png")]
    print(tag, "exit", r.returncode, "made", done, flush=True)
    return r.returncode


def main():
    if len(sys.argv) < 2 or sys.argv[1] != "run":
        sys.exit(__doc__)
    keys = sys.argv[2:] or list(ITEMS)
    os.makedirs(f"{DATA}/ai", exist_ok=True)
    batches = [keys[i:i + 2] for i in range(0, len(keys), 2)]
    with ThreadPoolExecutor(max_workers=5) as ex:
        list(ex.map(lambda b: run("fake-" + "+".join(x.split("-")[0] for x in b), b), batches))


if __name__ == "__main__":
    main()
