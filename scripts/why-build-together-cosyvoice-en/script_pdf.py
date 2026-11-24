"""Export the existing English narration faithfully as a readable PDF."""
from pathlib import Path
from xml.sax.saxutils import escape
import hashlib,json,re,shutil
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'out/why-build-together-v04/script-en.json'
TRIAL=ROOT.parent/'lucas-academy-video-data/why-build-together-20261122/cosyvoice-en-trial-20261123'
OUTPUT=ROOT/'output/pdf/with-ai-english-narration-script.pdf'
TITLE='With AI, from Curiosity to Product'

def main():
    OUTPUT.parent.mkdir(parents=True,exist_ok=True);TRIAL.mkdir(parents=True,exist_ok=True)
    rows=json.loads(SOURCE.read_text())['rows']
    expected=json.loads((ROOT/'docs/why-build-together/approved-script-en-v04.json').read_text())['rows']
    qa=json.loads((ROOT/'out/why-build-together-v04/audio/en/qa.json').read_text())
    assert [r['spoken_text'] for r in rows]==[r['spoken_text'] for r in expected]==[r['expected'] for r in qa]
    pdfmetrics.registerFont(TTFont('GeorgiaScript','/System/Library/Fonts/Supplemental/Georgia.ttf'))
    pdfmetrics.registerFont(TTFont('GeorgiaTitle','/System/Library/Fonts/Supplemental/Georgia Bold.ttf'))
    style=ParagraphStyle('script',fontName='GeorgiaScript',fontSize=14,leading=20,textColor=HexColor('#252a2c'))
    width=474
    blocks=[Paragraph(escape(r['spoken_text']),style) for r in rows]
    heights=[p.wrap(width,700)[1] for p in blocks]
    total=sum(heights)+9*(len(blocks)-1)
    assert total<=612,(total,heights)
    c=canvas.Canvas(str(OUTPUT),pagesize=(612,792),pageCompression=1)
    c.setTitle(TITLE+' - English Narration Script');c.setAuthor('Lucas Academy')
    c.setFillColor(HexColor('#626a6b'));c.setFont('Helvetica-Bold',9)
    c.drawString(54,749,'ENGLISH NARRATION SCRIPT')
    c.setFillColor(HexColor('#182124'));c.setFont('GeorgiaTitle',22)
    assert pdfmetrics.stringWidth(TITLE,'GeorgiaTitle',22)<504
    c.drawString(54,713,TITLE)
    c.setStrokeColor(HexColor('#d7dddd'));c.setLineWidth(.7);c.line(54,694,558,694)
    y=674
    for i,(row,p,h) in enumerate(zip(rows,blocks,heights),1):
        c.setFont('Helvetica',9);c.setFillColor(HexColor('#7b8383'));c.drawString(54,y-10,f'{i:02}')
        p.drawOn(c,84,y-h);y-=h+9
    assert y>48,y
    c.setStrokeColor(HexColor('#d7dddd'));c.line(54,43,558,43)
    c.setFillColor(HexColor('#697273'));c.setFont('Helvetica',8)
    c.drawString(54,28,'Lucas Academy | Current video narration | 23 Nov 2026')
    c.drawRightString(558,28,'1 / 1');c.save()
    reader=PdfReader(OUTPUT);assert len(reader.pages)==1
    text=re.sub(r'\s+',' ',reader.pages[0].extract_text()).strip()
    for row in rows:assert re.sub(r'\s+',' ',row['spoken_text']).strip() in text,row['id']
    plain='\n\n'.join(r['spoken_text'] for r in rows)+'\n'
    (TRIAL/'english-narration.txt').write_text(plain)
    payload={'title':TITLE,'language':'en','rows':rows,'source':str(SOURCE),
        'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'script_sha256':hashlib.sha256(plain.encode()).hexdigest()}
    (TRIAL/'script.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')
    shutil.copy2(OUTPUT,TRIAL/OUTPUT.name)
    report={'pdf':str(OUTPUT),'pages':1,'passages':len(rows),'words':sum(len(r['spoken_text'].split()) for r in rows),
        'all_current_narration_text_verified':True,'text_unchanged':True,'body_font_pt':14,'bottom_y_pt':round(y,2)}
    (TRIAL/'pdf-verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
