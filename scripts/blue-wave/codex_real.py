#!/usr/bin/env python3
"""Period reconstructions ("仿古图") of the 蓝色浪潮 paintings, made by the Codex CLI, for the owner to animate in Muse.

Same method as scripts/gymnopedies/codex_real.py (owner 11-03: 「codex 生成仿古图，muse 做，和油画切换」), but the paintings
come from many periods and places, so each note carries its own era instead of one 1870s-Paris preamble.

  codex_real.py TAG ID [ID ...]          one Codex run for these ids -> codex/real-<id>.png,
                                         registry codex/generated-assets.<TAG>.json (one per run, so parallel runs don't collide)
  codex_real.py --plan TAG ID [ID ...]   no run: write codex/runs/<TAG>.plan.md, the same request as one prompt the owner
                                         pastes into Codex (owner 11-05: 「给我让codex 执行的计划提示词吧」); references
                                         are named by absolute path instead of attached
Reference = art/<painting>.jpg (sent at <= 2048 px). Log, prompt and last message in codex/runs/.
Every new photo keeps the painting's own aspect: Muse gives ~0.8 MP whatever the input, so a wide canvas would leave a
portrait painting too few pixels for the vertical shorts, and the 16:9 film tilts through a same-aspect clip instead
(the 听得见的舞 method). An id in WIDE is the one exception, the Wanderer ending: the whole painting sits in the middle at
its own size and only the left and right are new, so the painting still dissolves into the photo without a jump.
No photo is tinted: the blue filter (tint.py) goes on afterwards, on the painting and the photo alike.
"""
import os, subprocess, sys
from PIL import Image

DATA = os.environ.get("BLUE_WAVE_DATA", "/Users/yqin/repo/playground/lucas-academy-video-data/blue-wave")

COMMON = ("照着参考画，生成一张「仿古」写实照片：像画里那个年代的真实场景被电影摄影机拍下来的一帧剧照——彩色、照片级写实、"
          "自然的光影和质感，不是黑白老照片，也没有任何油画笔触或插画感。"
          "构图、视角、每个人物和景物的位置、姿态、朝向、服装颜色和光线方向都和原画一一对应，好让照片和原画能叠化切换；"
          "原画边缘切掉的东西也照样切掉。画幅比例和原画一致，用最大的原生尺寸，不要软件放大。"
          "颜色照原画，不要加任何滤镜、调色或整体偏色（蓝色调之后会统一加）。"
          "人物的脸自然、完整、好看，手脚形状正确；服装、发型符合那个年代；画面里不要出现任何现代物品、文字或水印。"
          "要像一个正在进行的动作中的一瞬间（风、雾、水、头发、衣服都可以在动），方便之后把照片做成几秒的短视频。")

NOTES = {
    "wanderer": "卡斯帕·大卫·弗里德里希《雾海上的旅人》（约 1818，汉堡美术馆）。德国萨克森小瑞士的山顶，清晨。"
                "画面正中一个男人背对我们站在一块黑色的岩石尖顶上，深绿色的长大衣、左手拄一根手杖，右手垂在身侧，"
                "红棕色的头发被风吹乱，微微低头看着脚下；他的前方是翻滚的雾海，雾里露出一座座岩峰和远处的山，"
                "右边远处一座平顶的山，左后方是淡蓝灰的山脉；天空是淡蓝和白色的云。前景岩石是深色的，人物是画面最暗的剪影。",
    "great-wave": "葛饰北斋《神奈川冲浪里》（约 1830–32，木版画，大都会博物馆藏本）。江户时代，神奈川外海，阴天。"
                  "画面左边一道巨浪高高卷起，浪头碎成一根根像爪子一样的白色浪花，正要砸下来；浪的形状、高度和卷的方向照原画，"
                  "但要是真实的海水和浪沫。三条细长的木制押送船（运鲜鱼的快船），每条船上一排桨手蜷着身子紧抓船舷："
                  "一条在左边巨浪的下面，一条在中间偏右、富士山后面，一条在最下面的前景里；前景还有一道小一点的浪，像一座小山。"
                  "远处两道浪之间的低处，是戴着雪的富士山，小小的。海水是深蓝色，浪尖是白色；天空是真实的、淡暖灰色的阴天，"
                  "靠近海平线暗一些——不要纸张的颜色和纹理。原画左上角的题签和签名不要。",
    "blue-dancers-orsay": "埃德加·德加《蓝色舞者》（约 1893，奥赛博物馆，油画）。巴黎歌剧院后台，上场之前。"
                          "四个穿浅蓝色纱裙的芭蕾舞者挤在一起整理衣服：左边的舞者双手举到头上整理头发；中间的舞者背对我们，"
                          "两只手肘向外弯，在整理肩带；右边两个舞者侧身低着头，一个用手调整胸前的肩带；她们身后远处还有两个"
                          "穿橙黄色衣服的舞者。左边和上方是斑驳的绿、黄、粉色的风景布景画布，右边是一块深棕红色的侧幕立柱，"
                          "脚下是暗色的舞台木地板，舞者穿着粉色的足尖鞋。光是暖色的舞台煤气灯光，蓝纱裙带一点青绿。",
    "rhone": "文森特·梵高《罗纳河上的星夜》（1888 年 9 月，阿尔勒，奥赛博物馆）。夜晚的罗纳河岸。"
             "天空是深蓝色的夜（不是黑的），满天星星，北斗七星在中上方；对岸是阿尔勒的城区剪影，左边有一座教堂钟楼，"
             "一排煤气街灯是暖黄色的，在河面上拉出一条条长长的金色倒影；河中间靠近岸边停着两条小船，桅杆竖着；"
             "近岸是一片斜斜的沙滩；右下角一对恋人挽着手朝我们走来，男人穿蓝色的工装、戴帽子，女人穿深色的衣服。"
             "整体是深蓝、蓝绿和金黄的灯光。",
    "kramskoi-moonlit": "伊万·克拉姆斯柯依《月夜》（1880，特列季亚科夫画廊）。俄罗斯庄园的花园，夏夜，月光。"
                        "一个年轻女人穿一身白色长裙，头上披着白色的蕾丝头巾，坐在一张浅色的木长椅上，身体靠向椅背，"
                        "一只手臂顺着椅背伸向右边，另一只手放在膝上，低头想着心事；背后是高大的树，树干被月光照亮，"
                        "右边是开着白色小花的灌木；她脚下是一条被月光照亮的小路，前景是池塘的水边，有芦苇和草，"
                        "水面上有几朵白色的睡莲。整体是很暗的蓝绿色夜晚，只有她的白裙和树干最亮。"
                        "这是夜里的月光，不是白天的阳光、也不是树荫：天已经黑了，光是冷的、带一点蓝绿的银白色，从右上方照下来，阴影里几乎全黑，小路和她裙子上的亮处是月光（第一版看起来像白天，11-05 重做）。",
    "missolonghi": "欧仁·德拉克洛瓦《希腊在迈索隆吉翁的废墟上》（1826，波尔多美术馆）。1826 年希腊独立战争，"
                   "迈索隆吉翁城陷落之后的废墟。一个年轻的希腊女人跪在一块倒下的白色大石块上，双臂向两边张开、手掌向前，"
                   "像在诉说，两只手的五指要清楚完整；她的脸悲伤而坚定，看向左前方；头上包着金色花纹的头巾，深色长发披在肩后，"
                   "穿白色宽松的衬衣和白色的宽腿长裤，腰上系一条金黄色的宽腰带，外面是一件深蓝色天鹅绒的长外套，金色镶边，"
                   "红色的软鞋。照片里衬衣的领口是敞开的，但要遮住胸部，不要裸露。她脚下是碎石和废墟，"
                   "右下角倒下的石块下面露出一只阵亡战士的手和红色的衣袖；右后方远处站着一个包着橙红色头巾、穿红色衣服的士兵，"
                   "举着一根长旗杆；天空是暗的、灰黑色的硝烟。"
                   "如果这张参考图不能用作参考（画里人物的胸口是敞开的），就只按上面的文字描述生成，构图照这段描述。",
    "liberty": "欧仁·德拉克洛瓦《自由引导人民》（1830，卢浮宫，2024 年修复后的样子）。1830 年 7 月 28 日，巴黎七月革命的街垒。"
               "画面中央，象征自由的年轻女子赤脚踏上街垒，右手高举红白蓝三色旗，左手握着一支上了刺刀的步枪，头戴红色的弗里吉亚帽，"
               "侧脸回头望向身后的人群、招呼大家向前；她穿一件黄白色的长裙，腰间系着红色的布带。照片里她的长裙上身是完整的，"
               "遮住胸部，不要裸露。她左边（画面左）是一个戴黑色高礼帽、穿黑色外套的年轻人，双手握着一支长枪；最左边一个穿白衬衫、"
               "斜挎白带子的工人举着一把军刀，身后人群里举着刀枪；她右边（画面右）是一个戴黑色贝雷帽的少年，两只手各握一把手枪，"
               "斜挎一个大子弹袋，张嘴喊着向前冲；她脚下一个穿蓝色上衣、系红腰带、包着头巾的人跪在石块上，仰头望着她。"
               "前景是街垒的石块、木头和倒下的人：左下一个倒地的人（照片里他穿着长裤，不要裸露），右下躺着阵亡的士兵，"
               "一个穿浅色制服，一个戴黑色高筒军帽。右后方的硝烟里露出巴黎的房子和圣母院的两座钟楼。"
               "天空是蓝色的，白色的硝烟和云在翻滚，光从左上方照下来，照亮她和旗子。"
               "如果这张参考图不能用作参考（画里人物的胸口裸露），就只按上面的文字描述生成，构图照这段描述。",
    "shalott": "约翰·威廉·沃特豪斯《夏洛特夫人》（1888，泰特美术馆），取材于丁尼生的诗。英国的一条河，秋天的傍晚。"
               "夏洛特夫人坐在一条黑色的木船上，船头雕着金色的卷形装饰、挂着一盏灯笼，船头前面竖着三根白蜡烛；"
               "她穿一件白色的长袍，宽袖，红色的长发披下来，额上一条细细的发带，脖子上一串金项链，嘴唇微张、望向前方，"
               "像在唱歌；她的一只手握着系船的铁链，正要放开；船上铺着一块很大的挂毯（红、金、蓝的图案），一角垂到水里。"
               "左边近处是芦苇和枯草，有一只小鸟；背后是深色的秋天树林，左后方露出一点石头建筑，右上角远处露出一点天空和绿色的山坡；"
               "水面平静，漂着黄色的落叶。",
    "chelsea-shalott": "詹姆斯·惠斯勒《夜曲：蓝与银——切尔西》（1871，泰特美术馆）。伦敦泰晤士河，刚入夜的蓝色时刻，"
                       "从切尔西的河岸望向对岸的巴特西。整个画面是一片很淡、很静的蓝和银色，像起了薄雾：上面是淡蓝灰的天空，"
                       "中间一条低低的深蓝色对岸剪影（房子，右边一座方形的塔），对岸零星亮着几盏小灯，在水面上拉出细细的倒影；"
                       "宽阔平静的河面占了大半个画面；左下近处浮着一条又长又低的驳船，船头一点橙色的灯；"
                       "右下近处的浅水边站着一个人影，向左伸出一根竿子；最下面是近岸一条浅色的河滩。"
                       "这一张要比惠斯勒原画多一样东西：第二张参考图（夏洛特夫人）里她的那条黑色木船，小小的、在远处，"
                       "停在河面中央偏左，静静地漂，船头灯笼和蜡烛是几个暖色的小光点，船上隐约能看出白衣红发的她——"
                       "好像她顺着河一直漂到了这里。除了这条船，其他都和惠斯勒原画一一对应；"
                       "原画最下面正中的蝴蝶签名牌不要。颜色就是原画的蓝和银。",
    "miranda": "约翰·威廉·沃特豪斯《米兰达——暴风雨》（1916），取材于莎士比亚《暴风雨》。暴风雨中的海岛岸边。"
               "米兰达站在右边的一块礁石旁，侧身、几乎背对我们，望着海上；她穿一件深蓝绿色的长裙，裙摆和袖口里露出红色的衬里，"
               "腰间挂一个小皮包；红色的长发被风吹向左后方，一只手按在胸口，另一只手举到额前；"
               "左上方远处一条大帆船在巨浪里倾斜、快要沉没，后面还有一条船；海上一排排绿色的大浪翻卷着白沫，"
               "拍向右上方的黑色悬崖，溅起高高的浪花；左边近岸漂着一根断掉的木桨；前景是湿的鹅卵石和礁石。天空是暗灰色的暴风云。",
}
ART = {"wanderer-wide": "wanderer", "chelsea-shalott": "whistler-chelsea",   # main reference when it differs from the id;
       "wanderer-16x9": "codex/refs/wanderer-canvas.png",                    # a path = a file under DATA instead of art/
       "liberty-plate": "liberty"}
EXTRA = {"chelsea-shalott": ["shalott"], "wanderer-16x9": ["wanderer"]}      # further references
# ids whose note is the whole instruction — not a photo: the painting itself widened to 16:9 (owner 11-05: 「旅人基于原画扩充为横屏」),
# layout from extend_painting.py canvas, the real scan put back in the middle by extend_painting.py compose
OWN = {
    # owner 11-05: 「自由引导人民 你让codex做一个去掉中间女人的图 完了我们生成视频，再把女人加回去」 — the painting without
    # Liberty for Muse to animate; liberty_plate.py keeps the real scan outside her and cuts her out to lay back on the clip
    "liberty-plate": "欧仁·德拉克洛瓦的油画《自由引导人民》（1830，卢浮宫，2024 年修复后）。把画中央那个象征自由的女子整个去掉："
                     "她的身体、红色的帽子、黄白色的长裙和红腰带、她高举的三色旗和旗杆、她左手握的带刺刀的步枪，全部去掉。"
                     "去掉以后，那里补上原本在她身后的东西：上半部是同样的蓝天和翻滚的白色、灰色硝烟（旗子原来的地方也补成天空和硝烟）；"
                     "中间是她身后远处的人群、举着的刀枪和硝烟的自然延续；下半部是街垒的石块和木头。不要在那里画任何新的人物或旗子。"
                     "其他所有东西一点都不要改：左边戴高礼帽的青年、举军刀的工人和身后的人群，右边举手枪的少年，跪在地上仰头的人，"
                     "前景倒下的人和士兵，右后方的房子和圣母院钟楼——位置、大小、姿态、颜色、笔触都和原画完全一样。"
                     "风格必须是这幅原画本身：同一幅油画，同样的笔触、颜色、明暗和画布质感——这一张要的是油画，不是照片。"
                     "不要加文字或签名。画幅比例和原画一致，用最大的原生尺寸。",
    "wanderer-16x9": "把卡斯帕·大卫·弗里德里希的油画《雾海上的旅人》（约 1818）扩成一幅 16:9 的横幅油画，用 16:9 横版的最大原生尺寸。"
                     "第一张参考图是横幅的布局：中间是原画，整幅、上下撑满，大小和位置都不要动；左右两边的灰色是要你补画的部分。"
                     "第二张参考图是原画本身，看清楚它的笔触和颜色。在左右两边画出这幅画合理的延续：同样翻滚的雾海、雾里露出的岩峰"
                     "和远处淡蓝灰的山、同样的淡蓝天空和白云、同样从左上方来的柔和晨光；左下和右下可以让前景深色的岩石自然延伸一点，"
                     "但不要比原画里的岩石更高、更抢眼。风格必须和原画完全一样：同一位画家的油画，同样细腻平滑的笔触、颜色、"
                     "明暗和画布质感——这一张要的是油画，不是照片。不要加新的人物、动物、鸟、建筑、文字或签名。"
                     "中间原画的部分照原样画，和两边接起来的地方看不出接缝，雾和云的走向从原画里自然地延续出去。",
}
WIDE = {"wanderer-wide": "同样的雾海、岩峰和远山"}   # id -> what to add left and right
SAME_ASPECT = "画幅比例和原画一致，用最大的原生尺寸，不要软件放大。"
LANDSCAPE = ("这一张做成横幅：用横版的最大原生尺寸（1536×1024）。原画的整个画面放在横幅正中间，上下边缘就是原画的上下边缘，"
             "每个人物和景物的大小和位置都不变；只在原画的左边和右边补出合理的延续（{ext}），"
             "好让原画放在横屏中间时能和照片叠化对上。")

PRE = ("这是自动运行，没有人能回答问题：不要提问，直接把下面每一张都做完。用内置的图像生成工具生成，"
       "生成时把对应的画作为参考图（{refs}）。生成的图会先存在 ~/.codex/generated_images 里，"
       "每做完一张就马上复制到要求的输出路径（PNG），并在 {reg} 里登记它的输出路径、实际尺寸和你用的提示词——"
       "不要等全部做完再存，这样中途断了也不丢。做完自己检查一遍：构图和人物位置是不是和原画对得上、脸和手有没有变形、"
       "是不是照片而不是油画（写明要油画的那张除外）、有没有文字或偏色；不合格就重画。最后一条消息列出每张的输出路径和实际尺寸。\n\n")
ATTACHED = "已附在这条消息里，顺序和下面的编号一致"
BY_PATH = ("在下面写的绝对路径里：先用 view_image 工具逐张打开看清楚（或者我直接把图拖进来），"
           "生成时把它作为参考图。工作目录是 {data}，下面的相对路径都相对于它")

def main():
    plan = sys.argv[1] == "--plan"
    tag, ids = sys.argv[1 + plan], sys.argv[2 + plan:]
    os.makedirs(f"{DATA}/codex/runs", exist_ok=True); os.makedirs(f"{DATA}/codex/refs", exist_ok=True)
    imgs, lines = [], []
    for k, pid in enumerate(ids, 1):
        names = []
        for art in [ART.get(pid, pid)] + EXTRA.get(pid, []):
            src = f"{DATA}/{art}" if "/" in art else f"{DATA}/art/{art}.jpg"
            ref = f"{DATA}/codex/refs/{os.path.splitext(os.path.basename(art))[0]}.jpg"
            im = Image.open(src).convert("RGB"); im.thumbnail((2048, 2048), Image.LANCZOS); im.save(ref, quality=92)
            imgs.append(ref)
            names.append(f"参考图 {len(imgs)}（{ref if plan else os.path.basename(ref)}，{im.size[0]}×{im.size[1]}）")
        common = COMMON.replace(SAME_ASPECT, LANDSCAPE.format(ext=WIDE[pid])) if pid in WIDE else COMMON
        if pid in OWN: common = ""
        note = OWN.get(pid) or NOTES.get(pid) or NOTES[ART.get(pid, pid)]
        if plan:                                  # the pasted prompt says COMMON once, up front; only a wide id repeats it
            common = common if pid in WIDE else ""
        lines.append(f"{k}. {' + '.join(names)} → 输出 codex/real-{pid}.png\n   {note}" + (f"\n   {common}" if common else ""))
    refs = BY_PATH.format(data=DATA) if plan else ATTACHED
    prompt = PRE.format(refs=refs, reg=f"codex/generated-assets.{tag}.json")
    if plan: prompt += f"每一张都要做到：{COMMON}\n\n"
    prompt += "\n\n".join(lines)
    if plan:
        open(f"{DATA}/codex/runs/{tag}.plan.md", "w").write(prompt + "\n")
        print(f"{DATA}/codex/runs/{tag}.plan.md"); return
    open(f"{DATA}/codex/runs/{tag}.prompt.md", "w").write(prompt)
    cmd = ["codex", "exec", "--skip-git-repo-check", "-s", "workspace-write", "-C", DATA, "--enable", "image_generation",
           "-c", 'model_reasoning_effort="medium"', "-o", f"{DATA}/codex/runs/{tag}.last.md"]
    for im in imgs: cmd += ["-i", im]
    cmd += ["-"]
    with open(f"{DATA}/codex/runs/{tag}.log", "w") as log:
        r = subprocess.run(cmd, input=prompt, text=True, stdout=log, stderr=subprocess.STDOUT)
    print(tag, "exit", r.returncode)
    sys.exit(r.returncode)

if __name__ == "__main__":
    main()
