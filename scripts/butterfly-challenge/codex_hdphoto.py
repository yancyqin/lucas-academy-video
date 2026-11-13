#!/usr/bin/env python3
"""Round 6 (Yancy 2026-11-12): 「真实的蝴蝶找真实的高清照 wing 尽量不blur codex生成图也告诉他 让他掺杂一些wing blur的
现在就是博弈 我希望不要超过6/10」.

  codex_hdphoto.py specs            print the 10 specs
  codex_hdphoto.py run [vNN ...]    Codex draws them -> ai/vNN.png
  codex_hdphoto.py redraw <cand>…   replacement candidates (see redraws) -> ai/<cand>.png

The real side is now sharp iNaturalist photographs (inat_photos.py). Round 5's last tell was motion blur: real video
frames had blurred flapping wings, AI butterflies were frozen. So now the real photos are sharp, and a random 4 of
the 10 AI pictures get one wing caught mid-flap with motion blur. Same species, perch, light and framing as round 4
(codex_macro.specs, slot vNN = tNN), so the pairing stays the same; the look is a naturalist's high-resolution
photograph, not a video frame, and there is no H.264 pass.
"""
import os, random, subprocess, sys
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(__file__))
import codex_macro as r4  # noqa: E402
import codex_realistic as r3  # noqa: E402

DATA = r3.DATA
SEED = 20261112
N_BLUR = 4

RULE = ("每一张都要像**自然爱好者用相机加微距镜头拍的一张真实高清照片**（像 iNaturalist 上拍得好的观察照片），让人和 AI 都看不出是生成的：\n"
        "- 蝴蝶是一种**真实存在的常见物种**（下面写明了），翅膀的形状、花纹、颜色都要和这个物种的真实样子一模一样，"
        "正面和反面不要画混；头、复眼、末端膨大的棒状触角、身体、腿都画对（蛱蝶科、斑蝶只露四条走路的腿，其他六条）。\n"
        "- 近景：蝴蝶占画面宽度的三分之一到一半，对焦在蝴蝶身上，蝴蝶清楚；背景自然虚化。颜色自然、明亮，不要过分饱和。\n"
        "- **像真照片，不要完美**：翅缘有一点磨损或小缺口，鳞片有一点掉，身上有细毛；左右翅因为角度不同不完全一样；"
        "背景里有普通的杂草、枯叶、杂乱的枝条，不要每样东西都好看；有一点点相机的噪点。不要 CG、不要插画感、不要过度锐化。\n"
        "- 不要任何文字、水印、边框。横幅 16:9，用工具能给的最大原生尺寸，不要用软件放大。")
BLUR = ("**这一张蝴蝶正在扇翅膀**：一边或两边翅膀因为在动，有明显的动态模糊（翅膀边缘拉出模糊的残影），"
        "但头、身体和停着的脚是清楚的，就像快门不够快时拍到的真实照片。")


def specs(current=True):
    """The 10 round-6 specs. current=True gives what ai/vNN.png holds now (CURRENT: redrawn slots)."""
    base = r4.specs()
    rng = random.Random(SEED)
    blur = set(rng.sample(sorted(base), N_BLUR))
    out = {}
    for k, s in base.items():
        v = "v" + k[1:]
        s = dict(s)
        s["blur"] = k in blur
        if s["blur"] and s["pose"].startswith("翅膀合拢"):
            s["pose"] = "翅膀正要张开"
        out[v] = s
    if current:
        rd = redraws(out)
        for slot, cand in CURRENT.items():
            out[slot] = rd[cand]
    return out


# What ai/vNN.png holds now when it is not the original round-6 picture (candidate picked by eye; the rest in _retired/).
CURRENT = {"v05": "v05c", "v04": "v04t", "v09": "v09u", "v08": "v08u", "v10": "v10w"}  # 11-12: sharp 4, closed-wing 5 and 7, open-wing 8

# 2026-11-12, Yancy: 「把3和8 按照clue再改一下 争取让Astra 猜错」. What the two models said on pairs 3 and 8 (round 6 and
# the retest), turned into instructions for the AI side:
#   #3 real Malachite — Astra: "irregular wing damage", "harsh, uneven exposure", "natural flower occlusion"; Fable: real
#      has blown-out sun, tattered edges, the flower hiding part of the butterfly; AI v05 "overly clean, smooth",
#      "smudgy wing markings", "suspiciously clean and idealized".
#   #8 real Black Swallowtail — Astra: "natural image noise/softness", "consistent wing anatomy", AI v10b "tangled wing
#      details"; Fable: real has missed focus, slight blur, awkward crop, messy gravel; AI "too flawlessly polished".
CLUE3 = ("这一张要**乱、不完美**，像野外随手拍、没修过的照片：几根花枝和花穗挡在蝴蝶前面，遮住翅膀的一小部分；"
         "正午的硬光，曝光不均，翅膀和花上有一块高光过曝发白，阴影很深；翅缘明显磨损，有一两个小缺口；"
         "翅膀上的小褐色斑点要清楚、边缘利落，不要糊成一片；整张不要干净、不要理想化。")
CLUE8 = ("这一张要**普通、不精致**，像随手拍的一张没修过的照片（这一张例外：焦点不在蝴蝶身上）：对焦稍微没对准，"
         "焦点落在蝴蝶前面一点的地上，蝴蝶整体有一点点软；整张有明显的相机噪点；构图随便，一只翅尖被画面边缘切掉一点；"
         "翅膀的结构简单清楚，前翅、后翅分得开，不要几片翅膀叠在一起、花纹缠成一团；不要精致、不要完美、不要理想化。")


# 2026-11-12, Yancy on the film's round 6: 「AI错的几个太离谱了，不要翅膀虚 再测测试试 生成图片好一些，更逼真」: the AI
# pictures the models fell for because of motion blur (pairs 4, 5, 7) or overall softness (pair 8) are redrawn sharp.
SHARP = ("这一张要**清清楚楚、非常逼真**，像 iNaturalist 上拍得最好的一张照片：翅膀静止，翅膀、身体、头、触角、腿全部清楚，"
         "没有任何动态模糊，也没有失焦；翅膀的花纹、鳞片、翅脉都和这个物种真实的样子一模一样，前后翅、左右翅的结构都对；"
         "身体比例对，腿和触角自然。颜色自然，不要过分饱和，不要过度锐化；背景是自然的虚化。")


CLEAN = ("两根触角都完整、都看得见；翅膀的重叠和真蝴蝶一样（合着翅膀时后翅在前、前翅在后，只露出前翅的上半部分）；"
         "翅缘有一点自然的磨损，不要每一片鳞片都完美；不要摆拍感。")


OPEN = ("两根触角都完整、都看得见；四片翅膀张开，前翅、后翅分得清清楚楚，不互相乱叠；左右翅的角度、形状因为透视不完全一样；"
        "翅缘有自然的磨损和一两个小缺口，有几处鳞片掉了一点；像随手拍到的真照片，不要摆拍、不要精修、不要理想化。")


def redraws(sp):
    """Replacement candidates for the film's round 6; I pick one per slot by eye (never by asking the test models),
    it becomes vNN.png (CURRENT), the old picture and the unused candidates go to _retired/.
      v10a/v10b (2026-11-12, 「round 6 把第8 替换一下 有点太假」): pair 8's Painted Lady without the symmetric blur.
      v05c/v05d, v10c/v10d (2026-11-12, 「把3和8 按照clue再改一下」): pairs 3 and 8 redrawn from the models' clues.
      v04s/t, v09s/t, v08s/t, v10s/t (2026-11-12, 「不要翅膀虚」): pairs 4, 5, 7, 8 redrawn sharp and realistic.
      v09u/v, v08u/v, v10u/v (2026-11-12, 「猜对的 5 7 8 再换一下试试」): new pictures for pairs 5, 7, 8.
      v10w/x (2026-11-12, 「8 换一个展开翅膀的」): pair 8 with open wings, plain and natural."""
    v10 = dict(sp["v10"], blur=False)
    v05 = dict(sp["v05"], blur=False)
    return {"v10a": dict(v10),  # same pose as before, wings still
            "v10b": dict(v10, pose="翅膀半张，四分之三角度"),
            "v05c": dict(v05, pose="翅膀合拢，侧面，正在吸花蜜", light="正午很硬的直射阳光", frame="蝴蝶偏在画面一边，构图随意",
                         extra=CLUE3),
            "v05d": dict(v05, pose="翅膀合拢，侧面，正在吸花蜜", perch="一簇白色的鬼针草花", light="正午很硬的直射阳光",
                         frame="蝴蝶偏在画面一边，构图随意", extra=CLUE3),
            # sharp redraws (Yancy 11-12: 不要翅膀虚); s = round 6's own scene, t = another natural pose
            **{f"{k}{c}": dict(sp[k], blur=False, extra=SHARP, **({"pose": pose} if pose else {}))
               for k, poses in (("v04", ("翅膀张开晒太阳", "翅膀半张，四分之三角度")),
                                ("v09", ("正在吸花蜜，口器伸进花里，翅膀半张", "翅膀张开晒太阳")),
                                ("v08", ("翅膀半张", "翅膀张开晒太阳")),
                                ("v10", ("翅膀完全张开", "翅膀半张，四分之三角度")))
               for c, pose in zip("st", poses)},
            # 11-12 again, 「猜对的 5 7 8 再换一下试试 生成别的试试」: both models saw through the sharp 5/7/8 (Fable: a muddled
            # wing with one antenna, a forewing under the hindwing, too polished). What fooled them was simple, clean anatomy
            # (wings closed side-on in 2 and 9, open flat in 4). So: u = the same species wings closed side-on, v = a species
            # not used yet (Meadow Brown, Orange-tip, Monarch; not the Old World Swallowtail, too like pair 8's real one).
            **{k: dict(base, blur=False, extra=SHARP + CLEAN, **over) for k, base, over in (
                ("v09u", sp["v09"], dict(pose="翅膀合拢，侧面，露出反面的花纹，正在吸花蜜", perch="一朵橙色万寿菊")),
                ("v09v", sp["v09"], dict(species="草地褐蝶 Meadow Brown (Maniola jurtina)", pose="翅膀合拢，侧面，露出反面",
                                          perch="一朵紫色的矢车菊")),
                ("v08u", sp["v08"], dict(pose="翅膀合拢，侧面，露出反面的花纹", perch="一枝紫色薰衣草")),
                ("v08v", sp["v08"], dict(species="红襟粉蝶 Orange-tip 雄蝶 (Anthocharis cardamines)",
                                          pose="翅膀合拢，侧面，露出反面绿白相间的斑驳花纹，前翅尖露出一点橙色",
                                          perch="一朵淡紫色的草地碎米荠")),
                ("v10u", sp["v10"], dict(pose="翅膀合拢，侧面，露出反面的花纹", perch="一朵黄色金鸡菊")),
                ("v10v", sp["v10"], dict(species="帝王斑蝶 Monarch (Danaus plexippus)", pose="翅膀张开晒太阳，从斜上方拍",
                                          perch="一簇橙色的马利筋花")))},
            # 11-12, 「8 换一个展开翅膀的 别都是夹着翅膀的 再测一次8」: open wings again, but plain and natural, not polished
            "v10w": dict(sp["v10"], blur=False, extra=SHARP + OPEN, pose="翅膀完全张开，平摊着晒太阳，从斜上方拍",
                         perch="路边一块晒热的灰石头", light="晴天上午的阳光，有一点硬"),
            "v10x": dict(sp["v10"], blur=False, extra=SHARP + OPEN, pose="翅膀张开，四分之三角度，正在吸花蜜",
                         perch="一丛开败了一半的紫色醉鱼草花穗", light="明亮的阴天光"),
            "v10c": dict(v10, pose="翅膀完全张开，平摊着晒太阳，从斜上方拍", perch="路边的砂石地",
                         light="阴天的平光，颜色偏灰", frame="蝴蝶不在正中", extra=CLUE8),
            "v10d": dict(v10, pose="翅膀合拢，侧面，露出反面的花纹", perch="路边的砂石地",
                         light="阴天的平光，颜色偏灰", frame="蝴蝶不在正中", extra=CLUE8)}


def describe(s):
    d = f"物种：{s['species']}。{s['pose']}，停在{s['perch']}上；{s['light']}；{s['frame']}。"
    if s.get("extra"):  # the clue redraws say how sharp it is themselves
        return d + "翅膀是静止的，没有动态模糊。" + s["extra"]
    return d + (BLUR if s["blur"] else "翅膀是静止的，清楚。")


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
        for k, s in sp.items():
            print(k, describe(s))
    elif cmd == "redraw":  # redraw <cand> [<cand> ...] -> ai/<cand>.png, two per Codex run, in parallel
        rd = redraws(specs(current=False))
        keys = sys.argv[2:]
        for k in keys:
            print(k, describe(rd[k]))
        batches = [keys[i:i + 2] for i in range(0, len(keys), 2)]
        with ThreadPoolExecutor(max_workers=5) as ex:
            list(ex.map(lambda b: run("hdphoto-redraw-" + "+".join(b), b, rd), batches))
    elif cmd == "run":
        keys = sys.argv[2:] or list(sp)
        batches = [keys[i:i + 2] for i in range(0, len(keys), 2)]
        with ThreadPoolExecutor(max_workers=5) as ex:
            list(ex.map(lambda b: run("hdphoto-" + "+".join(b), b, sp), batches))
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
