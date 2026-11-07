"""Generate localized YouTube copy in the repository's required layout."""
from pathlib import Path
import hashlib,json,sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
from youtube_tags import hashtags,tags,DEFAULT

COURSE='https://ai.lucasacademy.org/courses/zero-and-one/'
TITLES={
 'long':{'en':'Can 0 and 1 Talk?','zh':'0和1，能聊天吗？'},
 'short':{'en':'Can 0 and 1 Connect the World?','zh':'0和1，能连起全世界吗？'},
}
TOPICS={
 'long':{'en':['binary','bitsandbytes','ascii','computerscience','codingforkids','familyailab'],'zh':['二进制','信息编码','ascii','计算机科学','少儿编程','亲子学习','家庭ai实验室']},
 'short':{'en':['shorts','binary','internet','aiforkids','artificialintelligence','codingforkids','familyailab'],'zh':['shorts','二进制','互联网','人工智能','少儿编程','亲子学习','家庭ai实验室']},
}
CHAPTERS={
 'en':['A note that will not fit','Two tiny signals','A shared code','PLAY arrives','Find the hidden gift','Why four questions?','The watermelon clue','Your turn'],
 'zh':['纸条塞不进去','两种小信号','先约好编码','邀请送到了','寻找七号箱','为什么四问够用','西瓜线索','换你来发消息'],
}


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def text(kind,lang,tl):
    title=TITLES[kind][lang]
    if kind=='long':
        intro=("Mia's paper note will not fit through the pipe. She and Leo try a shared code: gold for one, blue for zero.\n\nSend PLAY, follow yes-or-no clues to a hidden gift, and find the watermelon snack. Then try a message of your own with the browser lab or a printed code table.\n\nA story for families about binary messages, bits, bytes and asking useful questions." if lang=='en' else
               '米娅的纸条塞不进管子。她和里奥先约好：金色表示一，蓝色表示零。\n\n把 PLAY 传过去，再用是否问题找出藏礼物的箱子，看看里面是什么点心。看完也能和孩子试试：打开网页实验室，或者打印编码表，互相出一道消息题。\n\n跟着两个朋友的小冒险，认识比特、字节、编码和提问的方法。')
    else:
        intro=("The note gets stuck. Tiny signals get the invitation through!\n\nJoin Mia and Leo for an adventure in space: send a message, find a hidden gift and send a reply. Their tiny pipe leads us to the internet, where videos, messages and even chats with AI use zeros and ones.\n\nA funny story? A new game? What will you share today?" if lang=='en' else
               '纸条卡住了，邀请却送到了！\n\n跟着米娅和里奥，传消息、找礼物，再回一声「收到啦」。从两个朋友的小管子，看到连起全世界的互联网：视频、消息，连和 AI 聊天，都用零和一。\n\n一个好玩的故事？一个新游戏？今天你想分享什么？')
    lab=('Try the browser lab and printable worksheets: ' if lang=='en' else '网页实验室和可打印学习单：')+COURSE
    sections=[intro,lab]
    if kind=='long':
        chapters=[]
        for scene,name in enumerate(CHAPTERS[lang],1):
            seconds=int(next(r['from'] for r in tl['lines'] if r['scene']==scene)/tl['fps']);chapters.append(f'{seconds//60:02}:{seconds%60:02} {name}')
        sections.append(('Chapters' if lang=='en' else '章节')+'\n'+'\n'.join(chapters))
        sections.append('ASCII reference: https://www.rfc-editor.org/rfc/rfc20' if lang=='en' else 'ASCII 参考：https://www.rfc-editor.org/rfc/rfc20')
    if lang=='en':
        credit='By Lucas Academy Team\nNarration: Louise, synthetic voice in English and Chinese.\nFictional space scenes: Muse. Environment artwork: ImageGen. Teaching graphics, original music and sound effects: Lucas Academy.'
        if kind=='long':credit+='\nBrowser recording and worksheets: Lucas Academy. Fruit illustrations: Microsoft Fluent Emoji (MIT).'
    else:
        credit='作者：Lucas Academy Team\n配音：Louise，中英文合成旁白。\n太空舱虚构剧情片段：Muse；场景底图：ImageGen；图解、原创配乐和音效：Lucas Academy。'
        if kind=='long':credit+='\n网页录屏与学习单：Lucas Academy；水果图片：Microsoft Fluent Emoji（MIT）。'
    own=TOPICS[kind][lang];sections.extend([credit,hashtags(own)]);description='\n\n'.join(sections);studio=tags(own)
    folder='01-长片' if kind=='long' else '02-竖屏短片';stem='0和1能聊天吗-双语长片' if kind=='long' else '0和1能聊天吗-竖屏短片'
    cover=f'03-封面/{"英文" if lang=="en" else "中文"}封面.png' if kind=='long' else '视频首帧 / First frame of the short'
    settings=(f'主视频 / Main video: {folder}/{stem}.mp4\n'
              '原始语言 / Original language: English\n'
              f'独立中文配音 / Chinese audio: {folder}/中文音轨.m4a\n'
              f'独立英文配音 / English audio: {folder}/英文音轨.m4a\n'
              f'字幕 / Captions: {folder}/{stem}.en.srt; {folder}/{stem}.zh-Hans.srt\n'
              f'封面 / Thumbnail: {cover}\n'
              f'画幅 / Aspect: {"16:9" if kind=="long" else "9:16"}\n'
              '中英文标题与简介用于同一影片的语言版本 / Localized metadata for one shared video\n'
              '类别 / Category: Education')
    output=f'【标题 / Title】\n{title}\n\n【简介 / Description】\n{description}\n\n【标签 / Tags】\n{studio}\n\n【上传设置 / Upload settings】\n{settings}\n'
    assert len(title)<=100 and len(description)<5000 and len(studio)<=500
    assert description.splitlines()[-1]==hashtags(own) and studio==studio.lower()
    assert description.splitlines()[-1].split()[:len(DEFAULT)]==['#'+t for t in DEFAULT]
    assert all(t.startswith('#') and ' ' not in t for t in studio.split())
    return output,{'title':title,'description':description,'tags':studio,'hashtagLine':hashtags(own),'uploadSettings':settings}


def main():
    doc=ROOT/'docs/family-ai-lab-02';dest=doc/'youtube';dest.mkdir(exist_ok=True);out=ROOT/'out/family-ai-lab-02/orbital-v2/youtube';out.mkdir(parents=True,exist_ok=True)
    records={}
    for kind,verify,source in [('long',doc/'design-v2/orbital-verification.json',ROOT/'public/family-ai-lab-02/orbital-v2/timeline.json'),('short',doc/'design-v2/short/verification.json',ROOT/'public/family-ai-lab-02/orbital-v2/short/timeline.json')]:
        v=json.loads(verify.read_text());tl=json.loads(source.read_text());assert sha(ROOT/v['movie'])==v['sha256'] and v['frames']==tl['durationInFrames']
        for lang in ['en','zh']:
            value,record=text(kind,lang,tl);name=f'{kind}.{lang}.txt';(dest/name).write_text(value);(out/name).write_text(value)
            records[kind+'/'+lang]={**record,'file':str((dest/name).relative_to(ROOT)),'sha256':sha(dest/name),'sourceMovieSha256':v['sha256']}
    (doc/'youtube.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n');print('Prepared four localized YouTube texts, using shared lowercase tag defaults.')


if __name__=='__main__':main()
