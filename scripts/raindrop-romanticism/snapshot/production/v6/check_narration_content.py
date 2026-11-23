"""Compare local ASR against the confirmed script; report differences for review."""
import ctypes
from difflib import SequenceMatcher
import json
from pathlib import Path
import re

P=Path(__file__).resolve().parent


def simplified(text):
    cf=ctypes.CDLL('/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation')
    pointer=ctypes.c_void_p;index=ctypes.c_long;encoding=0x08000100
    cf.CFStringCreateWithCString.argtypes=[pointer,ctypes.c_char_p,ctypes.c_uint32]
    cf.CFStringCreateWithCString.restype=pointer
    cf.CFStringCreateMutableCopy.argtypes=[pointer,index,pointer];cf.CFStringCreateMutableCopy.restype=pointer
    cf.CFStringTransform.argtypes=[pointer,pointer,pointer,ctypes.c_bool];cf.CFStringTransform.restype=ctypes.c_bool
    cf.CFStringGetCString.argtypes=[pointer,ctypes.c_char_p,index,ctypes.c_uint32];cf.CFStringGetCString.restype=ctypes.c_bool
    cf.CFRelease.argtypes=[pointer]
    original=cf.CFStringCreateWithCString(None,text.encode(),encoding)
    name=cf.CFStringCreateWithCString(None,b'Traditional-Simplified',encoding)
    mutable=cf.CFStringCreateMutableCopy(None,0,original)
    assert cf.CFStringTransform(mutable,None,name,False)
    buffer=ctypes.create_string_buffer(len(text.encode())*4+1024)
    assert cf.CFStringGetCString(mutable,buffer,len(buffer),encoding)
    result=buffer.value.decode()
    for value in [original,name,mutable]:cf.CFRelease(value)
    return result


def tokens(text,language):
    if language=='zh':
        text=simplified(text).replace('萧邦','肖邦')
        return re.findall(r'[\u3400-\u9fffA-Za-z0-9]',text.lower())
    return re.findall(r"[a-z]+|[0-9]+",text.lower())


def main():
    script=json.loads((P/'narration-bilingual.json').read_text())
    rows=[r for r in script['rows'] if r['spoken']]
    results=[]
    for language in ['zh','en']:
        source=P/f'checks/final-audio/narration-{language}.txt'
        if not source.is_file():continue
        expected=' '.join(r[language] for r in rows);actual=source.read_text()
        a=tokens(expected,language);b=tokens(actual,language)
        matcher=SequenceMatcher(None,a,b,autojunk=False)
        changes=[]
        for tag,i,j,x,y in matcher.get_opcodes():
            if tag=='equal':continue
            join='' if language=='zh' else ' '
            changes.append(dict(operation=tag,expected=join.join(a[i:j]),recognized=join.join(b[x:y]),
                                preceding=join.join(a[max(0,i-8):i]),following=join.join(a[j:j+8])))
        item=dict(language=language,paragraphs=len(rows),expected_units=len(a),recognized_units=len(b),
                  sequence_similarity=round(matcher.ratio(),5),changes=changes,
                  note='ASR differences require review; they are not automatically classified as narration mistakes.')
        results.append(item)
        print(language,'similarity',item['sequence_similarity'],'differences',len(changes))
        for change in sorted(changes,key=lambda c:len(c['expected'])+len(c['recognized']),reverse=True)[:18]:
            print(json.dumps(change,ensure_ascii=False))
    (P/'checks/content-comparison.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
