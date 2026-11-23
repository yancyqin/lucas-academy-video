"""Check newly generated Mandarin takes for dropped or repeated words."""
import argparse
import difflib
import hashlib
import json
from pathlib import Path
import re
import subprocess
import time

from pypinyin import lazy_pinyin, Style
from mandarin_voice_inputs import spoken, DIGITS, cardinal

P = Path(__file__).resolve().parent
OUT = P / 'checks/fangfang-mandarin-asr'
OUT.mkdir(exist_ok=True)
REPORT = P / 'checks/fangfang-mandarin-content-qa.json'


def normalize(text):
    text = re.sub(r'(?<!\d)\d{4}(?!\d)', lambda m: ''.join(DIGITS[int(d)] for d in m[0]), text)
    text = re.sub(r'\d{1,2}(?!\d)', lambda m: cardinal(m[0]), text)
    text = spoken(text)
    # Pinyin permits traditional/simplified ASR variants and homophonous names.
    text = re.sub(r'[^\u4e00-\u9fffA-Za-z0-9]', '', text).lower()
    return lazy_pinyin(text, style=Style.NORMAL, strict=False)


def check(line, path, reuse_asr=False):
    prefix = OUT / line['id']
    command = ['/opt/homebrew/bin/whisper-cli', '-m', '@USER_HOME@/.cache/whisper/ggml-small-q5_1.bin',
               '-l', 'zh', '-t', '2', '-np', '-oj', '-of', str(prefix),
               '--prompt', '肖邦，乔治桑，马略卡，戈雅，籍里柯，德拉克洛瓦，赖特，弗里德里希，透纳，物哀。',
               '-f', str(path)]
    if not reuse_asr:
        result = subprocess.run(command, capture_output=True, text=True)
        (prefix.with_suffix('.log')).write_text(result.stderr + result.stdout)
        result.check_returncode()
    transcript = json.loads(prefix.with_suffix('.json').read_text())
    heard = ''.join(segment['text'] for segment in transcript['transcription'])
    expected_units, actual_units = normalize(line['text']), normalize(heard)
    match = difflib.SequenceMatcher(None, expected_units, actual_units, autojunk=False)
    differences = [dict(operation=op, expected=' '.join(expected_units[a:b]), heard=' '.join(actual_units[c:d]))
                   for op, a, b, c, d in match.get_opcodes() if op != 'equal']
    return dict(score=round(match.ratio(), 4), heard=heard, expected=line['text'],
                differences=differences, normalizer_version=2)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--watch', action='store_true')
    args = parser.parse_args()
    lines = json.loads((P / 'voices/fangfang-mandarin.json').read_text())['lines']
    existing = json.loads(REPORT.read_text()) if REPORT.exists() else {}
    results = existing.get('takes', {})
    last_progress = time.monotonic()
    while True:
        for line in lines:
            path = P / 'voices/fangfang-mandarin' / (line['id'] + '.wav')
            if not path.is_file():
                continue
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            prior = results.get(line['id'], {})
            unchanged = prior.get('sha256') == digest
            if unchanged and prior.get('normalizer_version') == 2:
                continue
            results[line['id']] = {**check(line, path, reuse_asr=unchanged), 'sha256': digest}
            last_progress = time.monotonic()
            REPORT.write_text(json.dumps(dict(voice='fangfang/zh', language='zh', takes=results), ensure_ascii=False, indent=2))
            print(line['id'], results[line['id']]['score'], results[line['id']]['heard'], flush=True)
        if not args.watch or len(results) == len(lines):
            break
        if time.monotonic() - last_progress > 240:
            raise RuntimeError('Generation has not produced a new take for four minutes')
        time.sleep(1)
    print('Checked', len(results), 'of', len(lines), 'takes', flush=True)


if __name__ == '__main__':
    main()
