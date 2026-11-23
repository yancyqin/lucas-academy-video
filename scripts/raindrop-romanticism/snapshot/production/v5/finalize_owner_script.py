"""Apply the owner's accepted micro-edits to a separate review copy only."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import RGBColor

P = Path(__file__).resolve().parent
SOURCE = Path('@DATA_ROOT@/production/v12/published-release/09-压力焦虑肖邦浪漫-中文配音稿.docx')
OUT = P / 'script-review/2026-11-20'
DEST = Path('@USER_HOME@/Desktop/压力焦虑肖邦浪漫-最终文案-待确认.docx')
SKILL = Path('@USER_HOME@/.codex/plugins/cache/openai-primary-runtime/documents/26.1116.12010/skills/documents')
sys.path.insert(0, str(SKILL/'scripts'))
from comments_strip import strip_comments


def set_text(paragraph, text):
    # Preserve paragraph and first-run formatting while replacing accepted text.
    rpr = deepcopy(paragraph.runs[0]._r.rPr) if paragraph.runs and paragraph.runs[0]._r.rPr is not None else None
    paragraph.clear()
    run = paragraph.add_run(text)
    if rpr is not None:
        run._r.insert(0, rpr)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    original_bytes = SOURCE.read_bytes()
    original_hash = hashlib.sha256(original_bytes).hexdigest()
    snapshot = OUT/'owner-original.docx'
    if not snapshot.exists():
        snapshot.write_bytes(original_bytes)
    else:
        assert snapshot.read_bytes() == original_bytes, 'Owner source changed; inspect before retrying.'
    doc = Document(SOURCE)
    changes = []

    def replace(old, new, reason):
        matches = [p for p in doc.paragraphs if old in p.text]
        assert len(matches) == 1, (old, len(matches))
        paragraph = matches[0]
        before = paragraph.text
        after = before.replace(old, new)
        set_text(paragraph, after)
        changes.append(dict(reason=reason, before=before, after=after))

    replace('这首降D大调前奏曲全曲贯穿持续的低音重复，就像永不停歇的脉搏或滴水声，后人也因此直接将其命名为《雨滴》。',
            '这首降D大调前奏曲中，贯穿作品的重复音型，就像永不停歇的脉搏或滴水声。今天，人们也因此把它称作《雨滴》。',
            'Owner accepted repeated-note wording and the present-day Raindrop name.')
    replace('如果故事到这里就结束了，那也无从谈起浪漫。',
            '但这首曲子没有停在沉重里。', 'Owner-approved transition.')
    replace('是什么使这些浪漫主义艺术能够放下心中的牵挂、愁烦呢？是什么使他们转眼向往自然的崇高和纯粹的自由呢？',
            '这些艺术家如何带着牵挂与愁烦，仍然向往自然的崇高与自由？', 'Owner-approved central question.')
    replace('想象一下，一个人从看见王权倒下、共和国诞生、将军称帝，最后专制复辟。',
            '想象一下，一个人看见王权倒下、共和国诞生、将军称帝，最后又看见王朝复辟。',
            'Owner accepted 王朝复辟; repair the adjacent grammatical fragment.')
    replace('从 1789 年法国大革命爆发到 1875 年法兰西第三共和国宪法颁布，法国在君主制、帝制与共和制之间反反复复动荡了整整 86 年,整个欧洲大陆也经历了长达 82 年的剧烈重塑。',
            '从 1789 年法国大革命爆发，到 1875 年法兰西第三共和国宪法颁布，近一个世纪里，法国仍多次更换政体。欧洲其他地区也在这数十年间，反复经历革命、战争与政治秩序的重组。',
            'Preserve the long European upheaval context without an unsupported uniform 82-year period.')
    replace('彩蛋：日本平安时代孕育出的核心文学与美学理念，物哀Mono no aware ，',
            '彩蛋：日本的物哀美学，Mono no aware。这种感受已见于平安文学，后来由本居宣长加以理论化。',
            'Owner-approved distinction between literary sensibility and later theorization.')
    replace('这就是浪漫主义艺术家的盼望。',
            '也许，这些作品能留给我们这样的盼望。', 'Owner-approved final line.')

    # Already identified surface corrections; preserve all other narration.
    replace('二十六间', '二十六年间', 'Typo.')
    replace('把海、天气和光是他一生的题材', '把海、天气和光作为一生的题材', 'Grammar.')
    replace('其当下的闪光才格外动。', '其当下的闪光才格外动人。', 'Missing character.')
    replace('更广阔的世界和更宝贵瞬间', '更广阔的世界和更宝贵的瞬间', 'Missing character.')

    # The source contains a heading style accidentally assigned to a spoken line.
    for paragraph in doc.paragraphs:
        if paragraph.text == '我们听一听他心中最沉重的段落。':
            paragraph.style = doc.styles['Normal']
    replace('正文供朗读，方括号内为音乐和停顿提示，无需朗读。时间参照当前约 14 分 45 秒的影片，录音时可自然停顿。',
            '正文供朗读，方括号内为音乐和停顿提示，无需朗读。章节时间码沿用旧版，仅供定位；文案确认后，再按音乐与旁白重新安排。',
            'Update production guidance only; do not imply that the revised script is already timed.')

    # Use fonts available on the owner's Mac and to the bundled renderer.
    for style in doc.styles:
        if style.type != 1:
            continue
        style.font.name = 'Songti SC'
        style.font.color.rgb = RGBColor(0, 0, 0)
        pr = style.element.get_or_add_rPr()
        fonts = pr.find(qn('w:rFonts'))
        if fonts is None:
            fonts = OxmlElement('w:rFonts'); pr.insert(0, fonts)
        for attribute in ('ascii', 'hAnsi', 'eastAsia', 'cs'):
            fonts.set(qn('w:'+attribute), 'Songti SC')
        for attribute in ('asciiTheme', 'hAnsiTheme', 'eastAsiaTheme', 'cstheme'):
            fonts.attrib.pop(qn('w:'+attribute), None)
    for paragraph in doc.paragraphs:
        for run in paragraph.runs:
            run.font.name = 'Songti SC'
            run._r.get_or_add_rPr().rFonts.set(qn('w:eastAsia'), 'Songti SC')
    raw = OUT/'with-applied-edits.docx'
    doc.save(raw)
    clean = OUT/'压力焦虑肖邦浪漫-最终文案-待确认.docx'
    strip_comments(str(raw), str(clean))
    read_back = Document(clean)
    assert [p.text for p in read_back.paragraphs] == [p.text for p in doc.paragraphs]
    all_text = '\n'.join(p.text for p in read_back.paragraphs)
    for required in ['但这首曲子没有停在沉重里。', '这些艺术家如何带着牵挂与愁烦，仍然向往自然的崇高与自由？',
                     '王朝复辟', '欧洲其他地区也在这数十年间', '后来由本居宣长加以理论化',
                     '也许，这些作品能留给我们这样的盼望。']:
        assert required in all_text, required
    assert '82 年' not in all_text
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == original_hash
    DEST.write_bytes(clean.read_bytes())
    (OUT/'accepted-edits.json').write_text(json.dumps(dict(source=str(SOURCE), source_sha256=original_hash,
        output=str(DEST), output_sha256=hashlib.sha256(clean.read_bytes()).hexdigest(), changes=changes),
        ensure_ascii=False, indent=2))
    state_path = P/'next-revision.json'
    state = json.loads(state_path.read_text())
    state['status'] = 'awaiting_owner_final_script_confirmation'
    state['script_review'] = dict(file=str(DEST), accepted_changes_record=str(OUT/'accepted-edits.json'),
                                confirmation_pending=True)
    state['voice_plan'] = dict(provider='MiniMax', model='speech-2.8-hd', performance='natural narrative',
                              timbre_conversion='local CosyVoice3', english='Louise', mandarin='Fangfang',
                              native_cloning=False, full_generation='wait for script confirmation')
    state['owner_direction'].append('Owner cannot use native cloning and chooses cloud performance followed by local voice conversion. Confirm the revised script first.')
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(dict(file=str(DEST), accepted_edits=len(changes), source_unchanged=True), ensure_ascii=False))


if __name__ == '__main__':
    main()
