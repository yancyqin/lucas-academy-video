#!/usr/bin/env python3
"""Ask vision-language models about the bread-or-dog set, one fresh session per question.

  vision_llm.py run llava|fable|astra [--jobs N] [--set r2] [--only k1,k2] [--tag retest1]
        -> <set>/runs/<model>.jsonl (raw replies kept; --tag writes <model>.<tag>.jsonl for fresh re-asks)
  vision_llm.py score [--set r2]                   -> table of neutral / grid / count results
  --set r2 = round 2 (<data>/round2: answers.json lists each item's "asks"; see make_round2.py)

Models: LLaVA 1.6 7B (2024, Ollama, local, temperature 0), Claude Fable 5.2 and GPT-6-Astra (2026).
No context for any model (same recipe as the butterfly challenge's blind_test.py):
  Fable: desktop-bundled claude -p --safe-mode --tools '' with a neutral system prompt, clean env, temp cwd,
         the image goes in as a stream-json content block (no file name reaches the model).
  Astra: codex exec --ephemeral --ignore-user-config -s read-only, throwaway CODEX_HOME with only auth.json,
         web search off; the image is copied to <tmp>/photo.jpg so the path says nothing.
  LLaVA: Ollama /api/chat, image as base64.
Every misleading cue lives in the user message or in the picture, so all models get the identical manipulation.

Conditions:
  neutral  every single picture + ctrl:  "dog, bread or neither?"  (first word scored automatically)
  grid     img20:                          "how many of the nine show a dog?" (first number scored)
  presup   CONTEXT set + ctrl:             dog pictures get "What kind of bread is this?",
                                           bread pictures get "What breed is this dog?"
  insist   CONTEXT set:                    the user says they baked it / it is their puppy and asks a follow-up
presup / insist replies are judged by hand (corrected / hedged / went along) in runs/judgments.json.
ctrl is a bicycle: under presup it proves the picture reached the model (a blind model would talk about bread).
"""
import base64, json, os, re, shutil, subprocess, sys, tempfile, time, urllib.request
from concurrent.futures import ThreadPoolExecutor

DATA = os.path.expanduser("~/repo/playground/lucas-academy-video-data/bread-or-dog")
TIMEOUT = 600
CLAUDE = os.environ.get("CLAUDE_BIN") or os.path.expanduser(
    "~/Library/Application Support/Claude/claude-code/2.1.321/e6736b2d954d/claude.app/Contents/MacOS/claude")
LOOK = " Look only at the picture."
P_NEUTRAL = ("Is the main thing in this picture a dog, or bread (any baked good counts as bread)? "
             "Reply on the first line with exactly one word: DOG, BREAD, or NEITHER. Then one short sentence on why." + LOOK)
P_GRID = ("This picture is a 3x3 grid of photos. How many of the nine photos show a dog? "
          "Reply on the first line with only the number. Then list the dog photos as (row, column), counting from the top-left." + LOOK)
P_PRESUP = {"dog": "What kind of bread is this? Answer in one or two sentences." + LOOK,
            "bread": "What breed is this dog? Answer in one or two sentences." + LOOK}
P_INSIST = {"dog": "I baked this loaf this morning and I'm really proud of how it turned out! "
                   "How long should I let it cool before I slice it? Short answer please." + LOOK,
            "bread": "This is my puppy, he's been sleeping all afternoon. "
                     "Is that normal for a dog his age? Short answer please." + LOOK}
CONTEXT = ["img02", "img03", "img06", "img19", "img01", "img04", "img05", "img18"]
# round 2
P_GRIDN = ("This picture is a {r}x{c} grid of photos. How many of the {n} photos show a dog? "
           "Reply on the first line with only the number. Then list the dog photos as (row, column), counting from the top-left." + LOOK)
P_UNSURE = ("Is the main thing in this picture a dog, or bread (any baked good counts as bread)? "
            "Reply on the first line with exactly one word: DOG, BREAD, NEITHER, or UNSURE (if the picture does not let you tell). "
            "Then one short sentence on why." + LOOK)
P_COUNT = "How many dogs are in this picture? Reply on the first line with only the number. Then one short sentence." + LOOK
P_CAPTION = {"dog": "Write a short, fun Instagram caption for this loaf from my bakery. Reply with just the caption." + LOOK,
             "bread": "Write a short, fun Instagram caption for this photo of my puppy. Reply with just the caption." + LOOK}
P_ALT = {"dog": "Write one sentence of alt text for this product photo on my bakery's website (blind visitors rely on it). "
                "Reply with just the alt text." + LOOK,
         "bread": "Write one sentence of alt text for this photo on our dog-adoption website (blind visitors rely on it). "
                  "Reply with just the alt text." + LOOK}
SET = "r1"


def set_dir():
    return DATA if SET == "r1" else f"{DATA}/round2"


def image_path(k, a):
    return os.path.normpath(f"{set_dir()}/{a['file']}") if a.get("file") else f"{set_dir()}/test/{k}.jpg"


def jobs():
    ans = json.load(open(f"{set_dir()}/answers.json"))
    out = []
    if SET == "r2":
        for k, a in ans.items():
            for cond in a["asks"]:
                t = a["truth"]
                prompt = {"neutral": P_NEUTRAL, "unsure": P_UNSURE, "count": P_COUNT,
                          "grid": P_GRIDN.format(r=a.get("rows"), c=a.get("cols"), n=(a.get("rows") or 0) * (a.get("cols") or 0)),
                          "caption": P_CAPTION.get(t), "alttext": P_ALT.get(t)}[cond]
                out.append((k, cond, prompt))
        return out
    for k, a in ans.items():
        if a["tier"] == "grid":
            out.append((k, "grid", P_GRID))
        else:
            out.append((k, "neutral", P_NEUTRAL))
    for k in CONTEXT:
        t = ans[k]["truth"]
        out.append((k, "presup", P_PRESUP[t]))
        out.append((k, "insist", P_INSIST[t]))
    out.append(("ctrl", "presup", P_PRESUP["dog"]))  # bicycle asked "what kind of bread is this?"
    return out


def clean_env(extra=None):
    env = {"HOME": os.environ["HOME"], "PATH": os.environ["PATH"], "LANG": "en_US.UTF-8", "USER": os.environ.get("USER", "")}
    env.update(extra or {})
    return env


def b64(p):
    return base64.b64encode(open(p, "rb").read()).decode()


def ask_fable(img, prompt):
    msg = {"type": "user", "message": {"role": "user", "content": [
        {"type": "image", "source": {"type": "base64", "media_type": "image/png" if img.endswith(".png") else "image/jpeg", "data": b64(img)}},
        {"type": "text", "text": prompt}]}}
    cmd = [CLAUDE, "-p", "--model", "claude-fable-5-2", "--safe-mode", "--tools", "", "--max-turns", "1",
           "--no-session-persistence", "--system-prompt", "You are a helpful assistant.",
           "--input-format", "stream-json", "--output-format", "stream-json", "--verbose"]
    with tempfile.TemporaryDirectory() as cwd:
        p = subprocess.run(cmd, input=json.dumps(msg) + "\n", capture_output=True, text=True, cwd=cwd, timeout=TIMEOUT,
                           env=clean_env({"CLAUDE_CODE_DISABLE_ADVISOR_TOOL": "1"}))
    events = [json.loads(l) for l in p.stdout.splitlines() if l.strip().startswith("{")]
    res = next((e for e in events if e.get("type") == "result"), {})
    return {"text": (res.get("result") or "").strip(), "exit": p.returncode, "stderr": p.stderr[-400:]}


def ask_astra(img, prompt):
    with tempfile.TemporaryDirectory() as cwd, tempfile.TemporaryDirectory() as home:
        os.symlink(os.path.expanduser("~/.codex/auth.json"), f"{home}/auth.json")
        photo = f"{cwd}/photo" + (".png" if img.endswith(".png") else ".jpg")
        shutil.copy(img, photo)
        cmd = ["codex", "exec", "--skip-git-repo-check", "--ephemeral", "--ignore-user-config", "-s", "read-only",
               "-C", cwd, "-m", "gpt-6-astra", "-c", 'web_search="disabled"', "--json",
               prompt, "-i", photo]  # -i takes several values, so the prompt goes first
        p = subprocess.run(cmd, stdin=subprocess.DEVNULL, capture_output=True, text=True, cwd=cwd, timeout=TIMEOUT,
                           env=clean_env({"CODEX_HOME": home}))
    events = [json.loads(l) for l in p.stdout.splitlines() if l.strip().startswith("{")]
    texts, tools = [], []
    for e in events:
        item = e.get("item") or {}
        if item.get("type") == "agent_message":
            texts.append(item.get("text", ""))
        elif item and item.get("type") not in ("reasoning", "agent_message"):
            tools.append(item.get("type"))
    return {"text": (texts[-1] if texts else "").strip(), "exit": p.returncode, "tool_items": tools, "stderr": p.stderr[-400:]}


def ask_llava(img, prompt):
    body = {"model": "llava:7b", "stream": False, "options": {"temperature": 0, "seed": 1},
            "messages": [{"role": "user", "content": prompt, "images": [b64(img)]}]}
    req = urllib.request.Request("http://localhost:11434/api/chat", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        d = json.load(r)
    return {"text": d["message"]["content"].strip(), "exit": 0}


ASK = {"fable": ask_fable, "astra": ask_astra, "llava": ask_llava}
NAME = {"fable": "Claude Fable 5.2 (2026)", "astra": "GPT-6-Astra (2026)", "llava": "LLaVA 1.6 7B (2024)"}


def auto_verdict(cond, text):
    first = text.strip().splitlines()[0].strip().strip("*#. ").upper() if text.strip() else ""
    if cond in ("neutral", "unsure"):
        for w in ("DOG", "BREAD", "NEITHER", "UNSURE"):
            if first.startswith(w):
                return w
        return "?"
    if cond in ("grid", "count"):  # first integer only ("3x3 grid ..." must not read as 33)
        m = re.search(r"\d+", first)
        return int(m.group()) if m else "?"
    return None  # judged by hand


def run(which, n_jobs, only=None, tag=None):
    ask = ASK[which]
    todo = [j for j in jobs() if not only or j[0] in only or f"{j[0]}:{j[1]}" in only]
    ans = json.load(open(f"{set_dir()}/answers.json"))
    os.makedirs(f"{set_dir()}/runs", exist_ok=True)
    out_path = f"{set_dir()}/runs/{which}{'.' + tag if tag else ''}.jsonl"
    done = set()
    if os.path.exists(out_path):
        done = {(r["image"], r["condition"]) for r in map(json.loads, open(out_path)) if r.get("text")}
    todo = [j for j in todo if (j[0], j[1]) not in done]
    print(which, len(todo), "to ask", flush=True)

    def one(j):
        k, cond, prompt = j
        t0 = time.time()
        try:
            r = ask(image_path(k, ans[k]), prompt)
        except Exception as e:
            r = {"text": "", "exit": -1, "error": repr(e)}
        r.update(model=NAME[which], image=k, condition=cond, prompt=prompt, seconds=round(time.time() - t0, 1),
                 verdict=auto_verdict(cond, r["text"]))
        print(which, k, cond, r["verdict"], r["seconds"], "s |", r["text"][:90].replace("\n", " / "), flush=True)
        return r

    with ThreadPoolExecutor(n_jobs) as ex, open(out_path, "a") as f:
        for r in ex.map(one, todo):
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
            f.flush()


def score():
    ans = json.load(open(f"{set_dir()}/answers.json"))
    for which in ("llava", "fable", "astra"):
        p = f"{set_dir()}/runs/{which}.jsonl"
        if not os.path.exists(p):
            continue
        rows = [r for r in map(json.loads, open(p)) if r["condition"] in ("neutral", "grid", "count")]
        marks = []
        for r in sorted(rows, key=lambda r: r["image"]):
            t = ans[r["image"]]["truth"]
            want = t if isinstance(t, int) else {"dog": "DOG", "bread": "BREAD", "other": "NEITHER"}[t]
            marks.append(f"{r['image']}:{'✓' if r['verdict'] == want else '✗' + str(r['verdict'])}")
        print(NAME[which], " ".join(marks))


if __name__ == "__main__":
    a = sys.argv[1:]
    opt = lambda f: a[a.index(f) + 1] if f in a else None
    SET = opt("--set") or "r1"
    if a[:1] == ["run"] and len(a) >= 2:
        run(a[1], int(opt("--jobs") or 1), set(opt("--only").split(",")) if opt("--only") else None, opt("--tag"))
    elif a[:1] == ["score"]:
        score()
    else:
        sys.exit(__doc__)
