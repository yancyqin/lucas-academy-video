#!/usr/bin/env python3
"""Period reconstructions ("仿古图") of the dance paintings, made by the Codex CLI, for Muse to animate.

Owner 2026-11-02: MiniMax does oil paintings badly — 「还是 codex 生成仿古图，muse 做，和油画切换吧」; and add
Degas's The Dance Class (Met 1874), which he liked in 你知道印象派的秘密吗？. Same look as that film's
real-opera-pit-1870 / real-moulin-galette-1876: a colour film still of the real scene, same composition as the painting.

  codex_real.py TAG ID [ID ...]   one Codex run for these paintings -> codex/real-<id>.png,
                                  registry codex/generated-assets.<TAG>.json (one per run, so parallel runs don't collide)
Reference = art/<id>.jpg (sent at <= 2048 px). Log, prompt and last message in codex/runs/.
An id in VERTICAL is a portrait version for a vertical short (owner 11-03 on Blue Dancers: 「这幅画我挺喜欢的，生成一个 codex
竖屏图，做一个 muse，单独出一个短视频」): the whole painting sits in the middle at its own size, only the top and bottom are
new, so the painting still dissolves into the photo without a jump.
"""
import os, subprocess, sys
from PIL import Image

DATA = "/Users/yqin/repo/playground/lucas-academy-video-data/satie-gymnopedies"

COMMON = ("照着参考油画，生成一张「仿古」写实照片：像 1870–1880 年代巴黎的真实场景被电影摄影机拍下来的一帧剧照——彩色、照片级写实、"
          "自然的光影和皮肤质感，不是黑白老照片，也没有任何油画笔触或插画感。"
          "构图、视角、每个人物的位置、姿态、朝向、服装颜色和光线方向都和原画一一对应，好让照片和原画能叠化切换；"
          "原画边缘切掉的人物也照样切掉。画幅比例和原画一致，用最大的原生尺寸，不要软件放大。"
          "人物的脸自然、完整、好看，手脚形状正确；服装、发型、芭蕾舞鞋和纱裙符合那个年代；画面里不要出现任何现代物品、文字或水印。"
          "姿态要像一个正在进行的动作中的一瞬间，方便之后把照片做成几秒的短视频。")

NOTES = {
    "dance-class": "德加《舞蹈课》（1874，大都会博物馆）。巴黎歌剧院的排练厅：浅绿色墙、木地板、墙上的大镜子映出窗外。"
                   "右边是白发的老芭蕾教师 Jules Perrot，穿宽松的西装，双手拄着一根高手杖；左边一个舞者坐在钢琴上挠背；"
                   "前景中央的舞者正面站着，头上戴红花、腰后系缎带；谱架、地上的喷壶都在原位；后面一排排白纱裙的舞者在练习或休息，"
                   "最里面靠墙坐着陪孩子来的母亲们。",
    "waiting": "德加《等待》（约 1882，粉彩）。俯视角度，土黄色的墙、木地板、后面一张木长凳。左边的芭蕾舞者穿白纱裙、"
               "腰后系一条大的蓝绿色缎带，弯下腰揉自己的脚踝；右边坐着一位穿黑衣、戴黑帽的年长女人，身体前倾，"
               "双手扶着一把收起的黑伞，伞尖抵着地板。",
    "barre": "德加《把杆前练习的舞者》（1877，大都会博物馆）。俯视角度，黄色的墙、一根长木把杆、木地板。两个舞者穿白纱裙、"
             "腰系黄缎带，背对我们，各把一条腿高高搭在把杆上压腿；左下角地上放着一个喷壶。",
    "bougival": "雷诺阿《布吉瓦尔之舞》（1883）。塞纳河边露天舞会，夏天。一对男女在跳舞：女人是 Suzanne Valadon，"
                "穿白色带粉色调的长裙，戴红色的软帽，低头微笑，脸转向一边；男人穿深蓝色西装、戴草帽，脸贴近她。"
                "背景里有人坐在桌边喝酒聊天，树荫和斑驳的阳光，地上有落下的花和火柴。",
    "dance-city": "雷诺阿《城市之舞》（1883）。室内的夜间舞会，背景有棕榈盆栽。女人穿白色缎面长礼服、戴长手套，"
                  "头发盘起，侧脸，后背和肩膀露出（礼服样式），男人穿黑色燕尾服，搂着她跳华尔兹，他的脸几乎被她挡住。",
    "rehearsal-stage": "德加《舞台上的排练》（约 1874，奥赛）。从侧上方看歌剧院舞台，地板一直延伸，脚灯一排；"
                       "舞者们分成几组在排练，有的在伸展、有的在挠背或打哈欠；右边坐着两个戴高帽的男人（剧院的常客）；"
                       "芭蕾教师站在舞者中间；前景左下角露出一把低音提琴的琴头。颜色用真实的舞台：暖色的煤气灯光、白纱裙、深色布景。",
    "blue-dancers-vertical": "德加《蓝色舞者》（1898，普希金造型艺术博物馆，粉彩）。后台，上场之前，几个穿蓝色纱裙的芭蕾舞者挤在一起"
                             "整理肩带和头发：左边的舞者低着头，右臂高高举起扶着上方的布景，左手按在胸前的肩带上；中间的舞者背对我们，"
                             "红棕色的发髻，两只手在肩上拉肩带；右边的舞者侧身低头，一只手举到脑后，另一只手拉着肩带；最下面露出第四个舞者"
                             "低着的头顶。身后是橙黄、草绿色的风景布景，右上角露出一点蓝色。光是暖色的舞台煤气灯。上面补出的是布景的延续"
                             "（树和天空的画布），下面补出的是蓝色纱裙的下半部分、第四个舞者的肩背和舞台的木地板。",
    "etoile": "德加《舞台上的舞者（明星）》（约 1878，奥赛）。从高处包厢俯视舞台，一位首席舞者在舞台前方做阿拉贝斯克，"
              "穿白纱裙、胸前和裙上点缀着花，头上戴花，双臂展开，仰头；后面左边的侧幕后面站着一个穿黑色燕尾服的男人，"
              "旁边的布景里露出其他舞者的裙子和腿；舞台地板是浅灰色，侧幕是暖色的树林布景。",
}
NAMES = {"barre": "barre-met", "blue-dancers-vertical": "blue-dancers"}   # art file when it differs from the id
VERTICAL = {"blue-dancers-vertical"}
SAME_ASPECT = "画幅比例和原画一致，用最大的原生尺寸，不要软件放大。"
PORTRAIT = ("这一张做成竖幅：用竖版的最大原生尺寸（1024×1536）。原画的整个画面放在竖幅正中间，左右边缘就是原画的左右边缘，"
            "每个人物的大小和位置都不变；只在原画的上面和下面补出合理的延续，好让原画放在竖屏中间时能和照片叠化对上。")

PRE = ("这是自动运行，没有人能回答问题：不要提问，直接把下面每一张都做完。用内置的图像生成工具生成，"
       "生成时把对应的油画作为参考图（已附在这条消息里，顺序和下面的列表一致）。生成的图会先存在 ~/.codex/generated_images 里，"
       "请把每张复制到要求的输出路径（PNG）。做完自己检查一遍：构图和人物位置是不是和原画对得上、脸和手有没有变形、"
       "是不是照片而不是油画；不合格就重画。最后在 {reg} 里登记每张的输出路径、实际尺寸和你用的提示词，"
       "最后一条消息列出每张的输出路径和实际尺寸。\n\n")

def main():
    tag, ids = sys.argv[1], sys.argv[2:]
    os.makedirs(f"{DATA}/codex/runs", exist_ok=True); os.makedirs(f"{DATA}/codex/refs", exist_ok=True)
    imgs, lines = [], []
    for k, pid in enumerate(ids, 1):
        src = f"{DATA}/art/{NAMES.get(pid, pid)}.jpg"
        ref = f"{DATA}/codex/refs/{pid}.jpg"
        im = Image.open(src).convert("RGB"); im.thumbnail((2048, 2048), Image.LANCZOS); im.save(ref, quality=92)
        imgs.append(ref)
        common = COMMON.replace(SAME_ASPECT, PORTRAIT) if pid in VERTICAL else COMMON
        lines.append(f"{k}. 参考图 {k}（{os.path.basename(ref)}，{im.size[0]}×{im.size[1]}）→ 输出 codex/real-{pid}.png\n   {NOTES[pid]}\n   {common}")
    prompt = PRE.format(reg=f"codex/generated-assets.{tag}.json") + "\n\n".join(lines)
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
