#!/usr/bin/env python3
"""Muse first frames + prompts for 一片落叶 (G1–G8).

  muse_refs.py run TAG ID [ID ...]   Codex draws these first frames -> out/leaf-truck/muse-refs/<ID>.png
  muse_refs.py desktop               phone folder on the Desktop: "<ID> <name>.jpg" + "<ID> <name>.txt" (English prompt) + 说明

Every truck matches the white box van of the side clip (v6/truck.mp4): input/truck.jpg is the look reference,
input/side-shot.jpg the composition reference for G7 (the ending mirrors the opening brake shot).
"""
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
REFS = REPO / "out/leaf-truck/muse-refs"
DESK = Path.home() / "Desktop/一片落叶-Muse参考图和提示词"

TRUCK = ("卡车照参考图 truck.jpg 那一辆：白色厢式货车（厢式面包车的驾驶室 + 后面一个方方正正的白色货箱），"
         "**去掉所有车标、品牌、文字**（车头中间不要三叉星或任何标志），车牌空白或看不清；驾驶室里没有人（这是无人驾驶卡车）。")
PLACE = "奥地利小镇的工业区道路，秋天，橙黄色的树，阴天上午，路面是湿的。"

# id, name (zh), where it goes in the film, priority, Codex first-frame description, Muse prompt (English)
SHOTS = [
    ("G1", "小镇公路远景", "开场第 1–2 句（讲一辆卡车 / 小镇、无人、送货）", "重要",
     f"远景。{PLACE}两边是两栋低矮的厂房，路边一排秋天的树。卡车在远处正对镜头开过来，只占画面宽度的八分之一左右，在车道正中。"
     "画面里没有别的车、没有人；路牌、厂房上不要有能读出来的字。",
     "Use this image as the first frame. Photoreal, 16:9, 24 fps, one continuous 10-second shot. A quiet small-town industrial road "
     "in Austria in autumn, overcast morning, wet asphalt. The unbranded white box truck drives slowly toward the camera along the "
     "middle of its lane, growing larger; nobody is in the cab (it is a driverless truck). Slow, steady push-in of the camera. A light "
     "breeze moves the orange trees and a few leaves drift down. The truck is still in the middle distance when the clip ends. "
     "No people, no other vehicles, no logos, no legible text, no subtitles, no music."),
    ("G2", "保险杠前的落叶特写", "开场第 5 句（是几片落叶）", "重要",
     "贴着路面的低机位微距特写：前景是湿的深色沥青路上四五片湿的橙色落叶，清晰锐利。"
     "背景虚焦：约两米外，那辆白色卡车的车头停在那里——白色保险杠、车灯、进气格栅，糊成柔和的形状，看得出是卡车车头。阴天的柔光，浅景深。",
     "Use this image as the first frame. Photoreal macro shot at road level, 16:9, 24 fps, one continuous 10-second shot, fixed camera. "
     "The wet orange leaves on the dark asphalt tremble and shift slightly in a light breeze; one leaf slowly flips over. In the soft-focus "
     "background the white truck has stopped and stays completely still. Soft overcast light, shallow depth of field stays the same, "
     "no camera movement. No people, no text, no logos, no music."),
    ("G3", "货箱里的货往前一冲", "第二段（每一次急刹车，车上的货都往前一冲）", "最重要",
     "卡车白色货箱的里面，相机固定在侧壁上，横着看过去：货箱前壁（靠驾驶室那一面）在画面右边。"
     "地板中间一个木托盘，上面整齐码着三四层素色牛皮纸箱（箱子上没有印字、没有标签），没有绑带。"
     "车顶一块灯板，光线偏暗，铝合金的厢壁和地板。没有人。",
     "Use this image as the first frame. Photoreal, 16:9, 24 fps, one continuous 10-second shot. A fixed camera mounted on the side wall "
     "inside the cargo box of a moving delivery truck; the front wall of the box is on the right of the frame. For the first 4 seconds "
     "the truck drives steadily: a slight vibration, the stacked cardboard boxes stay in place. At about 4 seconds the truck brakes hard: "
     "the camera jolts, and the boxes lurch and slide forward toward the front wall on the right, about half a metre; the top box tips "
     "over onto its side. Nothing breaks. Then everything settles and stays still. Steady light from the roof panel. No people, no text, "
     "no logos, no music."),
    ("G4", "车道上的低矮木托盘", "第二段（它看不出路上一块只有十四厘米高的木托盘）", "最重要",
     f"贴地的低机位，{PLACE}前景：一块普通的木托盘（欧标托盘的样子，但木块上没有任何印字和标记）平躺在车道上，横着挡住车道，只有一掌高。"
     "远处背景里，那辆白色卡车在同一条车道上正对镜头开过来，还很远、很小。没有别的车、没有人、没有字。",
     "Use this image as the first frame. Photoreal, 16:9, 24 fps, one continuous 10-second shot, fixed camera at ground level. The plain "
     "wooden pallet lies flat and completely still across the lane in the foreground. Far in the background the unbranded white box "
     "truck drives slowly toward the camera along the same lane, growing only a little larger; it is still far away when the clip ends "
     "and never reaches the pallet. A few fallen leaves drift across the wet road. Overcast light. No people, no other vehicles, no text, "
     "no logos, no music."),
    ("G5", "车顶的激光雷达（可选）", "第三段（传感器坏了，换一个）——不做就用动画", "可选",
     "特写：那辆白色卡车驾驶室车顶前沿，挡风玻璃上方，装着一个小小的黑色圆柱形激光雷达（短支架固定）。"
     "细雨，传感器外壳上有水珠，空中飘着一两片秋天的落叶。背景是虚焦的秋天树木。没有字、没有标志。",
     "Use this image as the first frame. Photoreal close-up, 16:9, 24 fps, one continuous 10-second shot. The camera slowly orbits about "
     "20 degrees around the small black cylindrical lidar sensor on the front edge of the white truck's cab roof. Light drizzle, raindrops "
     "bead and run on the sensor housing, and a few autumn leaves drift past it in the air. The truck stands still. Keep the sensor in "
     "focus. No people, no text, no logos, no music."),
    ("G6", "后车急刹（不相撞）", "第五段（一脚急刹，受影响的不只是它自己）", "重要",
     f"略高的固定机位，在后方偏一侧，顺着一条安静的双车道公路往前看。{PLACE}"
     "前面是那辆白色卡车（看到它的后部和一侧），后面约两个车身的距离跟着一辆灰色的小两厢车——**两辆车在同一条车道里，一前一后排成一条直线**，小车正对着卡车的车尾，车道中线（虚线）在它们左边，不在两车之间。两辆车都在行驶，刹车灯没亮。"
     "车牌空白或看不清，没有人、没有字。",
     "Use this image as the first frame. Photoreal, 16:9, 24 fps, one continuous 10-second shot, fixed elevated camera behind and to the "
     "side. The white box truck and the small grey hatchback behind it drive slowly forward in the same lane. At about 4 seconds the "
     "truck's brake lights come on and it stops suddenly; the hatchback brakes hard, its nose dips, and it stops close behind the truck "
     "with a clear gap of about one metre. No collision, no contact, no damage. Both stay stopped until the end. No people visible, "
     "no text, no logos, no music."),
    ("G7", "修好之后，平稳开过落叶", "结尾（最后一句破题问题和片尾）", "最重要",
     "构图照参考图 side-shot.jpg（开场急刹那个镜头）：同一个角度、同样的路口和树，卡车侧面朝右，在画面左半边往右开。"
     "但换成**傍晚**：低低的暖色斜阳从右后方照过来，树叶和路面被染成金色，影子拉长。右边前方的路边堆着一小堆干的橙色落叶，还没被风吹起来。"
     "路牌、厂房上不要有能读出来的字，没有人、没有别的车在动。",
     "Use this image as the first frame. Photoreal, 16:9, 24 fps, one continuous 10-second shot, fixed wide camera, warm late-afternoon "
     "sun. The unbranded white box truck drives slowly from left to right. At about 2 seconds a gust lifts a handful of dry orange leaves "
     "from the pile at the curb on the right and blows them across the lane ahead of the truck. The truck keeps driving smoothly at the same steady speed straight "
     "through the swirling leaves, without slowing or braking, and is leaving the frame on the right at the end. No people, no other "
     "moving vehicles, no text, no logos, no music."),
    ("G8", "正面：停在落叶前（可选）", "开场第 4 句（前面没人、没车）——换掉现在那辆美式卡车", "可选",
     f"正面低机位，相机贴近路面，放在**右侧那条车道的正中**，正对着前方。{PLACE}"
     "车道中线（白色虚线）在画面左边，**卡车在它自己的车道里，不压线**。画面下方中间的前景里，这条车道正中的路面上有一小撮干落叶（五六片），是被风吹到一起的样子，散乱、自然，不要摆成整齐的圆圈。远处，那辆白色卡车正对镜头开过来，车头朝我们，还比较远。"
     "两边是厂房和秋天的树。没有人、没有别的车、没有字。",
     "Use this image as the first frame. Photoreal, 16:9, 24 fps, one continuous 10-second shot, fixed camera low in the middle of the "
     "lane, looking straight at the front of the approaching truck. The small cluster of dry leaves stays on the asphalt in the "
     "lower-middle foreground, fluttering slightly in place. The unbranded white box truck approaches slowly and grows larger, then brakes "
     "and stops while the leaves are still several metres in front of its bumper, with a clear stretch of road between them. The truck "
     "stays stopped until the end, nobody in the cab. Soft overcast light. No people, no other vehicles, no text, no logos, no music."),
]
BY_ID = {s[0]: s for s in SHOTS}

PRE = ("这是自动运行，没有人能回答问题：不要提问，直接把下面每一张都做完。\n"
       "这些图是图生视频（Muse）的**首帧**：画面是动作开始之前的那一刻，之后会让它动起来。"
       "用内置的图像生成工具生成，附在消息里的图是参考图（truck.jpg = 卡车长什么样；side-shot.jpg = 开场镜头的构图）。"
       "生成的图会先存在 ~/.codex/generated_images 里，请复制到要求的输出路径，再登记。最后一条消息列出每张的输出路径和实际尺寸。\n\n")

COMMON = [
    "**统一要求**",
    "- **照片级真实**：像电影摄影机拍下的一帧，自然的光和颜色；不要 HDR、不要过度锐化、不要 AI 光滑感、不要插画感。",
    f"- **卡车**：{TRUCK}",
    "- **不能有文字**：没有字母、数字、招牌字、水印；路牌可以有，但上面的字看不清。",
    "- **没有人**，也不要出现手。",
    "- **尺寸**：16:9，用图像工具能给的最大 16:9 尺寸，不要再用软件放大。",
    "- **自查**：每张画完对照上面的要求和参考图检查一遍（卡车样子对不对、有没有标志和字、构图是不是写的那样），不对就重画这一张。",
]


def run(tag, ids):
    (REFS / "runs").mkdir(parents=True, exist_ok=True)
    lines = COMMON + [f"- **登记**：每张在 `{REFS}/generated-assets.{tag}.json` 里追加一条：`path`、`tool`、`created`、"
                      "`intent`（一句话写画面）、`reference`（参考图文件）、`dimensions`、`sha256`、`bytes`，`label` 写 `\"AI 生成 · Muse 首帧\"`。",
                      "", "**要画的图**", ""]
    for i in ids:
        _, name, _, _, desc, _ = BY_ID[i]
        lines.append(f"- `{REFS}/{i}.png` — {name}：{desc}")
    prompt = PRE + "\n".join(lines) + "\n"
    (REFS / f"runs/{tag}.prompt.md").write_text(prompt)
    cmd = ["codex", "exec", "--skip-git-repo-check", "-s", "workspace-write", "-C", str(REFS),
           "--enable", "image_generation", "-c", 'model_reasoning_effort="medium"',
           "-o", str(REFS / f"runs/{tag}.last.md"),
           "-i", str(REFS / "input/truck.jpg"), "-i", str(REFS / "input/side-shot.jpg"), "-"]
    with open(REFS / f"runs/{tag}.log", "w") as log:
        r = subprocess.run(cmd, input=prompt, text=True, stdout=log, stderr=subprocess.STDOUT)
    print(tag, "exit", r.returncode, flush=True)
    return r.returncode


def desktop():
    DESK.mkdir(parents=True, exist_ok=True)
    for old in DESK.glob("G*"):
        old.unlink()
    rows = []
    for i, name, use, prio, _, muse in SHOTS:
        src = REFS / f"{i}.png"
        if not src.exists():
            print("missing", src)
            continue
        stem = f"{i} {name}"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-q:v", "2", str(DESK / f"{stem}.jpg")], check=True)
        (DESK / f"{stem}.txt").write_text(muse + "\n")
        rows.append(f"{i}　{name}\n　　用在：{use}\n　　{prio}")
    note = ["一片落叶 · Muse 参考图和提示词", "",
            "每个镜头两份文件，名字一样：",
            "　.jpg 是首帧参考图（上传到 Muse 当第一帧）",
            "　.txt 是英文提示词（打开 → 全选 → 拷贝 → 粘到 Muse）", "",
            "卡车都照开场侧面急刹那个镜头里的白色厢式货车画的，没有车标、没有字，驾驶室没人。",
            "每段 10 秒、16:9、24 fps。慢放、调色、标签我在剪辑里做，Muse 只要正常速度。", "",
            "镜头：", ""] + rows + ["",
            "最影响观感的是 G3、G4、G7，先做这三个。G5、G8 可选：",
            "　G5 不做，第三段就用动画；",
            "　G8 做了，就换掉开场那段美式卡车（它和侧面那辆对不上）。", "",
            "做好的视频按编号命名（G1.mp4、G2.mp4……），AirDrop 回电脑放进这个文件夹就行，我来接进片子。",
            "「01 全部提示词.txt」是八段提示词合在一起的版本，方便一次存进备忘录。", ""]
    (DESK / "00 说明.txt").write_text("\n".join(note))
    allp = []
    for i, name, _, prio, _, muse in SHOTS:
        allp += [f"{i} {name}（{prio}）", muse, ""]
    (DESK / "01 全部提示词.txt").write_text("\n".join(allp))
    ins = [a for i, *_ in SHOTS for a in ("-i", str(REFS / f"{i}.png"))]
    pads = "".join(f"[{k}]scale=640:360,pad=648:368:4:4:white[v{k}];" for k in range(8))
    layout = "0_0|w0_0|w0+w1_0|w0+w1+w2_0|0_h0|w0_h0|w0+w1_h0|w0+w1+w2_h0"
    subprocess.run(["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex",
                    pads + "".join(f"[v{k}]" for k in range(8)) + f"xstack=inputs=8:layout={layout}",
                    "-q:v", "3", str(DESK / "02 八张总览（G1-G4 上排，G5-G8 下排）.jpg")], check=True)
    print("wrote", DESK)


if __name__ == "__main__":
    if sys.argv[1] == "run":
        sys.exit(run(sys.argv[2], sys.argv[3:]))
    if sys.argv[1] == "desktop":
        desktop()
