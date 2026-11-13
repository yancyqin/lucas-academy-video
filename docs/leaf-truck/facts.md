# 事实与出处

主出处是 AWARD 项目（欧盟 Horizon 2020）的 D7.3《Impact assessment and user survey results》，2.0 版，2024-07-10：
https://www.iru.org/system/files/AWARD_Impact%20Assessment_D7.3.pdf

补充出处是项目博客：https://award-h2020.eu/index.php/2023/08/23/award-kicks-off-the-hub-to-hub-use-case-testing/

| 稿中说法 | 原文出处 | 原文要点 |
|---|---|---|
| 奥地利小镇，两座工厂之间无人驾驶送货 | 博客 | TII KAMAG 无人驾驶电动换箱卡车（EasyMile 系统），在 Gunskirchen 的 BRP-Rotax 工厂和 DB Schenker 之间，约 600 米公路 |
| 开得很慢 | §4.8.1；博客 | 主路太窄，自动驾驶最高约 25 km/h；博客说路上 15–20 km/h |
| 落叶让它急刹 | §4.8.1 | "frequent and unnecessary braking events, particularly in response to minor obstacles like tree leaves" |
| 最多是人类司机的十一倍 | §4.8.2；§4.8.4 | "up to 11 times more stops than those of human drivers on the same route"；"11-fold increase in braking frequency" |
| 货往前冲、移位 | §4.8.1；§4.8.2 | "cargo displacement" |
| 后车可能差点追尾 | §4.8.2 | "potentially causing near-miss rear-end collisions due to unexpected stops" |
| 下雨更严重（稿中未用） | §4.8.2 | "Rainy conditions worsened the issue" |
| 看不出十四厘米高的木托盘 | §4.8.2 | "inability to detect low-lying obstacles like a euro-pallet standing only 14.4 cm tall"；建议用摄像头做数据融合 |
| 一个半月、四十七次停车 | §4.8.2 | 2023-08-07 到 09-20，7.9 小时实际行驶。分类：其他车辆 13、定位丢失 12、天气 9、安全停车 4、其他紧急停车 3、靠近路径的障碍物 3、超车 2、路上有集装箱 1 |
| 激光雷达少了一道过滤 | §4.8.1；§4.8.2；§4.8.4 | "overly sensitive lidar filter"；"lacked a rain filter"；"absence of a lidar filter to ignore trivial obstacles" |
| 电多用了大约两成 | §4.8.4 | 自动模式能耗增加 19.9–21.4%，原因是频繁刹车 |
| 把树叶、树枝归为「不是障碍」 | §5.8.2.1 | 同项目的无人叉车："classify soft obstacles like leaves and branches as non-obstacles"。稿中说「同一个项目里」，不说是卡车 |
| 加摄像头看低矮的东西 | §4.8.2 | "camera-based data fusion"，针对托盘 |

## 稿中的设想，不是报告内容

- **行人加落叶的「每次只改一个地方」测试**：这是我们设想的，不是 AWARD 做的。画面标「设想 / Thought experiment」。
- **路况和卡车镜头**：AI 生成的情景重现。画面标「情景重现 · AI 生成」，上传时勾选合成内容。

## 备用的真事（稿中未用）

- 路边植被一变，激光雷达定位就受影响（§4.8.1、§4.8.2）。
- 有司机在红灯前等了 30 秒，没看到动静，就闯了过去（§4.8.2）。
- 17% 的行驶需要人工协助，大约每小时 10 分钟（§4.8.1）。
