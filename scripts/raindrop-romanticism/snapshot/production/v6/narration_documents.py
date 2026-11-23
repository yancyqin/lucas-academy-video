"""Deliver the locked Chinese text and its synchronized English narration."""
import hashlib
import json
from pathlib import Path
import re

from docx import Document
from docx.shared import Pt,RGBColor

P=Path(__file__).resolve().parent
DESKTOP=Path('@USER_HOME@/Desktop')
SECTION_NAMES={
    '开头':'Opening','肖邦与雨滴':'Chopin and the Raindrop Prelude',
    '革命与动荡的时代':'Revolution and Upheaval','戈雅':'Francisco Goya',
    '籍里柯':'Theodore Gericault','德拉克洛瓦':'Eugene Delacroix',
    '赖特与火山':'Joseph Wright and Vesuvius','弗里德里希':'Caspar David Friedrich',
    '雾海上的旅人':'Wanderer above the Sea of Fog','透纳':'J M W Turner',
    '雨 蒸汽与速度':'Rain Steam and Speed','感受 自然 时间 人的有限性':'Feeling Nature Time and Human Limits',
    '开头的旋律回来了':'The Opening Melody Returns','片尾彩蛋 物哀':'Closing Bonus Mono no Aware',
}
CUES={
    'cue-005':'[Music only for 10 seconds]',
    'cue-013':'[Music only: the heaviest passage before the return of the opening melody; follow the musical phrase]',
    'cue-017':'[Music only: the transition into the closing section, through the end]',
    'cue-067':'[Piano only for 12 seconds]',
    'cue-069':'[Leave space for the piano ending and resonance]',
    'cue-082':'[End of narration. Hold picture and music.]',
}


def main():
    script=json.loads((P/'narration-bilingual.json').read_text())
    source=P/'压力焦虑肖邦浪漫-已确认中文文案.docx'
    assert hashlib.sha256(source.read_bytes()).hexdigest()==script['source_sha256']
    zh=DESKTOP/'压力焦虑肖邦浪漫-中文定稿.docx';zh.write_bytes(source.read_bytes())
    template=DESKTOP/'压力焦虑肖邦浪漫-YouTube上传/10-压力焦虑肖邦浪漫-英文配音稿.docx'
    doc=Document(template)
    for element in list(doc.element.body):
        if not element.tag.endswith('}sectPr'):doc.element.body.remove(element)
    doc.add_paragraph('Pressure? Anxiety? Chopin? Romanticism?','Title')
    doc.add_paragraph('English narration script','Subtitle')
    note=doc.add_paragraph('Based on the confirmed Chinese script. Bracketed cues are for music and pauses and are not read aloud. Timing will follow the new recording.')
    for run in note.runs:run.font.size=Pt(9.5);run.font.color.rgb=RGBColor.from_string('555555')
    last=None;spoken=[]
    for row in script['rows']:
        section=row['section'].strip()
        if section!=last:
            doc.add_paragraph(SECTION_NAMES[section],'Heading 1');last=section
        if row['spoken']:
            doc.add_paragraph(row['en']);spoken.append(row['en'])
        else:
            assert row['id'] in CUES,row['id']
            paragraph=doc.add_paragraph(CUES[row['id']])
            for run in paragraph.runs:run.italic=True;run.font.size=Pt(10);run.font.color.rgb=RGBColor.from_string('555555')
    doc.core_properties.title='Pressure? Anxiety? Chopin? Romanticism?'
    doc.core_properties.author='Yancy and Eunice'
    en=DESKTOP/'压力焦虑肖邦浪漫-英文配音稿-新版.docx';doc.save(en)
    reread=Document(en)
    actual=[p.text for p in reread.paragraphs if p.text in spoken]
    assert actual==spoken
    (P/'document-delivery.json').write_text(json.dumps(dict(chinese=str(zh),english=str(en),
        chinese_exact_copy=True,source_sha256=script['source_sha256'],spoken_paragraphs=len(spoken)),ensure_ascii=False,indent=2))
    print('Updated narration Word files',zh,en,'paragraphs',len(spoken),flush=True)


if __name__=='__main__':main()
