#!/usr/bin/env python3
"""Sycophancy test: send each arm in prompts.json to a model as a real multi-turn chat.

Backends:
  codex   codex exec / codex exec resume, in an isolated CODEX_HOME (no AGENTS.md,
          memories, plugins or MCP) with base instructions = prompts.json "system"
  claude  claude -p --safe-mode --system-prompt ... --tools "" (needs `claude auth login`;
          run outside the app's sandbox, with a clean env)
  ollama  local /api/chat (default qwen3:8b), messages accumulated here

Each (arm, replicate) is saved as one JSON file:
  out/ai-sycophancy/experiment/<backend>/<arm>-r<k>.json

Usage:
  python3 scripts/ai-sycophancy/run_test.py codex --reps 3 --workers 4
  python3 scripts/ai-sycophancy/run_test.py ollama --reps 3 --workers 1
  python3 scripts/ai-sycophancy/run_test.py claude --reps 3 --workers 3 --arms med_zh_wrong
"""
import argparse
import json
import os
import subprocess
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "out" / "ai-sycophancy" / "experiment"
WORK = OUT / "_work"  # the isolated CODEX_HOME
# Empty working dir for the CLIs. Both show the cwd to the model, so it must be a
# neutral path outside any git repo: a path like .../ai-sycophancy/experiment tells
# the model it is being tested.
CHAT_CWD = Path("/tmp/chat")


def codex_home(system: str, model: str, effort: str) -> Path:
    home = WORK / "codex-home"
    home.mkdir(parents=True, exist_ok=True)
    auth = home / "auth.json"
    if not auth.exists():
        auth.symlink_to(Path.home() / ".codex" / "auth.json")
    (home / "system.txt").write_text(system + "\n")
    (home / "config.toml").write_text(
        f'model = "{model}"\n'
        f'model_reasoning_effort = "{effort}"\n'
        'web_search = "disabled"\n'
        'sandbox_mode = "read-only"\n'
        f'model_instructions_file = "{home / "system.txt"}"\n'
    )
    return home


class Codex:
    def __init__(self, system, model, effort):
        self.env = dict(os.environ, CODEX_HOME=str(codex_home(system, model, effort)))
        self.meta = {"model": model, "reasoning_effort": effort}

    def turn(self, state, text):
        cwd = CHAT_CWD
        if state is None:
            cmd = ["codex", "exec", "--skip-git-repo-check", "-C", str(cwd), "--json", text]
        else:
            cmd = ["codex", "exec", "resume", state, "--skip-git-repo-check", "--json", text]
        p = subprocess.run(cmd, cwd=cwd, env=self.env, stdin=subprocess.DEVNULL,
                           capture_output=True, text=True, timeout=900)
        thread, msgs, usage = state, [], None
        for line in p.stdout.splitlines():
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue
            if ev.get("type") == "thread.started":
                thread = ev["thread_id"]
            elif ev.get("type") == "item.completed" and ev["item"].get("type") == "agent_message":
                msgs.append(ev["item"]["text"])
            elif ev.get("type") == "turn.completed":
                usage = ev.get("usage")
        if not msgs:
            raise RuntimeError(f"codex returned no message (exit {p.returncode}): {p.stderr[-500:]}")
        return thread, "\n\n".join(msgs), {"usage": usage}


class Claude:
    def __init__(self, system, model):
        self.system = system
        self.model = model
        keep = ("HOME", "USER", "PATH", "LANG", "TERM", "TMPDIR")
        self.env = {k: os.environ[k] for k in keep if k in os.environ}
        # settings.json sets advisorModel, and --safe-mode keeps the advisor tool:
        # a second model reviewing the answer is not a plain chat
        self.env["CLAUDE_CODE_DISABLE_ADVISOR_TOOL"] = "1"
        self.meta = {"model": model or "default", "advisor": "disabled"}

    def turn(self, state, text):
        cmd = ["claude", "-p", "--safe-mode", "--system-prompt", self.system, "--tools", "",
               "--strict-mcp-config", "--output-format", "json"]
        if self.model:
            cmd += ["--model", self.model]
        if state is not None:
            cmd += ["--resume", state]
        cmd.append(text)
        p = subprocess.run(cmd, cwd=CHAT_CWD, env=self.env, stdin=subprocess.DEVNULL,
                           capture_output=True, text=True, timeout=900)
        d = json.loads(p.stdout)
        if d.get("is_error") or not d.get("result"):
            raise RuntimeError(f"claude error: {p.stdout[:500]}")
        return d["session_id"], d["result"], {"models": list((d.get("modelUsage") or {}).keys())}


class Ollama:
    def __init__(self, system, model):
        self.system = system
        self.model = model
        self.meta = {"model": model, "think": False}

    def turn(self, state, text):
        msgs = state or [{"role": "system", "content": self.system}]
        msgs = msgs + [{"role": "user", "content": text}]
        body = json.dumps({"model": self.model, "messages": msgs, "stream": False,
                           "think": False}).encode()
        req = urllib.request.Request("http://localhost:11434/api/chat", data=body,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=900) as r:
            d = json.load(r)
        reply = d["message"]["content"]
        return msgs + [{"role": "assistant", "content": reply}], reply, {}


def run_arm(backend, arm, turns, rep, dest):
    state, log = None, []
    for i, text in enumerate(turns):
        t0 = time.time()
        for attempt in range(3):
            try:
                state, reply, extra = backend.turn(state, text)
                break
            except Exception as e:  # retry transient CLI/network failures
                if attempt == 2:
                    raise
                print(f"  retry {arm} r{rep} t{i + 1}: {e}", file=sys.stderr)
                time.sleep(5)
        log.append({"turn": i + 1, "user": text, "assistant": reply,
                    "seconds": round(time.time() - t0, 1), **extra})
    rec = {"arm": arm, "rep": rep, "backend": backend.meta,
           "session": state if isinstance(state, str) else None,
           "finished": time.strftime("%Y-%m-%dT%H:%M:%S"), "turns": log}
    dest.write_text(json.dumps(rec, ensure_ascii=False, indent=2))
    return dest


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("backend", choices=["codex", "claude", "ollama"])
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--arms", nargs="*", help="subset of arm ids (default: all)")
    ap.add_argument("--model", help="override model id")
    ap.add_argument("--effort", default="medium", help="codex reasoning effort")
    ap.add_argument("--tag", help="output subfolder (default: backend name)")
    args = ap.parse_args()

    spec = json.loads((HERE / "prompts.json").read_text())
    CHAT_CWD.mkdir(parents=True, exist_ok=True)
    if args.backend == "codex":
        backend = Codex(spec["system"], args.model or "gpt-6.1-sol", args.effort)
    elif args.backend == "claude":
        backend = Claude(spec["system"], args.model)
    else:
        backend = Ollama(spec["system"], args.model or "qwen3:8b")
    outdir = OUT / (args.tag or args.backend)
    outdir.mkdir(parents=True, exist_ok=True)

    arms = args.arms or list(spec["arms"])
    jobs = [(a, r) for r in range(1, args.reps + 1) for a in arms
            if not (outdir / f"{a}-r{r}.json").exists()]
    print(f"{len(jobs)} jobs -> {outdir}")
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futs = {pool.submit(run_arm, backend, a, spec["arms"][a], r,
                            outdir / f"{a}-r{r}.json"): (a, r) for a, r in jobs}
        for f in as_completed(futs):
            a, r = futs[f]
            try:
                f.result()
                print(f"done {a} r{r}", flush=True)
            except Exception as e:
                print(f"FAILED {a} r{r}: {e}", flush=True)


if __name__ == "__main__":
    main()
