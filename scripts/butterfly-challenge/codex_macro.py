#!/usr/bin/env python3
"""Round 4 (Yancy 2026-11-11, on round 3's 2/10 · 0/10: 「Use round 3 但是你把蝴蝶 zoom in 微距大图，而且色彩鲜艳一些。
现在这风格都不一样 太明显」).

  codex_macro.py specs            print the 10 specs (same species per slot as round 3, new random look)
  codex_macro.py run [tNN ...]    Codex draws them -> ai/raw/tNN.png
  codex_macro.py video            ai/raw/tNN.png -> 1920x1080 H.264 ~5 Mbps -> frame -> ai/tNN.png

Round 3's amateur phone look fooled both models, but every AI picture was the scruffy one next to a polished Pexels
clip, so the style itself was the tell. Round 4 keeps round 3's real species (slot tNN = round 3's sNN, so the pairing
stays the same) and matches the real clips' look instead: macro close-up, butterfly large in frame, soft background
blur, vivid natural colour. It keeps real-life flaws (worn wing edges, a few lost scales, hair, video softness) and the
H.264 pass, so the AI pictures carry the same compression as the real frames.
"""
import os, random, subprocess, sys
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(__file__))
import codex_realistic as r3  # noqa: E402

DATA = r3.DATA
SEED = 20261114

POSE = ["翅膀完全张开", "翅膀合拢，侧面", "翅膀半张", "正在吸花蜜，口器伸进花里"]
# bright flowers and leaves; none of the real frames' own perches (porterweed, dandelion, coneflower, buddleia)
PERCH = ["一朵粉色百日菊", "一簇红色马缨丹", "一朵黄色金鸡菊", "一簇白色野胡萝卜花", "一片嫩绿的大叶子",
         "一枝紫色薰衣草", "一朵橙色万寿菊", "一枝蓝色鼠尾草", "一朵粉紫色的波斯菊", "一簇黄色的一枝黄花"]
LIGHT = ["晴天的侧光，翅膀颜色很亮", "明亮柔和的阴天光", "逆光，翅膀边缘透亮", "上午的暖光"]
FRAME = ["蝴蝶在画面中间偏左", "蝴蝶在画面中间偏右", "蝴蝶几乎在正中"]

RULE = ("每一张都要像 **Pexels 这类网站上拍得很好的蝴蝶微距视频里截下来的一帧**（4K 摄像机 + 微距镜头），让人和 AI 都看不出是生成的：\n"
        "- 蝴蝶是一种**真实存在的常见物种**（下面写明了），翅膀的形状、花纹、颜色都要和这个物种的真实样子一模一样，"
        "正面和反面不要画混；头、复眼、末端膨大的棒状触角、身体、腿都画对（蛱蝶科、斑蝶只露四条走路的腿，其他六条）。\n"
        "- **微距近景**：蝴蝶很大，占画面宽度的一半到三分之二，翅膀上的鳞片纹理看得见；背景是柔和的虚化，一片片花和叶的颜色。\n"
        "- **色彩鲜艳**：自然光下饱和、明亮、好看的颜色，像拍得好的自然素材，不要发灰、不要暗。\n"
        "- **但要真实，不要完美**：翅缘有一点磨损或小缺口，鳞片有一点掉，身上有细毛；左右翅因为角度不同看起来不完全一样；"
        "像视频截图那样有一点点柔和，不要过度锐化，不要 CG、不要插画感。\n"
        "- 不要任何文字、水印、边框。横幅 16:9，用工具能给的最大原生尺寸，不要用软件放大。")


def specs():
    species = {k.replace("s", "t", 1): v["species"] for k, v in r3.specs().items()}
    rng = random.Random(SEED)
    perch = rng.sample(PERCH, 10)
    out = {k: dict(species=species[k], pose=rng.choice(POSE), perch=perch[i], light=rng.choice(LIGHT),
                   frame=rng.choice(FRAME)) for i, k in enumerate(sorted(species))}
    for s in out.values():
        # sulphurs and yellows (钩粉蝶, 豆粉蝶, 黄粉蝶) almost always rest with their wings closed
        if any(x in s["species"] for x in ("钩粉蝶", "豆粉蝶", "黄粉蝶")) and s["pose"] in ("翅膀完全张开", "翅膀半张"):
            s["pose"] = "翅膀合拢，侧面"
        if "叶子" in s["perch"] and "吸花蜜" in s["pose"]:  # nothing to drink on a leaf
            s["pose"] = "翅膀张开晒太阳"
    return out


def describe(s):
    return f"物种：{s['species']}。{s['pose']}，停在{s['perch']}上；{s['light']}；{s['frame']}。"


def run(tag, keys, sp):
    os.makedirs(f"{DATA}/codex-runs", exist_ok=True)
    lines = [f"{i + 1}. 输出到 ai/raw/{k}.png：{describe(sp[k])}" for i, k in enumerate(keys)]
    prompt = r3.PRE + RULE + f"\n\n登记文件：ai/raw/generated-assets-{tag}.json。每一张：\n\n" + "\n".join(lines)
    open(f"{DATA}/codex-runs/{tag}.prompt.md", "w").write(prompt)
    cmd = ["codex", "exec", "--skip-git-repo-check", "-s", "workspace-write", "-C", DATA,
           "--enable", "image_generation", "-c", 'model_reasoning_effort="medium"',
           "-o", f"{DATA}/codex-runs/{tag}.last.md", "-"]
    with open(f"{DATA}/codex-runs/{tag}.log", "w") as log:
        r = subprocess.run(cmd, input=prompt, text=True, stdout=log, stderr=subprocess.STDOUT)
    print(tag, "exit", r.returncode, "made", [k for k in keys if os.path.exists(f"{DATA}/ai/raw/{k}.png")], flush=True)


def main():
    sp = specs()
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "specs":
        for k, s in sp.items():
            print(k, describe(s))
    elif cmd == "run":
        keys = sys.argv[2:] or list(sp)
        os.makedirs(f"{DATA}/ai/raw", exist_ok=True)
        batches = [keys[i:i + 2] for i in range(0, len(keys), 2)]
        with ThreadPoolExecutor(max_workers=5) as ex:
            list(ex.map(lambda b: run("macro-" + "+".join(b), b, sp), batches))
    elif cmd == "video":
        r3.video()  # same H.264 pass, for every ai/raw/*.png
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
