"""Keep Mandarin captions verbatim while spelling dates for Fangfang's reading."""
from pathlib import Path
import json
import re

P = Path(__file__).resolve().parent
DIGITS = '零一二三四五六七八九'


def cardinal(value):
    value = int(value)
    if value < 10:
        return DIGITS[value]
    if value < 100:
        ten, one = divmod(value, 10)
        return ('' if ten == 1 else DIGITS[ten]) + '十' + (DIGITS[one] if one else '')
    raise ValueError(value)


def spoken(text):
    text = ' '.join(text.split())
    text = re.sub(r'\b\d{4}\b', lambda m: ''.join(DIGITS[int(d)] for d in m[0]), text)
    text = re.sub(r'\d{1,2}(?=\s*[月日])', lambda m: cardinal(m[0]), text)
    text = re.sub(r'七\s*月\s*27\s*日到\s*29\s*日', '七月二十七日到二十九日', text)
    # Captions retain the romanization; the voice reads the Japanese word.
    text = text.replace('Mono no aware', '莫诺诺阿瓦雷').replace('（Mono）', '（莫诺）')
    text = text.replace('（Aware，', '（阿瓦雷，')
    return text


def main():
    plan = json.loads((P / 'edit-plan.json').read_text())
    lines = [dict(id=scene['id'], scene_id=scene['id'], caption=scene['text_zh'],
                  text=spoken(scene['text_zh']), speed=1.2)
             for scene in plan['scenes'] if scene.get('text_zh', '').strip()]
    assert len(lines) == 52
    payload = dict(voice='fangfang/zh', language='zh', speed=1.2,
                   mode='zero-shot', lines=lines)
    path = P / 'voices/fangfang-mandarin.json'
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n')
    print(f'{len(lines)} Mandarin paragraphs -> {path}')


if __name__ == '__main__':
    main()
