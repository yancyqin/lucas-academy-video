# 一片落叶 · 镜头表与 Muse 提示词（v0.1）

画面规格：16:9，1920×1080，24 fps（和已有的 Muse 片段一致）。英文默认音轨，另带中文音轨。

画面标签只在出现那一刻亮出，旁白里不念：
- 思维方式标签：发散、批判、系统、逆向、综合。
- 情景重现、AI 生成、设想这几类说明标签。

## 镜头表

「已有」表示素材在 `out/autonomous-driving-seven-ways/source/`。「新」是要用 Muse 新生成的镜头（G 编号），提示词见下文。「动画」用 Remotion 做。

| 段 | 句 | 画面 | 来源 |
|---|---|---|---|
| LF01 | lf01-01 讲一辆卡车 | 秋天的奥地利小镇，工厂间的公路，远处一辆白色厢式卡车 | 新 G1 |
| | lf01-02 小镇、无人、送货 | G1 接上，卡车慢慢开近 | 新 G1 |
| | lf01-03 突然急刹 | 侧面：一阵落叶吹进车道，卡车急停；配刹车声 | 已有 `v6/truck.mp4` |
| | lf01-04 前面没人没车 | 正面：路上只有几片落叶，卡车停在它们前面 | 已有 `v6/truck-headon.mp4` |
| | lf01-05 是几片落叶 | 特写：保险杠前，湿路面上的几片落叶在颤 | 新 G2 |
| 片名 | （无旁白） | 「一片落叶，为什么让卡车急刹车？」 | 动画 |
| LF02 | lf02-01 十一倍 | 同一条路：人类司机和无人卡车的急刹次数并排累加到 11 倍 | 动画 |
| | lf02-02 货往前一冲 | 货箱里，托盘上的纸箱随急刹往前滑 | 新 G3 |
| | lf02-03 十四厘米的托盘 | 低机位：车道上平躺一块欧标木托盘，卡车在远处慢慢开来；标出 14.4 cm 刻度 | 新 G4 + 动画 |
| | lf02-04 落叶当障碍、真障碍看不见 | 左右分屏：落叶被框成障碍，托盘没被框 | 动画（用 G2、G4 画面） |
| | lf02-05 你会先从哪儿下手？ | 分屏停住，留白 1.2 秒 | 动画 |
| LF03 | lf03-01 传感器坏了 | 车顶激光雷达特写，落叶飘过 | 新 G5（可选，不做就用图标动画） |
| | lf03-02 记下每次停车 | 停车记录滚动 | 动画 |
| | lf03-03 四十七次 | 柱状图：其他车辆 13、定位丢失 12、天气 9、其他 13；标签「发散 → 批判」 | 动画 |
| | lf03-04 拿证据去对 | 柱状图逐条高亮 | 动画 |
| LF04 | lf04-01、lf04-02 设想测试 | 行人走上斑马线，落叶吹过，车减速；画面标「设想」 | 已有 `v6/crossing-moving.mp4` |
| | lf04-03 为谁停？ | 定格，人和落叶各打一个问号 | 动画叠在已有画面上 |
| | lf04-04 每次只改一个 | 模拟器 A/B：A 只有人，B 只有落叶；停住让观众猜 | 动画（参考 v11「Change one thing at a time」） |
| | lf04-05 问题在落叶 | B 显示 STOP | 动画 |
| | lf04-06 激光雷达少一道过滤 | 点云：一团落叶的点被判成障碍 | 动画 |
| LF05 | lf05-01、lf05-02 后车、货、电 | 后方视角：后车跟着卡车，卡车突然停，后车急刹停住（不相撞）；电量图标多耗 20% | 新 G6 + 动画 |
| | lf05-03 传得更远 | 涟漪图：一次急刹 → 后车 → 货 → 电 | 动画 |
| LF06 | lf06-01、lf06-02 调迟钝？ | 灵敏度旋钮：往迟钝拧，落叶过去了，托盘也漏了 | 动画 |
| | lf06-03 先定目标再倒推 | 目标卡「落叶：不管 / 托盘、行人：不能漏」，箭头往回指到「要分清什么」；标签「逆向」 | 动画 |
| | lf06-04 办法不只一个 | 两个办法汇合（软东西判为非障碍 + 摄像头看低矮物）；标签「综合」 | 动画 |
| LF07 | lf07-01 我们每天都在做 | 转场回家 | — |
| | lf07-02、lf07-03 纸飞机 | 折纸飞机，再扔出去 | 已有 `v5/plane_alt.mp4`、`v5/plane.mp4` |
| | lf07-04 钥匙 | 钥匙放到桌上 | 已有 `v5/keys.mp4` |
| | lf07-05 互相补充 | 片中出现过的标签一起亮起 | 动画 |
| | lf07-06 结尾问题 | 修好之后：卡车平稳开过一阵落叶，不再停；落 Lucas Academy | 新 G7 |

- **音乐**：待定。建议用 K.265 Renzi 录音，和趣味信息学系列一致，人声出现就压低。
- **音效**：刹车声、货物滑动声，只用 CC0。

## Muse 提示词（英文；1280×720 或更高，24 fps，10 秒）

卡车外观要和已有的 `truck.mp4`、`truck-headon.mp4` 一致：无标识的白色厢式卡车、秋天、阴天、湿路面。

**G1 小镇公路远景**
Generate one downloadable 10-second photoreal 16:9 video, 24 fps, one continuous shot. Educational reconstruction. A quiet small-town industrial road in Austria in autumn, overcast morning, wet asphalt, orange and yellow trees along the road, two low factory buildings in the background. A single unbranded white box truck with no driver visible drives slowly toward the camera from far away along the road. Slow steady push-in, no cuts. No people, no other vehicles, no logos, no legible text, no subtitles, no music.

**G2 保险杠前的落叶特写**
Generate one downloadable 10-second photoreal 16:9 video, 24 fps. Low macro shot at road level: four or five wet fallen orange leaves lying on dark wet asphalt, trembling slightly in a light breeze. In the soft-focus background, the white front bumper and headlights of a stopped unbranded white box truck, about two metres away. Overcast light, fixed camera, shallow depth of field, no cuts, no people, no text, no logos, no music.

**G3 货箱内货物前冲**
Generate one downloadable 10-second photoreal 16:9 video, 24 fps. Inside the cargo box of a moving delivery truck, a fixed camera mounted on the side wall. A wooden pallet stacked with plain brown cardboard boxes stands on the floor. At about 4 seconds the truck brakes hard: the boxes jolt and slide forward about half a metre, one box tips over; nothing breaks, no people. Dim interior light from a roof panel, slight camera shake at the moment of braking, one continuous shot, no text, no logos, no music.

**G4 车道上的低矮木托盘**
Generate one downloadable 10-second photoreal 16:9 video, 24 fps. Camera at ground level on a quiet wet logistics road in autumn. In the foreground, a plain wooden euro pallet lies flat across the lane, only a hand's height tall. Far in the background, an unbranded white box truck drives slowly toward the camera along the same lane and is still many metres away when the clip ends; it never reaches the pallet. Overcast light, fixed camera, no cuts, no people, no other vehicles, no text, no logos, no music.

**G5（可选）车顶激光雷达**
Generate one downloadable 10-second photoreal 16:9 video, 24 fps. Close-up of a compact roof-mounted lidar sensor (a small black cylinder) on the front edge of an unbranded white truck cab, light drizzle, a few autumn leaves drifting past the sensor. Slow orbit of about 20 degrees, one shot, no text, no logos, no people, no music.

**G6 后车急刹（不相撞）**
Generate one downloadable 10-second photoreal 16:9 video, 24 fps. Elevated fixed camera behind and slightly to the side, looking down a quiet two-lane road in autumn. An unbranded white box truck drives ahead at low speed; a small grey hatchback follows about two car lengths behind. At about 4 seconds the truck stops suddenly; the hatchback brakes hard, its nose dips, and it stops close behind the truck with a clear gap. No collision, no damage, no people visible, no text, no logos, no music. One continuous shot.

**G7 修好之后，平稳开过落叶**
Generate one downloadable 10-second photoreal 16:9 video, 24 fps. Same quiet Austrian road in autumn at late afternoon with warm low sun. A gust blows a handful of orange leaves across the lane in front of an unbranded white box truck; the truck keeps driving smoothly and steadily through the leaves without slowing and continues away from the camera. Fixed wide camera, one shot, no people, no other vehicles, no text, no logos, no music.

## 成片里的 Muse 片段（2026-11-12）

Yancy 用 `scripts/leaf-truck/muse_refs.py` 做的首帧和提示词生成了八段，存在 `lucas-academy-video-data/leaf-truck/muse/G1–G8.mp4`（`SOURCES.json` 记着 Muse 原文件名和 sha1；他那边的编号和这里不同，按画面对过）。没有重做，片段没演到的动作在剪辑里补：

| 片段 | 用在 | 怎么用 |
|---|---|---|
| G1 小镇公路远景 | lf01-01、lf01-02 | 0.85 倍，卡车冲到镜头前之前切走 |
| G8 正面，落叶前 | lf01-04 | 0.8 倍；换掉了原来那辆美式卡车 |
| G2 落叶特写 | lf01-05、片名底图 | 0.75 倍，卡车一直停着 |
| G3 货箱 | lf02-02 | 箱子没动：「往前一冲」处在 Remotion 里加急刹晃动（`jolt`） |
| G4 木托盘 | lf02-03、分屏右半 | 0.5 倍，镜头往前推；标「14.4 cm · 只有一掌高」 |
| G5 激光雷达 | lf03-01 | 从 5 秒起的特写 |
| G6 后车 | lf05-01 | 没拍出急刹，只配这一句；lf05-02 起回到涟漪图 |
| G7 夕阳 | lf07-06、片尾 | 卡车平稳开走 |

片段自带的路面声（除 G1 和斑马线那段）低低地垫在旁白下面，见 `build.py` 的 `FX_CLIPS`。
