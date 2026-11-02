"""Generate a 看得见的诗 issue's living-painting pictures with the Codex CLI (its built-in image generator).

    python3 scripts/zhong-ying/pictures.py <art-lab checkout> <work id> [<work id> …]

The prompts live in art-lab's docs/living-image-prompts.json (the entry whose file is assets/living/<id>.jpg), with
the earlier issues' pictures it names as style references. One Codex run per picture, all at once; each writes
DATA/pictures/<id>.png (and its log and last message beside it). Check every picture, then save the chosen one as
art-lab's assets/living/<id>.jpg (1536 × 1024).
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from films import DATA  # noqa: E402

OUT = DATA / "pictures"
PRE = ("这是自动运行，没有人能回答问题：不要提问，直接做完。用内置的图像生成工具生成一张新画（附上的图只是风格参考，"
       "不要编辑它们）。生成的图会先存在 ~/.codex/generated_images 里，请把它复制到 {out}。"
       "最后一条消息写出输出路径和实际尺寸。\n\n")


def main():
    art_lab = pathlib.Path(sys.argv[1]).resolve()
    entries = {pathlib.Path(e["file"]).stem: e
               for e in json.loads((art_lab / "docs/living-image-prompts.json").read_text())["files"]}
    OUT.mkdir(parents=True, exist_ok=True)
    runs = []
    for wid in sys.argv[2:]:
        entry = entries[wid]
        out = OUT / f"{wid}.png"
        cmd = ["codex", "exec", "--skip-git-repo-check", "-s", "workspace-write", "-C", str(OUT),
               "--enable", "image_generation", "-c", 'model_reasoning_effort="medium"',
               "-o", str(OUT / f"{wid}.last.md")]
        for ref in entry["references"].split(", "):
            cmd += ["-i", str(art_lab / ref)]
        cmd += ["-"]
        log = open(OUT / f"{wid}.log", "w")
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=log, stderr=subprocess.STDOUT, text=True)
        proc.stdin.write(PRE.format(out=out) + entry["prompt"])
        proc.stdin.close()
        runs.append((wid, out, proc))
    for wid, out, proc in runs:
        code = proc.wait()
        print(wid, "exit", code, "ok" if out.exists() else "NO PICTURE")


if __name__ == "__main__":
    main()
