#!/usr/bin/env python3
"""Round 7 (Yancy 2026-11-12, on round 6's Astra 7/10 · Fable 5/10: "Yes, round 7"; target both <= 6/10).

  codex_scene.py specs            print pair, real photo, AI slot and spec for all 10 (check before drawing)
  codex_scene.py run [wNN ...]    Codex draws them -> ai/wNN.png

Same real photos, same AI species and the same pairing as round 6 (blind_test.assignment, seed 20261113); slot wNN
is round 6's vNN. What changes is the look, taken pair by pair from the real partner instead of one rule for all:
  - Round 6's AI pictures had small butterflies (30-40 % of the width) on busy brown weeds and dry leaves; the real
    photos fill 55-85 % of the width on clean green bokeh, rock, gravel or a pale background. Each AI picture now gets
    its partner's setting type, light and butterfly size, described in words (the real photo is never shown to Codex,
    so the butterflies cannot copy each other; round 1's look-alikes were rejected).
  - What both models called "real" in round 6: uneven or missed focus, an awkwardly clipped wing, harsh blown-out sun,
    one wing blurred while the body is sharp, worn wing edges. What they called "AI": too smooth, wing overlap that
    looks wrong, symmetric blur on a top-down open-wing butterfly (v10). So the flaws are spread: 5 of 10 get one wing
    blurred in a side or three-quarter view (never top-down, never both wings alike), the other 5 get a different
    camera flaw. No real photo has blur, so more blur would teach viewers "blur = AI".
Blur slots are chosen by hand where the pose allows it (round 6 drew 4 at random).
"""
import os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(__file__))
import blind_test as bt  # noqa: E402
import codex_hdphoto as r6  # noqa: E402
import codex_realistic as r3  # noqa: E402

DATA = r3.DATA

RULE = ("每一张都要像**自然爱好者用相机加微距镜头拍的一张真实照片**（像 iNaturalist 上拍得好的观察照片），让人和 AI 都看不出是生成的：\n"
        "- 蝴蝶是一种**真实存在的常见物种**（下面写明了），翅膀的形状、花纹、颜色都要和这个物种的真实样子一模一样，"
        "正面和反面不要画混；前翅压在后翅上面，翅膀重叠的地方结构要对；头、复眼、末端膨大的棒状触角、身体、腿都画对"
        "（蛱蝶科、斑蝶只露四条走路的腿，其他六条）。\n"
        "- **蝴蝶很大**：占画面宽度的一半到三分之二。景深很浅：对焦在蝴蝶的头和身体上，离镜头远的翅尖或一根触角可以有一点点虚；"
        "背景是自然的虚化，按下面每一张写的场景来，**背景干净简单，不要杂草、枯叶、乱枝条堆满画面**。\n"
        "- 颜色自然，不要过分饱和，不要过度锐化，不要 CG、不要插画感。翅缘有一点磨损，鳞片有一点掉，身上有细毛；"
        "左右翅因为角度不同不完全一样；有一点点相机的噪点。\n"
        "- 构图像真人拍的，不要太工整；下面每一张写了它的“相机小毛病”，照着做。\n"
        "- 不要任何文字、水印、边框。横幅 16:9，用工具能给的最大原生尺寸，不要用软件放大。")

BLUR = ("**这一张蝴蝶正在扇翅膀**：侧面或四分之三角度，不是从正上方俯拍。只有一边的翅膀在动，"
        "沿着扇动的方向拉出明显的动态模糊残影，模糊是不对称的；另一边翅膀、头、复眼、身体、腿、触角都是清楚的，"
        "就像快门不够快时拍到的真实照片。")

# Keyed by pair number n (blind_test.assignment). Each line: the partner photo's setting, light and size, in words,
# then this picture's camera flaw. "blur" pictures use BLUR as their flaw.
SCENE = {
    1: dict(pose="正在吸花蜜", scene="停在一朵很大的橙红色大丽花上，花占了画面一大块；背景是深绿色的叶子，有暗影",
            light="晴天正午的直射阳光，反差大，颜色很亮", flaw=None, blur=True),
    2: dict(pose="翅膀合拢，侧面，正在吸花蜜，口器伸进花里", scene="停在一簇紫红色的小花上，蝴蝶在画面右边；背景是均匀、柔和的浅绿色虚化",
            light="明亮的散射光", flaw="构图偏：一只翅膀的上沿被画面上边缘切掉一点", blur=False),
    3: dict(pose="翅膀合拢，侧面，正在吸花蜜", scene="停在一朵毛茸茸的白色小花球上；背景是很暗的树荫，夹着几块被太阳照亮的叶子",
            light="正午很硬的太阳光，反差很大", flaw="白色的花和浅色的翅膀有一点过曝，高光发白没有细节", blur=False),
    4: dict(pose="翅膀张开晒太阳，四分之三角度", scene="停在一片很大的浅绿色叶子上，叶子占了大半个画面，叶子上有蝴蝶的影子；背景是虚化的绿叶",
            light="明亮柔和的散射光", flaw=None, blur=True),
    5: dict(pose="正在吸花蜜，四分之三角度", scene="停在一朵紫色的蓟花上；背景是虚化的绿草和绿叶",
            light="晴天上午的阳光", flaw=None, blur=True),
    6: dict(pose="翅膀合拢，侧面", scene="停在一块灰白色的石头上，旁边有小碎石和几根小枯枝；整个画面颜色偏灰、偏淡，不鲜艳",
            light="阴天的平光", flaw="对焦有一点点没对准：前面的石头最清楚，蝴蝶稍微软一点", blur=False),
    7: dict(pose="翅膀半张，四分之三角度", scene="停在一根细长的绿色草茎上，旁边有几根绿茎；背景是很淡的灰白色虚化",
            light="阴天的柔光", flaw=None, blur=True),
    8: dict(pose="翅膀张开，停在地上吸水", scene="停在砂石地上，地上有小石子、泥土和几根干松针；整个画面颜色偏灰、偏淡",
            light="阴天的平光", flaw="整张照片有一点点软，没有特别锐利；一只后翅的边被画面下边缘切掉一点", blur=False),
    9: dict(pose="翅膀合拢，侧面", scene="停在一片有锯齿边的绿叶上，旁边有一朵小白花；背景是很暗的树丛，几乎是黑的",
            light="相机闪光灯打亮了蝴蝶和前面的叶子，后面很快暗下去", flaw="闪光灯在翅膀上有一点反光，一只翅尖被画面左边缘切掉一点",
            blur=False),
    10: dict(pose="正在吸花蜜，四分之三角度", scene="停在一小簇白色的花上，旁边是一片很大、有光泽的绿叶；背景是均匀的绿色虚化",
             light="明亮的散射光", flaw=None, blur=True),
}


def specs():
    species = {k: s["species"] for k, s in r6.specs().items()}  # vNN -> species (round 3/4/6)
    out = {}
    for a in bt.assignment():
        w = "w" + a["slot"]
        out[w] = dict(SCENE[a["n"]], n=a["n"], real=a["key"], species=species["v" + a["slot"]])
    return out


def describe(s):
    d = f"物种：{s['species']}。{s['pose']}；{s['scene']}；{s['light']}。"
    return d + (BLUR if s["blur"] else f"翅膀是静止的，清楚。相机小毛病：{s['flaw']}。")


def run(tag, keys, sp):
    os.makedirs(f"{DATA}/codex-runs", exist_ok=True)
    lines = [f"{i + 1}. 输出到 ai/{k}.png：{describe(sp[k])}" for i, k in enumerate(keys)]
    prompt = r3.PRE + RULE + f"\n\n登记文件：ai/generated-assets-{tag}.json。每一张：\n\n" + "\n".join(lines)
    open(f"{DATA}/codex-runs/{tag}.prompt.md", "w").write(prompt)
    cmd = ["codex", "exec", "--skip-git-repo-check", "-s", "workspace-write", "-C", DATA,
           "--enable", "image_generation", "-c", 'model_reasoning_effort="medium"',
           "-o", f"{DATA}/codex-runs/{tag}.last.md", "-"]
    with open(f"{DATA}/codex-runs/{tag}.log", "w") as log:
        r = subprocess.run(cmd, input=prompt, text=True, stdout=log, stderr=subprocess.STDOUT)
    print(tag, "exit", r.returncode, "made", [k for k in keys if os.path.exists(f"{DATA}/ai/{k}.png")], flush=True)


def main():
    sp = specs()
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "specs":
        for k, s in sorted(sp.items(), key=lambda kv: kv[1]["n"]):
            print(f"pair {s['n']:2d}  real {s['real']:22s} AI {k}  blur={s['blur']}\n    {describe(s)}")
        print("blur count", sum(s["blur"] for s in sp.values()))
    elif cmd == "run":
        keys = sys.argv[2:] or sorted(sp)
        batches = [keys[i:i + 2] for i in range(0, len(keys), 2)]
        with ThreadPoolExecutor(max_workers=5) as ex:
            list(ex.map(lambda b: run("scene-" + "+".join(b), b, sp), batches))
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
