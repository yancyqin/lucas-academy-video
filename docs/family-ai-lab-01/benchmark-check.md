# 复测记录：已按 30% 门槛停止

本轮时间：20261104T230222-0800（America/Los_Angeles）。Node v22.23.1，arm64。

| 选手 | 原始 JSON 中位数 | 复测中位数 | 变化 | 准确率 |
|---|---:|---:|---:|---:|
| JavaScript 感知机 | 0.373527 微秒 | 0.375365 微秒 | +0.49% | 10/10 |
| Claude Fable 5.1 | 1.146000 秒 | 1.920500 秒 | +67.58% | 10/10 |

计时口径沿用原脚本：JavaScript 是每张图五批计时取最快值，再对十张图取中位数；Claude 是 CLI 返回的 duration_api_ms 对十张图取中位数。Claude 复测端到端中位数为 4.417478 秒；停止门槛依据模型时间。

Claude 的变化超过方案要求的 30%，因此停止，没有继续调用 Astra 和 Qwen，也没有开始 Muse 生成、配音、封面或视频渲染。没有生成审核片或封面，没有 push 或开 PR。

原始 results/*.json 未改动。两份复测 JSON、实际 stdout 和比较表在 [本轮原始记录](../../scripts/perceptron-race/reruns/20261104T230222-0800/comparison.json)。临时目录其他模型的 JSON 是运行前复制的基线，**不是本轮复测**，没有纳入本轮记录。

## 实际命令

在完整复制的 scripts/perceptron-race 目录运行，避免覆盖基线：

```sh
/Users/yqin/.nvm/versions/node/v22.23.1/bin/node perceptron_js.mjs
python3 -u llm_run.py claude
```

## Checkout

按本次用户的直接指令，没有开 worktree。原本未提交的源码、文稿和输入图保存为本地提交 946b274，另有本地分支 codex/local-checkpoint-20261104；视频和生成的 outputs 没有提交。该保存分支不发布。制作分支 codex/family-ai-lab-01 从最新 origin/main（7f05c76）建立，仅带入本片方案、实验脚本和记录。

## 下一步需要确定

以哪轮数据作为制作依据，以及后续复测是否仍采用同一停止门槛。没有把原始一轮与本轮混用来生成宣传数字。
