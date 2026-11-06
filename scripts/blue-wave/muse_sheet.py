#!/usr/bin/env python3
"""First frames + prompt sheet for the owner's Muse clips (蓝色浪潮), in film order, all in one folder (owner 11-05:
「你把最终参考图都放在一个目录吧」): muse-refs/NN-<id>.jpg + muse-refs/MUSE-PROMPTS.md with each first frame's path
(「提示词里包含reference图的路径」), where it sits in the music and the prompt.

A realistic painting goes to Muse as itself (owner 11-05: 「绘画如果本身已经比较realistic 就不需要codex 生成图了 直接用原画
muse」) and the clip is the painting coming alive; a stylised one (woodblock print, impasto, Degas's loose strokes) goes
as its Codex photo's 4K upscale (codex/real-<id>-4k.png, scripts/gymnopedies/upscale_stills.py). Liberty goes as the
painting too (owner 11-05: 「自由引导人民 用原画试试」) — then as the painting with Liberty taken out, to be laid back on the
clip (「你让codex做一个去掉中间女人的图 完了我们生成视频，再把女人加回去」, codex/liberty-plate.png), Whistler's Nocturne as well, without the Lady's boat the bridge photo
added (「就用原来的油画吧 不用改变了」), and the Wanderer as the painting widened to 16:9 (「旅人基于原画扩充为横屏」,
codex/extended-wanderer.png from extend_painting.py). Same rules as 听得见的舞: fixed camera, slow continuous motion, the last second close to the first frame, so the clip dissolves cleanly with its painting both ways (the vertical
shorts alternate painting ↔ clip). Clips come back as footage/muse/NN-<id>.mp4.

  .venv-reframe/bin/python scripts/blue-wave/muse_sheet.py
"""
import os
from PIL import Image

DATA = os.environ.get("BLUE_WAVE_DATA", "/Users/yqin/repo/playground/lucas-academy-video-data/blue-wave")
OUT = f"{DATA}/muse-refs"
KEEP_PAINTING = ("Keep the original oil painting's texture, brushstrokes and colours; do not turn it into a photograph. ")
# ^ follows "Static camera. " in every prompt whose first frame is the painting. Prompts are in English (owner 11-05: 「muse prompt 用英文」).

# film order (Lévy recording): id, first frame ("codex" photo, the "art" painting, the painting "extended" to 16:9, or its
# "plate" — the painting with its central figure taken out, liberty_plate.py),
# music slot, painting, prompt;
# None = a clip we already have
CLIPS = [
    ("great-wave", "codex", "0:00 A 主题 · 开场", "葛饰北斋《神奈川冲浪里》",
     "Static camera. The giant wave holds its tall curling shape while the white, claw-like spray at its crest keeps churning "
     "and breaking, foam and droplets flying slowly; the three boats rise and fall gently on the swell, the rowers pressed low "
     "in the hulls; Mount Fuji in the distance stays still, clouds drift slowly across the sky. Slow-motion feel, one continuous shot."),
    (None, None, "0:29 A′", "莫奈《印象·日出》", "已有：footage/existing/le-havre-dawn-muse-original.mp4（勒阿弗尔港的黎明），直接用。"),
    ("blue-dancers-orsay", "codex", "0:58 B（前半）", "德加《蓝色舞者》（奥赛版）",
     "Static camera. Backstage before the performance, four ballet dancers slowly adjust their costumes: the dancer on the left "
     "pins up her hair with both hands; the dancer in the middle, her back to us, pulls her shoulder straps into place and gives "
     "a small shrug; the two dancers on the right bow their heads and adjust the straps at their chests; the pale blue tutus sway "
     "softly as they move; the two dancers in orange-yellow behind them talk quietly. Slow, natural movement, unchanging light, "
     "one continuous shot."),
    (None, None, "0:58 B（后半）", "德加《蓝色舞者》（普希金版）", "已有：footage/muse/blue-dancers-vertical.mp4（你做的竖版），横屏里上下摇着用。"),
    ("rhone", "codex", "1:28 A″", "梵高《罗纳河上的星夜》",
     "Static camera. The Rhône at night: the water ripples gently, the long golden reflections of the gas lamps shimmer and "
     "stretch on its surface; the stars twinkle softly; the two small boats by the shore rock gently; in the lower right the "
     "couple walk arm in arm one or two steps towards us, the woman leaning towards the man and turning her head to speak to him. "
     "One continuous shot."),
    ("kramskoi-moonlit", "art", "1:57 B′", "克拉姆斯柯依《月夜》",
     "Static camera. A garden in moonlight: she leans back on the bench, slowly raises her head to gaze into the distance, then "
     "after a moment gently lowers it again; the lace fringe of her shawl stirs in the night breeze; the white flowers and leaves "
     "on the bushes sway slightly; small ripples cross the pond and the water lilies bob gently. The moonlight stays the same. "
     "Very quiet, one continuous shot."),
    ("shalott", "art", "2:25 A‴（前半）", "沃特豪斯《夏洛特夫人》",
     "Static camera. She sits in the boat; the iron chain in her hand slowly loosens and slips away, and the boat rocks gently on "
     "the water; she gazes ahead, her lips moving slightly as if she were softly singing; her long red hair lifts a little in the "
     "breeze; the flames of the three candles flicker; fallen leaves drift slowly across the water. The boat stays where it is "
     "and does not drift out of frame. One continuous shot."),
    ("whistler-chelsea", "art", "2:25 A‴（后半）", "惠斯勒《夜曲：蓝与银——切尔西》",
     "Static camera. Blue-silver dusk on the Thames at Chelsea: thin mist drifts slowly over the wide, still water; the few "
     "lights on the far bank tremble in their long thin reflections; the low barge on the left floats almost still, its small "
     "orange lamp glimmering; the figure standing in the shallows on the right slowly moves the long pole in his hands. "
     "Very quiet and calm, one continuous shot."),
    ("miranda", "art", "2:54 尾声", "沃特豪斯《米兰达——暴风雨》",
     "Static camera. In the storm, row after row of great waves roll in and crash against the rocks and cliffs, spray flying "
     "high; the sailing ship in the distance heels and pitches in the waves; Miranda stands by the rock, her long red hair and "
     "dark blue-green gown whipping in the strong wind, one hand pressed to her chest, watching the ship. She stays where she "
     "is. One continuous shot."),
    ("liberty", "plate", "3:25 高潮", "德拉克洛瓦《自由引导人民》（去掉中间的女人，之后再加回去）",
     "Static camera. On the barricade, white and grey gunsmoke rolls and drifts across the blue sky and through the middle of "
     "the picture; the boy on the right raises his pistol and shouts; the young man in the top hat grips his gun and leans "
     "forward; the worker on the left lifts his sabre; the crowd behind them surges forward with raised sabres and guns; the "
     "kneeling man in blue looks up. Keep the open space in the middle (smoke, sky and barricade) empty: no new person, figure "
     "or flag appears there. Forceful but not fast, everyone stays in place. One continuous shot."),
    ("wanderer", "extended", "3:48 华彩 → 结束（43 秒）", "弗里德里希《雾海上的旅人》（原画扩成横屏）",
     "Static camera. He stands with his back to us on the rocky summit, almost motionless, only his hair and the hem of his coat "
     "stirring in the wind; below him the sea of fog slowly rolls and flows, distant rocky peaks appearing and fading in the mist; "
     "clouds drift slowly across the sky. Very slow and quiet, one continuous shot."),
]

def main():
    os.makedirs(OUT, exist_ok=True)
    for f in os.listdir(OUT):                     # one folder, only the current references
        if f.endswith(".jpg"): os.remove(f"{OUT}/{f}")
    rows, n = [], 0
    for pid, src, slot, title, prompt in CLIPS:
        if pid is None:
            rows.append(f"| — | {slot} | {title} | {prompt} |"); continue
        n += 1
        im = Image.open({"codex": f"{DATA}/codex/real-{pid}-4k.png", "art": f"{DATA}/art/{pid}.jpg",
                         "extended": f"{DATA}/codex/extended-{pid}.png", "plate": f"{DATA}/codex/{pid}-plate.png"}[src]).convert("RGB")
        im.thumbnail((3840, 3840), Image.LANCZOS)
        dst = f"{OUT}/{n:02d}-{pid}.jpg"; im.save(dst, quality=92)
        kind = {"codex": "仿古照片", "art": "原画", "extended": "原画扩成横屏", "plate": "原画去掉中间的女人"}[src]
        if src != "codex": prompt = prompt.replace("Static camera. ", "Static camera. " + KEEP_PAINTING, 1)
        rows.append(f"| `{dst}`<br>{kind} {im.width}×{im.height} | {slot} | {title} | {prompt} |")
        print(f"{n:02d}-{pid}", kind, im.size, f"{os.path.getsize(dst) / 1e6:.1f} MB")
    md = f"""# 蓝色浪潮 · Muse 参考图和提示词（2026-11-05）

一共 {n} 段新的 Muse，参考图（首帧）都在这个文件夹里，按片子里的顺序编号，完整路径写在第一列。
- **原画**：画本身已经够写实，直接让画动起来，提示词开头要求保持油画质感（Keep the original oil painting's texture…）。惠斯勒《夜曲》用原画，不加东西。
- **原画扩成横屏**：《雾海上的旅人》，中间是原画扫描，左右两边是 Codex 照着原画的笔触补出来的。
- **原画去掉中间的女人**：《自由引导人民》，Codex 把她（连同旗子和步枪）去掉、补上硝烟和人群，其他地方都是原画扫描。视频做好后我把她从原画里抠出来叠回去。
- **仿古照片**：画太写意（木版画、梵高、德加），用 Codex 照片。

成片里每段都要和原画叠化，竖屏短视频还要原画和视频来回切，所以：**镜头固定不动，动作慢而连续，最后一秒回到接近首帧的样子**。
慢放和跟着音乐的节奏我在剪辑里做，Muse 只要正常速度，尽量长（10 秒）。蓝色滤镜也在剪辑里加，Muse 里不用调色。

| 参考图（首帧） | 音乐里的位置 | 画 | Muse 提示词（英文） |
| --- | --- | --- | --- |
{chr(10).join(rows)}

做好的视频放进 `{DATA}/footage/muse/`，文件名和参考图一样（例如 `01-great-wave.mp4`），我来接进片子。
"""
    open(f"{OUT}/MUSE-PROMPTS.md", "w").write(md)
    print("wrote", f"{OUT}/MUSE-PROMPTS.md")

if __name__ == "__main__":
    main()
