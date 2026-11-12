# 动物想什么？AI 知道吗？· Muse 提示词（2026-11-10）

首帧图都在一个文件夹里，按片中顺序编号：
`/Users/yqin/repo/playground/lucas-academy-video-data/ai-animal-mind/references/`

做好的视频请放进 `/Users/yqin/repo/playground/lucas-academy-video-data/ai-animal-mind/muse/`，文件名用 G 编号开头就行（比如 `G01.mp4`、`G01-2.mp4`）。还没到的，片子先用首帧图慢推代替，到了再换。

首帧都是 Codex 生成的（已用 Real-ESRGAN 放大到 3840 宽的高清版在 `hd/` 里，Muse 用哪个都行）。画面里都没有字。

11-11：你的照片不用了，G03（海边的猴子）和 G04（海浪）两个镜头换成了 Pexels 实拍，不用做。

| 编号 | 用在哪 | 首帧 |
| --- | --- | --- |
| G01 | am00-04..07 一个人，两只猴子，一起看夕阳；结尾 am13-01 | G01-sunset-hill.png |
| G02 | am00-06 它们先握了握手 | G02-handshake.png |
| G05 | am06-01..02 汉斯 | G05-hans.png |
| G05b | am06-02 用蹄子一下一下敲出答案 | G05b-hoof.png |
| G06 | am11-02 鸽子看画 | G06-pigeon-paintings.png |
| G07 | am11-06 小猴子选了没有声音的那边 | G07-tamarin-quiet.png |
| G08 | am11-04 老鼠跟着拍子点头（画面用龙猫） | G08-chinchilla-music.png |
| G09 | am03-03..04 把录音放给大象听 | G09-elephant-speaker.png |
| G10 | am05-01..02 和海豚一起造几个新词 | G10-dolphin-scarf.png |

优先做 G01、G02（开场和结尾都用），然后 G05、G08、G06、G07，G09、G10 最后。

---

**G01** · `/Users/yqin/repo/playground/lucas-academy-video-data/ai-animal-mind/references/G01-sunset-hill.png`

Static camera with a very slow push-in. A man and two small monkeys sit side by side on a grassy hilltop, watching the sun set over a wide lake. The monkeys turn their heads a little, one scratches its arm, then both settle and keep watching the sun. The man stays still. The grass sways softly in a light breeze, the sun sinks slowly, and golden light shimmers on the water. Calm, natural, realistic.

**G02** · `/Users/yqin/repo/playground/lucas-academy-video-data/ai-animal-mind/references/G02-handshake.png`

Close-up, static camera. Two vervet monkeys on a grassy hillside at golden hour reach out and gently clasp hands, hold for a moment, then let go and sit down side by side, facing the sunset. Natural monkey movements, soft backlight, grass moving in the breeze. Realistic wildlife footage.

**G05** · `/Users/yqin/repo/playground/lucas-academy-video-data/ai-animal-mind/references/G05-hans.png`

Static camera. In a 1904 courtyard, the horse lifts its right front hoof and taps the cobblestones several times, slowly and clearly, then stops. The white-bearded man watches the horse; the crowd leans in, some people look surprised and whisper to each other. Natural early-1900s feel, realistic.

**G05b** · `/Users/yqin/repo/playground/lucas-academy-video-data/ai-animal-mind/references/G05b-hoof.png`

Low close-up, static camera. The horse's front hoof taps the cobblestones one, two, three, four times in a steady rhythm, then rests on the ground. The onlookers' coats stay softly out of focus in the background. Realistic.

**G06** · `/Users/yqin/repo/playground/lucas-academy-video-data/ai-animal-mind/references/G06-pigeon-paintings.png`

Static camera. The pigeon turns its head from the left painting to the right painting, bobs its head, takes two small steps toward the left painting and pecks the table in front of it. Soft window light. The paintings stay completely still and unchanged. Realistic, natural pigeon movement.

**G07** · `/Users/yqin/repo/playground/lucas-academy-video-data/ai-animal-mind/references/G07-tamarin-quiet.png`

Static camera. The little cotton-top tamarin looks toward the speaker on the left, then turns away, hops along the branch to the quiet right side and settles calmly on the soft blanket. Gentle, natural movement, warm light, realistic.

**G08** · `/Users/yqin/repo/playground/lucas-academy-video-data/ai-animal-mind/references/G08-chinchilla-music.png`

Static camera with a slight push-in. The chinchilla sits beside the vintage radio and gently bobs its head up and down in a steady rhythm, as if keeping time to music, its big ears twitching. Cosy warm light. Realistic, natural chinchilla movement, playful.

**G09** · `/Users/yqin/repo/playground/lucas-academy-video-data/ai-animal-mind/references/G09-elephant-speaker.png`

Static camera. The elephant, ears spread, walks slowly toward the small loudspeaker in the foreground, raising its trunk and swaying its head. Dust drifts in the golden light and the grass moves in the breeze. Realistic wildlife footage.

**G10** · `/Users/yqin/repo/playground/lucas-academy-video-data/ai-animal-mind/references/G10-dolphin-scarf.png`

Underwater, gently drifting camera. The spotted dolphin tugs gently at the red scarf with its beak, lets go, swims a slow circle around the woman and comes back to nudge the scarf again; she smiles and lets the scarf float toward it, her hair drifting in the water; sunbeams flicker on the sand below. Realistic, smooth, playful.

（11-11 重新生成：穿比基尼、不戴面镜和呼吸管的人，等你确认首帧后重做视频。旧视频在数据目录 `_retired/G10-muse-v1-snorkeler.mp4`。）

## 每段需要多长（2026-11-11 的时间线，加了真实动物声音之后）

镜头长度含 0.6 秒叠化。Muse 视频短一点没关系：最慢放到 0.55 倍；再短就先用首帧图代替，告诉我再拆镜头。

| 编号 | 镜头需要（秒） | 视频至少 |
| --- | --- | --- |
| G01 | 8.5 / 9.0 | 5.0 秒 |
| G02 | 8.3 | 4.6 秒 |
| G05 | 6.5 / 3.2 | 3.6 秒 |
| G05b | 4.5 | 2.5 秒 |
| G06 | 6.8 | 3.7 秒 |
| G07 | 6.7 | 3.7 秒 |
| G08 | 11.3 | 6.2 秒 |
| G09 | 5.6 | 3.1 秒 |
| G10 | 5.9 | 3.2 秒 |
