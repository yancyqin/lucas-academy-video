"""Collect results/*.json into results/summary.md (the table the video quotes)."""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
R = os.path.join(HERE, 'results')


def load(name):
    path = os.path.join(R, name + '.json')
    return json.load(open(path)) if os.path.exists(path) else None


def human(seconds):
    if seconds is None:
        return '-'
    if seconds < 1e-6:
        return f'{seconds * 1e9:.0f} ns'
    if seconds < 1e-3:
        return f'{seconds * 1e6:.1f} µs'
    if seconds < 1:
        return f'{seconds * 1e3:.0f} ms'
    return f'{seconds:.2f} s'


rows = []
p = load('perceptron')
if p:
    for key, label in (('page_12_examples', 'Perceptron, 12 training pictures (the page)'), ('many_examples', 'Perceptron, 419 training pictures')):
        r = p[key]
        rows.append((label, r['setting'], f"{r['right']}/{r['n']}", human(r['median_seconds']), human(r['median_seconds']),
                     f"learned in {r['training']['rounds']} rounds, {human(r['training']['median_seconds'])}"))
js = load('perceptron-js')
if js:
    rows.append(('Perceptron, 419 training pictures, plain JavaScript', js['setting'], f"{js['right']}/{js['n']}",
                 human(js['median_seconds']), human(js['median_seconds']),
                 f"learned in {js['training']['rounds']} rounds, {human(js['training']['seconds'])}"))
page = load('page')
if page:
    rows.append(('Perceptron in the web page (Brython)', 'perceptron.html, 20 × 20', '-', human(page['brython_seconds_per_call']),
                 human(page['brython_seconds_per_call']), f"plain JavaScript: {human(page['plain_javascript_seconds_per_call'])}"))
for name, label in (('qwen-fast', 'Qwen3 8B (local, Ollama), thinking off'), ('qwen-think', 'Qwen3 8B (local, Ollama), thinking on'),
                    ('claude-fable', 'Claude Fable 5.1'), ('astra-low', 'GPT-6-Astra, reasoning low'), ('astra-xhigh', 'GPT-6-Astra, reasoning xhigh (default)')):
    r = load(name)
    if not r:
        continue
    note = ''
    if r.get('cold_start'):
        note = f"cold start (loading the model) {human(r['cold_start']['load'])}"
    rows.append((label, r['setting'], f"{r['right']}/{r['n']}", human(r['median_wall']),
                 human(r['median_model']), note + (f"; wall {human(r['min_wall'])}–{human(r['max_wall'])}" if note else f"wall {human(r['min_wall'])}–{human(r['max_wall'])}")))

lines = ['# Perceptron race: is this a 7?', '',
         'Same 10 new 20 × 20 pictures (5 sevens, 5 ones) for everyone. Language models get the picture as 20 lines of # and .',
         '(the same 400 numbers the perceptron reads) and must answer YES or NO. Times are medians per picture.', '',
         '| System | Setting | Right | End to end | Model only | Notes |', '|---|---|---|---|---|---|']
lines += ['| ' + ' | '.join(r) + ' |' for r in rows]
open(os.path.join(R, 'summary.md'), 'w').write('\n'.join(lines) + '\n')
print('\n'.join(lines))
