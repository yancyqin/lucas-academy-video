"""One owner-requested Word edit, retaining every other paragraph and run style."""
from pathlib import Path
import hashlib,json,shutil
from docx import Document

P=Path(__file__).resolve().parent
PACKAGE=Path('@DATA_ROOT@/production/v12/published-release')
SOURCE=PACKAGE/'09-压力焦虑肖邦浪漫-中文文案.docx'
OUT=P/SOURCE.name
doc=Document(SOURCE)
before=[p.text for p in doc.paragraphs]
target=[p for p in doc.paragraphs if '听起来平静而优美' in p.text]
assert len(target)==1
hits=0
for run in target[0].runs:
    if '，你能想象，' in run.text:
        run.text=run.text.replace('，你能想象，','，对吗？\n但是你能想象，');hits+=1
assert hits==1
expected='听起来平静而优美，对吗？\n但是你能想象，在写这个前奏曲的那个冬天，肖邦曾在极度悲伤和焦虑中弹琴吗？'
assert target[0].text==expected
doc.save(OUT)
after=[p.text for p in Document(OUT).paragraphs]
changes=[(i,a,b) for i,(a,b) in enumerate(zip(before,after)) if a!=b]
assert len(before)==len(after) and len(changes)==1
(P/'script-change.json').write_text(json.dumps(dict(changes=changes,output=str(OUT),sha256=hashlib.sha256(OUT.read_bytes()).hexdigest()),ensure_ascii=False,indent=2))
print('One paragraph changed; all other paragraphs preserved.',flush=True)
