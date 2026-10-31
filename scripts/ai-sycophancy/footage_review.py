#!/usr/bin/env python3
"""Have Codex look at the footage frame sheets and pick candidates (Yancy 10-30: 你来找，让 codex 检查吧).

  python3 scripts/ai-sycophancy/footage_review.py A B C D      run those batches in parallel
  python3 scripts/ai-sycophancy/footage_review.py --print A    show batch A's prompt and stop

The rules and the shot table are read from docs/ai-sycophancy/codex-footage.md, so the prompt says exactly what the
brief says. Each batch attaches its shots' sheets (footage/sheets/<shot>.jpg) and asks for footage/review/<batch>.json.
Codex runs in a workspace-write sandbox rooted at the footage folder, with no network.
"""
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = next(p / "lucas-academy-video-data" for p in ROOT.parents if (p / "lucas-academy-video-data").is_dir())
FOOT = DATA / "ai-sycophancy/footage"
BRIEF = (ROOT / "docs/ai-sycophancy/codex-footage.md").read_text()

BATCHES = {
    "A": ["G1", "L01", "L02", "L03", "L04", "L05", "L06", "L07", "L08", "L09", "L10"],
    "B": ["L11", "L12", "L13", "L14", "L15", "L16", "L17", "G2", "L18", "L19", "L20", "L21", "L22"],
    "C": ["L23", "L24", "L25", "L26", "L27", "L28", "L29", "G3", "L30", "L31", "G4", "L32", "L33"],
    "D": ["L34", "G5", "L35", "L36", "L37", "L38", "L39", "L40", "L41", "L42", "L43", "L44", "L45"],
    # round 2: the shots where Codex found nothing (or only weak picks), searched again with its own keywords
    "E": ["L01", "L04", "L06", "L07", "L08", "L14", "L16", "G2", "L18", "L20", "L39", "L42"],
    # round 3: the four still empty after round 2, with looser requirements (ROUND3_NOTE)
    "F": ["L14", "L16", "L18", "L39"],
}
ROUNDS = {"E": 2, "F": 3}
# earlier-round sheets that go along, so the picks can come from any round
EARLIER = {"E": {"L06", "L42"}, "F": {"L14", "L16", "L18", "L39"}}
ROUND2_NOTE = """
**这是第二轮。** 上面这些镜头第一轮没有合适的候选（L06 只有勉强的），Claude Code 用你上次给的搜索词又找了一轮。第二轮的对照图是 sheets/<镜头>-2.jpg，候选描述在 search/pexels2.json；L06 和 L42 的第一轮对照图（sheets/<镜头>.jpg，描述在 search/pexels.json）也附上了，可以两轮一起挑。因为编号会重复，picks 里的 n 写成 "1#3"、"2#5" 这样（第几轮#编号），id 一定要写对。
「要多长」只是大概的剪辑长度：可用的连续画面有 8 秒就够，不要因为比表里的秒数短就不选（第一轮 L42 就是因为这个落选的）。
"""
ROUND3_NOTE = """
**这是第三轮。** 这四个镜头前两轮都没选上，因为表里的要求组合太具体。现在放宽要求，三轮的对照图都附上了：sheets/<镜头>.jpg（描述在 search/pexels.json）、sheets/<镜头>-2.jpg（pexels2.json）、sheets/<镜头>-3.jpg（pexels3.json）。picks 里的 n 写成 "1#3"、"3#5" 这样（第几轮#编号），id 一定要写对。可用的连续画面有 8 秒就够。

放宽以后的要求（其他规矩不变）：
- L14（她觉得自己在丢词）：学英语、找词的意象就行，比如单词本、抽认卡、书页、写字的手。书页和笔记上看得清的普通英文字可以（不是品牌、不是软件界面）。人物仍然只能是手、背影或远景。
- L16（几重压力压在一起）：可以没有人，比如夜里堆满文件的书桌、一盏灯。有人的话只拍手；或者是背影、侧影，而且不是年轻亚裔女性。
- L18（2 月 7 号晚上，她和爸爸打了四十分钟电话）：雨夜的窗户、窗外虚化的城市灯光就可以，不一定要有手机。有手机的话，屏幕不能看清。
- L39（孩子为什么更愿意去问 AI，而不来问我们？）：孩子一个人看平板就可以，家长不一定入镜。白天、夜里都行。
"""
NOTES = {"E": ROUND2_NOTE, "F": ROUND3_NOTE}


def between(start: str, end: str) -> str:
    return BRIEF.split(start, 1)[1].split(end, 1)[0].strip()


RULES = between("## 规矩（每个镜头都适用）", "## 镜头表")
GREEN = between("**绿幕镜头（G1–G5）的额外要求**", "## 交付")
HEADER = "| 镜头 | 对应的句子 | 要什么画面 | 要多长 | 搜索词 |\n|---|---|---|---|---|"
ROWS, section = {}, ""
for line in BRIEF.splitlines():
    if line.startswith("### SC"):
        section = line[4:]
    elif m := re.match(r"^\| ([GL]\d+)( ★)? \|", line):
        ROWS[m[1]] = (section, line)

PROMPT = """这是自动运行，没有人能回答问题：不要提问，直接做完。不要上网，不要下载任何东西。

你是这支片的素材审核。片子是《你爱听 AI 说「是的」吗？》（「从新闻看教育」系列，观众是家长和老师）：2026 年 10 月的新闻，亚马逊机器学习工程师 Bowen Wan（31 岁）和 ChatGPT 聊了一个多月，自己把抗癫痫药减到停，2026 年 2 月因癫痫猝死，父母起诉 OpenAI，法院还没判。片子借这件事讲 AI 素养（人一倾向，AI 就顺着说「是的」），最后讲家长和孩子说话。基调同情、温和、真诚。

Claude Code 已经在 Pexels 上为每个镜头找了最多 10 个候选。每个镜头一张对照图（已附在这条消息里，也在 sheets/<镜头>.jpg）：每行一个候选，行首写着 #编号、Pexels id、尺寸、帧率、时长、作者，后面是从 15%、40%、65%、90% 处抽的 4 帧。候选的文字描述在 search/pexels.json（按镜头分组，顺序和 #编号一致，#1 是第一个）。所有候选都是 Pexels License，许可不用再查。

请你一张一张仔细看，按下面的「规矩」和这个镜头在「镜头表」里要的画面，判断每个候选能不能用，然后挑：
- 没打 ★ 的镜头：挑 1 个首选；拿不准就挑 2–3 个，写为什么拿不准。
- 打 ★ 的镜头：挑 2–3 个给 Yancy 选，按你的推荐排序。
- 一个都不合适：picks 留空，写 why_none，再给 2–3 组新的英文搜索词（search_more）。
- 只能根据对照图和描述判断。看不出来的（比如是不是 AI 生成、屏幕上有没有小标志）写进 caution，不要当成没问题。
- 同一个 Pexels id 只能用在一个镜头。

逐条检查，任何一条不过就不能当首选：
1. 画面是这个镜头要的东西，情绪和对应的句子一致。
2. 讲她的段落（SC00–SC04）：人物只能是手、背影、剪影或远景；不能有年轻亚裔女性的正脸或独处镜头，让观众以为是她。
3. 没有可辨认的品牌、标志、软件界面、可读的文字（场景本身的中文书页、作业本除外）。
4. 没有规矩里列的「不要的画面」。
5. 不像 AI 生成（手指、文字、物体变形，皮肤过分光滑）。
6. 绿幕镜头（G 开头）：屏幕是绿色或纯色，四个角都在画面里，没有大块反光；手持的在 caution 里写「需要跟踪」。
7. 机位稳定，不是快速延时摄影。

把结果写成 JSON 文件 `review/{batch}.json`（UTF-8），格式：
{{
  "L06": {{
    "star": true,
    "picks": [{{"n": 2, "id": 5473801, "why": "一句话", "caution": null}}],
    "uncertain": null,
    "why_none": null,
    "search_more": [],
    "rejected": {{"1": "一句话原因"}}
  }}
}}
picks 按推荐排序，第一个是首选。rejected 给每个没选的候选写一句短原因。写完用 python3 -m json.tool 检查文件能解析。最后一条消息只列每个镜头的首选编号，以及哪些镜头一个都没选上。

## 规矩

{rules}

**绿幕镜头（G1–G5）的额外要求**

{green}

## 本批镜头（{batch} 批）

{table}
"""


def prompt(batch: str) -> str:
    rows, last = [], None
    for shot in BATCHES[batch]:
        section, line = ROWS[shot]
        if section != last:
            rows += ["", f"### {section}", "", HEADER]
            last = section
        rows.append(line)
    text = PROMPT.format(batch=batch, rules=RULES, green=GREEN, table="\n".join(rows).strip())
    return text + NOTES.get(batch, "")


def sheets(batch: str) -> list[str]:
    r = ROUNDS.get(batch, 1)
    if r == 1:
        return [f"sheets/{shot}.jpg" for shot in BATCHES[batch]]
    out = []
    for shot in BATCHES[batch]:
        out.append(f"sheets/{shot}-{r}.jpg")
        if shot in EARLIER[batch]:
            out += [f"sheets/{shot}{'' if k == 1 else f'-{k}'}.jpg" for k in range(1, r)]
    return out


def run(batch: str) -> int:
    (FOOT / "review").mkdir(exist_ok=True)
    text = prompt(batch)
    (FOOT / f"review/{batch}.prompt.md").write_text(text)
    cmd = ["codex", "exec", "--skip-git-repo-check", "-s", "workspace-write", "-C", str(FOOT),
           "-c", 'model_reasoning_effort="high"', "-o", str(FOOT / f"review/{batch}.last.md")]
    for sheet in sheets(batch):
        cmd += ["-i", str(FOOT / sheet)]
    cmd.append("-")
    with open(FOOT / f"review/{batch}.log", "w") as log:
        code = subprocess.run(cmd, input=text, text=True, stdout=log, stderr=subprocess.STDOUT).returncode
    print(batch, "exit", code, flush=True)
    return code


args = sys.argv[1:]
if args and args[0] == "--print":
    print(prompt(args[1]))
    raise SystemExit
with ThreadPoolExecutor(len(args)) as pool:
    codes = list(pool.map(run, args))
raise SystemExit(max(codes))
