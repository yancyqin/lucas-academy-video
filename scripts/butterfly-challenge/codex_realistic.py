#!/usr/bin/env python3
"""Round 3 (Yancy 2026-11-11, after round 2 scored Astra 9/10, Fable 10/10: 「那证明生成的不行！重新生成！」).

  codex_realistic.py specs            print the 10 random specs (fixed seed)
  codex_realistic.py run [sNN ...]    Codex draws them -> ai/raw/sNN.png
  codex_realistic.py video            every ai/raw/sNN.png -> one second of H.264 like the real clips -> ai/sNN.png

What gave round 2 away, from the models' own reasons: Fable named the real species 7 times and called the AI ones
"patterns that match no real species"; both called the AI ones too crisp, too clean, too symmetric, cinematic.
So round 3:
  - each AI picture shows a real, common species (random, none of the 10 real clips and no lookalikes), so species
    recognition stops working; the picture itself is still invented, with no reference photo;
  - the look of an amateur clip: phone or camcorder, focus slightly off, harsh or dull light, a little motion blur,
    wings at uneven angles, the butterfly off-centre and partly hidden;
  - the drawn picture goes through the same medium as the real frames: 1920x1080 H.264 at the real clips' bitrate
    (about 5 Mbps), and the frame is taken back out.
"""
import os, random, subprocess, sys
from concurrent.futures import ThreadPoolExecutor

DATA = "/Users/yqin/repo/playground/lucas-academy-video-data/butterfly-challenge"
SEED = 20261113

# common species with patterns an image model can get right; none of the 10 real clips or their lookalikes
SPECIES = [
    "菜粉蝶 Small White (Pieris rapae)", "钩粉蝶 Brimstone (Gonepteryx rhamni)", "橙黄豆粉蝶 Clouded Yellow (Colias croceus)",
    "红襟粉蝶 Orange-tip 雄蝶 (Anthocharis cardamines)", "红灰蝶 Small Copper (Lycaena phlaeas)",
    "斑点木蝶 Speckled Wood (Pararge aegeria)", "草地褐蝶 Meadow Brown (Maniola jurtina)",
    "白钩蛱蝶 Comma (Polygonia c-album)", "优红蛱蝶 Red Admiral (Vanessa atalanta)", "小红蛱蝶 Painted Lady (Vanessa cardui)",
    "帝王斑蝶 Monarch (Danaus plexippus)", "金凤蝶 Old World Swallowtail (Papilio machaon)",
    "宽边黄粉蝶 Common Grass Yellow (Eurema hecabe)", "金斑蝶 Plain Tiger (Danaus chrysippus)",
]
POSE = ["翅膀张开，但两边张开的角度不一样", "翅膀合拢，侧面", "翅膀半张，身体有点歪", "一边翅膀被前面的叶子挡住一小块"]
PERCH = ["路边的一丛野草花上", "一片有虫咬洞的叶子上", "花园里一朵开败了一半的花上", "水泥地缝里长出来的小花上",
         "灌木的枝条上", "一簇蓟花上", "落满灰尘的叶子上", "一朵被晒得有点蔫的向日葵上", "篱笆边的三叶草上", "一块晒热的石头上"]
LIGHT = ["正午很硬的阳光，高光有点过曝", "阴天，颜色发灰发平", "树荫下，光斑一块一块的", "傍晚，偏黄，有点暗"]
CAMERA = ["用手机拍的视频", "用家用摄像机拍的视频", "用相机的视频模式拍的，自动对焦"]
FLAW = ["对焦稍微落在蝴蝶后面的叶子上，蝴蝶本身略软", "翅膀边缘有一点动态模糊", "画面稍微有点手抖的模糊",
        "蝴蝶清楚，但背景很乱、不好看"]
FRAME = ["蝴蝶不在正中，偏左", "蝴蝶不在正中，偏右", "蝴蝶在画面里比较小，约占宽度的五分之一", "离得比较近，蝴蝶约占宽度的一半"]

PRE = ("这是自动运行，没有人能回答问题：不要提问，直接把下面每一张都做完。"
       "用内置的图像生成工具生成。生成的图会先存在 ~/.codex/generated_images 里，请把每张复制到要求的输出路径，"
       "并在要求的登记文件里登记（文件名、提示词、尺寸）。最后一条消息列出每张的输出路径和实际尺寸。\n\n")

RULE = ("每一张都要像**普通人用手机或家用摄像机随手拍的一段自然视频里截下来的一帧**，让人和 AI 都看不出是生成的：\n"
        "- 蝴蝶是一种**真实存在的常见物种**（下面写明了），翅膀的形状、花纹、颜色都要和这个物种的真实样子一模一样，"
        "正面和反面不要画混；头、复眼、末端膨大的棒状触角、身体、腿都画对（蛱蝶科、斑蝶只露四条走路的腿，其他六条）。\n"
        "- **不要好看、不要电影感、不要摆拍**：构图随意，蝴蝶不在正中；背景杂乱，有枯叶、杂草、虫咬的叶子；"
        "色彩偏平、略微发灰或高光过曝，不要高饱和；不要漂亮的奶油般虚化，景深就是手机/摄像机那种普通的样子。\n"
        "- **不要完美**：两边翅膀因为角度不同看起来不一样大；翅缘有磨损和小缺口；有一点对焦不准或动态模糊；"
        "画面有一点噪点。不要过度锐化，不要每根绒毛都清清楚楚。\n"
        "- 不要任何文字、水印、边框。横幅 16:9，用工具能给的最大原生尺寸，不要用软件放大。")


def specs():
    rng = random.Random(SEED)
    species = rng.sample(SPECIES, 10); perch = rng.sample(PERCH, 10)
    return {f"s{i + 1:02d}": dict(species=species[i], pose=rng.choice(POSE), perch=perch[i], light=rng.choice(LIGHT),
                                  camera=rng.choice(CAMERA), flaw=rng.choice(FLAW), frame=rng.choice(FRAME))
            for i in range(10)}


def describe(s):
    return (f"物种：{s['species']}。{s['camera']}；{s['pose']}，停在{s['perch']}；{s['light']}；"
            f"{s['flaw']}；{s['frame']}。")


def run(tag, keys, sp):
    os.makedirs(f"{DATA}/codex-runs", exist_ok=True)
    lines = [f"{i + 1}. 输出到 ai/raw/{k}.png：{describe(sp[k])}" for i, k in enumerate(keys)]
    prompt = PRE + RULE + f"\n\n登记文件：ai/raw/generated-assets-{tag}.json。每一张：\n\n" + "\n".join(lines)
    open(f"{DATA}/codex-runs/{tag}.prompt.md", "w").write(prompt)
    cmd = ["codex", "exec", "--skip-git-repo-check", "-s", "workspace-write", "-C", DATA,
           "--enable", "image_generation", "-c", 'model_reasoning_effort="medium"',
           "-o", f"{DATA}/codex-runs/{tag}.last.md", "-"]
    with open(f"{DATA}/codex-runs/{tag}.log", "w") as log:
        r = subprocess.run(cmd, input=prompt, text=True, stdout=log, stderr=subprocess.STDOUT)
    print(tag, "exit", r.returncode, "made", [k for k in keys if os.path.exists(f"{DATA}/ai/raw/{k}.png")], flush=True)


def video():
    """Same medium as the real frames: 1920x1080 H.264, ~5 Mbps (the real 1080p clips run 4.5-6 Mbps), frame back out."""
    for f in sorted(os.listdir(f"{DATA}/ai/raw")):
        if not f.endswith(".png"):
            continue
        k = f[:-4]
        tmp = f"{DATA}/ai/raw/{k}.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-i", f"{DATA}/ai/raw/{f}", "-t", "1", "-r", "30",
                        "-vf", "scale=1920:1080:flags=bicubic,format=yuv420p", "-c:v", "libx264", "-preset", "medium",
                        "-b:v", "5M", "-maxrate", "5M", "-bufsize", "10M", "-g", "30", tmp], check=True)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "0.5", "-i", tmp, "-frames:v", "1", f"{DATA}/ai/{k}.png"],
                       check=True)
        print(k, "-> ai/" + k + ".png")


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
            list(ex.map(lambda b: run("real-" + "+".join(b), b, sp), batches))
    elif cmd == "video":
        video()
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
