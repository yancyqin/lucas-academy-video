"""Races 2-4: the same 10 pictures, as text (# and .), sent to big language models.

    python3 llm_run.py ollama [--think]
    python3 llm_run.py claude
    python3 llm_run.py codex [--effort low|medium|high|xhigh]

Each call records two times: wall (end to end, what a person waits) and model (what the tool reports the
model itself took, when it reports one). Writes results/<name>.json.
"""
import json
import os
import re
import statistics
import subprocess
import sys
import tempfile
import time
import urllib.request

from pictures import TEST, prompt_for

HERE = os.path.dirname(os.path.abspath(__file__))
TIMEOUT = 600


def yes_no(text):
    words = re.findall(r'\b(YES|NO)\b', (text or '').upper())
    return {'YES': True, 'NO': False}.get(words[-1]) if words else None


def ollama(prompt, think):
    body = json.dumps({'model': 'qwen3:8b', 'prompt': prompt, 'stream': False, 'think': think,
                       'options': {'temperature': 0}}).encode()
    req = urllib.request.Request('http://localhost:11434/api/generate', data=body, headers={'Content-Type': 'application/json'})
    t0 = time.perf_counter()
    d = json.load(urllib.request.urlopen(req, timeout=TIMEOUT))
    wall = time.perf_counter() - t0
    return {'text': d.get('response', ''), 'wall': wall, 'model': d['total_duration'] / 1e9,
            'load': d.get('load_duration', 0) / 1e9, 'output_tokens': d.get('eval_count')}


def clean_env():
    # a fresh CLI login, not this session's proxy settings
    return {'HOME': os.environ['HOME'], 'PATH': os.environ['PATH'], 'LANG': 'en_US.UTF-8', 'USER': os.environ.get('USER', '')}


def claude(prompt, _):
    cmd = ['claude', '-p', '--model', 'claude-fable-5-1', '--output-format', 'json', '--max-turns', '1',
           '--tools', '', '--system-prompt', 'You answer questions about pictures.', prompt]
    with tempfile.TemporaryDirectory() as cwd:
        t0 = time.perf_counter()
        p = subprocess.run(cmd, capture_output=True, text=True, env=clean_env(), cwd=cwd, timeout=TIMEOUT)
        wall = time.perf_counter() - t0
    d = json.loads(p.stdout)
    return {'text': d.get('result', ''), 'wall': wall, 'model': d.get('duration_api_ms', 0) / 1000,
            'output_tokens': (d.get('usage') or {}).get('output_tokens'), 'error': d.get('is_error')}


def codex(prompt, effort):
    """Wall = whole codex exec run. Model = from 'turn.started' to 'turn.completed' as the events stream in,
    so Codex's own start-up (config, plugins, sandbox) is left out."""
    with tempfile.TemporaryDirectory() as cwd:
        cmd = ['codex', 'exec', '--skip-git-repo-check', '--ephemeral', '--sandbox', 'read-only', '-C', cwd,
               '-m', 'gpt-6-astra', '-c', f'model_reasoning_effort="{effort}"', '--json', prompt]
        t0 = time.perf_counter()
        errfile = tempfile.TemporaryFile(mode='w+')   # a stderr pipe left unread can fill up and stall codex
        p = subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=errfile, text=True, env=clean_env(), cwd=cwd)
        text, started, completed, usage, kinds = '', None, None, None, []
        for line in p.stdout:
            now = time.perf_counter()
            try:
                ev = json.loads(line)
            except ValueError:
                continue
            kind = ev.get('type', '')
            kinds.append(kind)
            if kind == 'turn.started' and started is None:
                started = now
            item = ev.get('item') or {}
            if item.get('type') == 'agent_message':
                text = item.get('text', '')
            if kind == 'turn.completed':
                completed, usage = now, ev.get('usage')
        p.wait(timeout=TIMEOUT)
        errfile.seek(0)
        err = errfile.read()
        wall = time.perf_counter() - t0
    return {'text': text, 'wall': wall, 'model': (completed - started) if started and completed else None,
            'output_tokens': (usage or {}).get('output_tokens'), 'reasoning_tokens': (usage or {}).get('reasoning_output_tokens'),
            'events': kinds, 'stderr_tail': err[-300:] if not text else ''}


def main():
    which = sys.argv[1]
    think = '--think' in sys.argv
    effort = sys.argv[sys.argv.index('--effort') + 1] if '--effort' in sys.argv else 'low'
    only = int(sys.argv[sys.argv.index('--only') + 1]) if '--only' in sys.argv else len(TEST)
    if which == 'ollama':
        call, setting, name = (lambda pr: ollama(pr, think)), f'qwen3:8b on this Mac, thinking {"on" if think else "off"}', f'qwen-{"think" if think else "fast"}'
        cold = ollama('Say OK.', False)   # load the model into memory first; report the cold start separately
        print(f'cold start (model load): {cold["load"]:.1f} s, wall {cold["wall"]:.1f} s')
    elif which == 'claude':
        call, setting, name, cold = (lambda pr: claude(pr, None)), 'claude-fable-5-1 via claude -p', 'claude-fable', None
    else:
        call, setting, name, cold = (lambda pr: codex(pr, effort)), f'gpt-6-astra via codex exec, reasoning {effort}', f'astra-{effort}', None
    rows = []
    for label, picture, answer in TEST[:only]:
        r = call(prompt_for(picture))
        said = yes_no(r['text'])
        rows.append({'picture': label, 'answer': answer, 'said': said, 'right': said == answer, **r})
        model = f"{r['model']:.2f} s" if r.get('model') else '-'
        print(f"  {label:8} answer {'YES' if answer else 'NO ':3} said {str(said):5} {'right' if said == answer else 'WRONG'}  "
              f"wall {r['wall']:.2f} s  model {model}  reply {r['text'][:40]!r}", flush=True)
    walls = [r['wall'] for r in rows]
    models = [r['model'] for r in rows if r.get('model')]
    out = {'system': name, 'setting': setting, 'right': sum(r['right'] for r in rows), 'n': len(rows),
           'median_wall': statistics.median(walls), 'min_wall': min(walls), 'max_wall': max(walls),
           'median_model': statistics.median(models) if models else None,
           'cold_start': cold, 'rows': rows}
    os.makedirs(os.path.join(HERE, 'results'), exist_ok=True)
    json.dump(out, open(os.path.join(HERE, 'results', f'{name}.json'), 'w'), indent=2)
    print(f"{name}: {out['right']}/{out['n']} right, median wall {out['median_wall']:.2f} s, median model "
          f"{out['median_model'] if out['median_model'] is None else round(out['median_model'], 2)} s")


if __name__ == '__main__':
    main()
