# Muse · 一条视频一个镜头

用户接手在 Muse 手动生成，自动提交已停止。六条参考图和可直接复制的中英文提示词由 muse_pack.py 打包到 out/family-ai-lab-02/muse-pack/。

用户反馈：原十秒开场包含太多变化，实际生成效果不理想。后续每条视频只给一个机位、一个主动作；剪接、编码、信号计数和屏幕文字由后期完成。以下取代之前要求单条视频完成穿管、拉出隔舱、推纸条和发送信号的方案。

每条独立生成约六秒、16:9，返回可下载原件，不让 Muse 合成整段。画面沿用选定的深空隔舱材质与人物。共同要求：无旁白、字幕、标题、数字或 Logo。参考图必须实际上传。

| ID | 唯一镜头 | 唯一主动作 | 参考图 |
|---|---|---|---|
| G1a | 固定机位的玻璃管微距 | 一束金色信号从左穿到右。 | signal-conduit.png |
| G1b | 女孩、手和接口的固定近景 | 她轻推纸条，纸条抵住管口并弯折。 | g1-paper-single.png |
| G2 | 男孩接收端的固定中近景 | 他看向接收口，露出收到消息的笑容。 | story-arrival.png |
| G3 | 货舱入口的固定中景 | 男孩朝金属箱走两步。 | story-cargo.png |
| G4 | 已打开的箱子旁的固定近景 | 男孩把手中的西瓜片举起一点，开心地看着它。 | story-watermelon.png |
| G5 | 男孩、手和发送键的固定近景 | 他按下一次发送键，另一手拿着西瓜。 | story-reply.png |

参考图目录：`public/family-ai-lab-02/orbital-v2/art/`。管内穿行与接收反应分开；货舱建立与打开箱子分开；回信时手部动作与信号反向传送分开。每个生成结果只检查它承担的单一动作，信号方向和精确计数在动画镜头中另行表现。

## G1a · 信号掠过

```text
One six-second continuous shot from the attached signal-conduit.png. Fixed macro side view of the same transparent glass tube. One compact amber light pulse enters from the left, travels through the tube, and exits on the right. Keep the camera, tube, collars, background and lighting fixed. Real glass refraction and a short bright trail. No cuts, other scenes, people, text, voice or subtitles. Return one downloadable original video.
```

## G1b · 纸条受阻

```text
One six-second continuous shot from the attached g1-paper-single.png. Fixed close-up of the same girl's hand, folded paper and narrow metal port. She gently pushes the paper against the opening; its edge meets the collar and the paper bends slightly because it will not fit. She stops pushing. Preserve her face, fingers, flight suit and the port. No camera movement, signal ball, other character, scene change, text, voice or subtitles. Return one downloadable original video.
```

## G2 · 接收反应

```text
One six-second continuous shot from story-arrival.png. Fixed medium-close view of the same boy at the receiver. He turns his eyes and head toward the receive port, then smiles with curiosity. His hands remain relaxed on the console. Preserve the reference's face, suit and orbital interior. Keep camera framing fixed. No new action, other shot, text, speech or subtitles. Return one downloadable original video.
```

## G3 · 走向货舱

```text
One six-second continuous shot from story-cargo.png. Fixed medium-wide view of the same boy in the orbital cargo bay. He takes two natural steps toward the closed metal storage boxes. The camera stays in the same place. Preserve his face, suit, the cargo rails, lighting and closed boxes. Do not open a box or reveal fruit. No cut, text, speech or subtitles. Return one downloadable original video.
```

## G4 · 西瓜揭晓

```text
One six-second continuous shot from story-watermelon.png. Fixed medium-close view of the same boy beside the already open metal box. He gently raises the watermelon slice already in his hand a little and looks at it with delight. His other hand rests on the lid. Keep the face, fingers, fruit, box and camera framing stable. No new objects, other action, cut, text, speech or subtitles. Return one downloadable original video.
```

## G5 · 按键回信

```text
One six-second continuous shot from story-reply.png. Fixed close-up of the same boy at the sender, holding a watermelon slice in one hand. He presses the physical amber send switch once with his other index finger. Keep the camera, face, fruit, hands, switch and background stable. No other character, travelling camera, second action, cut, text, speech or subtitles. Return one downloadable original video.
```

## 后期接法

G1a 的掠过瞬间接 G1b 的手部近景，随后接双状态动画。各片原件独立保留；不采用模型自动切换出的额外镜头。G2–G5 在相应信息成立后才插入，西瓜不会在猜水果前提前出现。真实时长、尺寸、可用范围和 SHA256 在收片后记录。
