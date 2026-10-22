#!/usr/bin/env python3
"""Run the 月光 Codex jobs with the Codex CLI (owner 2026-10-16: "你自己调用 codex cli").

  clair_codex_run.py step1                      the three photos Codex widens to 16:9 (frames/<key>.png)
  clair_codex_run.py paint TAG KEY [KEY ...]    paintings for these shot ids (paint/<key>.png);
                                                registry paint/generated-assets.TAG.json so parallel runs don't collide
Prompt text comes from clair_codex_prompts.py (the same words as the prompt sheet). Codex runs non-interactively
in a workspace-write sandbox rooted at the clair data folder; log + last message in clair/codex-runs/.
"""
import os, subprocess, sys
from clair_codex_prompts import CLAIR, STEP1, step1_lines, painting_lines, film_rows

PRE = ("这是自动运行，没有人能回答问题：不要提问，直接把表里每一张都做完。"
       "用内置的图像生成工具生成（输入照片已经附在这条消息里，生成时把对应的照片作为参考图，保证构图一致）。"
       "生成的图会先存在 ~/.codex/generated_images 里，请把每张复制到表里要求的输出路径，再登记。"
       "最后一条消息列出每张的输出路径和实际尺寸。\n\n")

def run(tag, prompt, images):
    os.makedirs(f"{CLAIR}/codex-runs", exist_ok=True)
    open(f"{CLAIR}/codex-runs/{tag}.prompt.md", "w").write(prompt)
    cmd = ["codex", "exec", "--skip-git-repo-check", "-s", "workspace-write", "-C", CLAIR,
           "--enable", "image_generation", "-c", 'model_reasoning_effort="medium"',
           "-o", f"{CLAIR}/codex-runs/{tag}.last.md"]
    for im in images: cmd += ["-i", im]
    cmd += ["-"]
    with open(f"{CLAIR}/codex-runs/{tag}.log", "w") as log:
        r = subprocess.run(cmd, input=prompt, text=True, stdout=log, stderr=subprocess.STDOUT)
    print(tag, "exit", r.returncode)
    return r.returncode

def main():
    if sys.argv[1] == "step1":
        imgs = [f"{CLAIR}/{src}" for _, src, _, _ in STEP1]
        sys.exit(run("step1", PRE + "\n".join(step1_lines()), imgs))
    if sys.argv[1] == "paint":
        tag, keys = sys.argv[2], sys.argv[3:]
        rows = [r for r in film_rows() if r[1]["id"] in keys]
        assert len(rows) == len(keys), "unknown key"
        widened = {k for k, _, _, _ in STEP1}
        imgs = [f"{CLAIR}/frames/{s['id']}.png" if s["id"] in widened else f"{CLAIR}/frames/{s['id']}.jpg" for _, s in rows]
        missing = [p for p in imgs if not os.path.exists(p)]
        assert not missing, f"missing photos: {missing}"
        sys.exit(run(tag, PRE + "\n".join(painting_lines(rows, f"generated-assets.{tag}.json")), imgs))

if __name__ == "__main__":
    main()
