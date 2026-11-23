from pathlib import Path
import json
import re
import sys

from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn


ROOT = Path(__file__).resolve().parent
DEST = Path('@DATA_ROOT@/production/v12/published-release')
SKILL = Path('@USER_HOME@/.codex/plugins/cache/openai-primary-runtime/documents/26.1116.12010/skills/documents')
sys.path.insert(0, str(SKILL / 'scripts'))
from comments_add import add_comments

PLAN = json.loads((ROOT / 'edit-plan.json').read_text())
SECTIONS = {
    'intro': ('开头', 'Opening'),
    'chopin': ('肖邦与雨滴', 'Chopin and the Raindrop Prelude'),
    'history': ('革命与动荡的时代', 'Revolution and Upheaval'),
    'goya': ('戈雅', 'Francisco Goya'),
    'gericault': ('籍里柯', 'Theodore Gericault'),
    'delacroix': ('德拉克洛瓦', 'Eugene Delacroix'),
    'wright': ('赖特与火山', 'Joseph Wright and Vesuvius'),
    'friedrich': ('弗里德里希', 'Caspar David Friedrich'),
    'wanderer': ('雾海上的旅人', 'Wanderer above the Sea of Fog'),
    'turner': ('透纳', 'J M W Turner'),
    'railway': ('雨 蒸汽与速度', 'Rain Steam and Speed'),
    'themes': ('感受 自然 时间 人的有限性', 'Feeling Nature Time and Human Limits'),
    'conclusion': ('开头的旋律回来了', 'The Opening Melody Returns'),
    'bonus': ('片尾彩蛋 物哀', 'Closing Bonus Mono no Aware'),
}
CUES = {
    'listen': ('[纯音乐 10 秒]', '[Music only for 10 seconds]'),
    'listen-dark': ('[纯音乐 7 秒]', '[Music only for 7 seconds]'),
    'listen-return': ('[纯钢琴 12 秒]', '[Piano only for 12 seconds]'),
    'piano-ending': ('[保留钢琴尾声和余音]', '[Leave space for the piano ending and resonance]'),
    'bonus-hold': ('[停止旁白 留给画面与音乐]', '[End of narration Hold picture and music]'),
}


def set_font(style, size, bold=False, chinese=False):
    family = 'Heiti SC' if chinese else 'Arial'
    style.font.name = family
    style.font.size = Pt(size)
    style.font.bold = bold
    style.font.color.rgb = RGBColor(0, 0, 0)
    pr = style.element.get_or_add_rPr()
    fonts = pr.find(qn('w:rFonts'))
    if fonts is None:
        fonts = OxmlElement('w:rFonts')
        pr.insert(0, fonts)
    for attr in ('ascii', 'hAnsi', 'cs'):
        fonts.set(qn('w:' + attr), family)
    fonts.set(qn('w:eastAsia'), 'Heiti SC')
    for attr in ('asciiTheme', 'hAnsiTheme', 'eastAsiaTheme', 'cstheme'):
        fonts.attrib.pop(qn('w:' + attr), None)


def stamp(t):
    n = int(t)
    return f'{n // 60:02d}:{n % 60:02d}'


def clean(t):
    return re.sub(r'\s+', '', t)


def build(lang):
    zh = lang == 'zh'
    ix = 0 if zh else 1
    key = 'text_zh' if zh else 'text'
    doc = Document()
    section = doc.sections[0]
    section.page_width = Cm(21)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(1.9)
    section.bottom_margin = Cm(2.7)
    section.left_margin = Cm(2.1)
    section.right_margin = Cm(2.1)
    section.footer_distance = Cm(1.0)

    set_font(doc.styles['Normal'], 13 if zh else 12.5, chinese=zh)
    normal = doc.styles['Normal'].paragraph_format
    normal.line_spacing = 1.42
    normal.space_after = Pt(9)
    normal.widow_control = True
    set_font(doc.styles['Title'], 23, True, zh)
    doc.styles['Title'].paragraph_format.space_after = Pt(6)
    set_font(doc.styles['Subtitle'], 12, False, zh)
    doc.styles['Subtitle'].paragraph_format.space_after = Pt(10)
    set_font(doc.styles['Heading 1'], 12, True, zh)
    h = doc.styles['Heading 1'].paragraph_format
    h.space_before = Pt(15)
    h.space_after = Pt(7)
    h.keep_with_next = True
    h.keep_together = True
    set_font(doc.styles['Footer'], 9, chinese=zh)
    # python-docx's built-in template can carry a blue title border.
    for border in list(doc.styles.element.iter(qn('w:pBdr'))):
        border.getparent().remove(border)

    doc.add_paragraph('压力？焦虑？肖邦？浪漫？' if zh else 'Pressure? Anxiety? Chopin? Romanticism?', 'Title')
    doc.add_paragraph('中文配音稿' if zh else 'English Narration Script', 'Subtitle')
    intro = doc.add_paragraph(
        '正文供朗读，方括号内为音乐和停顿提示，无需朗读。时间参照当前约 14 分 45 秒的影片，录音时可自然停顿。'
        if zh else
        'Read the body text aloud. Bracketed cues are for music and pauses. Times refer to the current 14 minute 45 second edit. Allow natural pauses while recording.'
    )
    for run in intro.runs:
        run.font.size = Pt(9.5)
        run.font.color.rgb = RGBColor.from_string('555555')
    intro.paragraph_format.line_spacing = 1.2
    intro.paragraph_format.space_after = Pt(12)

    spoken = []
    prev = None
    for scene in PLAN['scenes']:
        text = scene.get(key, '').strip()
        cue = CUES.get(scene['id'])
        if not text and not cue:
            continue
        sec = scene['section']
        if sec != prev:
            doc.add_paragraph(f"{SECTIONS[sec][ix]}  {stamp(scene['start'])}", 'Heading 1')
            prev = sec
        if text:
            paragraph = doc.add_paragraph(text)
            spoken.append(paragraph.text)
        elif cue:
            paragraph = doc.add_paragraph(cue[ix])
            paragraph.paragraph_format.space_before = Pt(2)
            paragraph.paragraph_format.space_after = Pt(10)
            for run in paragraph.runs:
                run.font.size = Pt(10)
                run.italic = True
                run.font.color.rgb = RGBColor.from_string('555555')

    footer = section.footer.paragraphs[0]
    footer.alignment = 2
    footer.add_run(('中文配音稿' if zh else 'English narration') + '  ')
    field = OxmlElement('w:fldSimple')
    field.set(qn('w:instr'), 'PAGE')
    run = OxmlElement('w:r')
    value = OxmlElement('w:t')
    value.text = '1'
    run.append(value)
    field.append(run)
    footer._p.append(field)

    doc.core_properties.title = '压力？焦虑？肖邦？浪漫？' if zh else 'Pressure? Anxiety? Chopin? Romanticism?'
    doc.core_properties.subject = '中文配音稿' if zh else 'English narration script'
    doc.core_properties.author = 'Yancy and Eunice'
    output = DEST / ('09-压力焦虑肖邦浪漫-中文配音稿.docx' if zh else '10-压力焦虑肖邦浪漫-英文配音稿.docx')
    doc.save(output)
    if zh:
        temp = ROOT / 'checks' / 'mandarin-script-with-comment.docx'
        add_comments(str(output), str(temp), [
            ('其当下的闪光才格外动', '原定稿此处为“格外动”，疑似漏了“人”字。建议录音前确认是否读作“格外动人”。正文保留原稿。')
        ], author='录音校对', require_all=True)
        output.write_bytes(temp.read_bytes())

    expected = ''.join(s.get(key, '') for s in PLAN['scenes'] if s.get(key, '').strip())
    assert clean(''.join(spoken)) == clean(expected)
    reread = Document(output)
    actual = ''.join(p.text for p in reread.paragraphs if p.style.name == 'Normal')
    for text in spoken:
        assert text in actual
    print(json.dumps({'file': str(output), 'spoken_paragraphs': len(spoken), 'text_verified': True}, ensure_ascii=False))


if __name__ == '__main__':
    DEST.mkdir(exist_ok=True)
    build('zh')
    build('en')
