"""Create a local desktop upload package from verified bilingual short films."""
import json
import shutil
import sys
from pathlib import Path
from common import ROOT,OUT,DOCS,sha

sys.path.insert(0,str(ROOT/'scripts'))
from youtube_tags import hashtags,tags

DEST=Path('/Users/yqin/Desktop/感知机与光遗传学-竖屏短片-v3')
COPY={
 'perceptron':{
  'en':('How did a 1957 model win this AI speed race?','Claude Fable 5.1 and GPT-6-Astra travel back to 1957 for a tiny recognition race. Meet the perceptron, then follow its weighted sum to matrix multiplication, a basic operation in today’s AI. At Lucas Academy, we learn step by step.\n\nThis compares speed on one specialized task. It does not rank overall model ability. Figures come from the preserved original experiment round.\n\nTry the lab: https://ai.lucasacademy.org/'),
  'zh':('一九五七年的模型，怎么跑赢大模型？','带上 Claude Fable 5.1 和 GPT-6-Astra，穿越到一九五七年，来场认数字的速度比赛。\n\n从黑格子的加权求和，到矩阵乘法，再到今天的人工智能。在 Lucas Academy，我们一起一点一点学。\n\n这是专项任务的速度对比，不代表模型整体能力的强弱。实验沿用原始整轮数据。\n\n实验室：https://ai.lucasacademy.org/'),
  'tags':['perceptron','ai','machinelearning','shorts']},
 'optogenetics':{
  'en':('The 2026 Nobel Prize in Medicine in one minute: Optogenetics','One minute on optogenetics, recognized by the 2026 Nobel Prize in Physiology or Medicine. A clue from tiny algae leads to a light-sensitive switch, special glasses, and a way to encode visual information. At Lucas Academy, we explore step by step: how do brains think, and how does AI learn?\n\nThe published 2021 case reported partial recovery in one patient. Glasses were still needed; normal vision had not returned. The moving scenes are owner-made illustrations, not documentary patient footage or a simulation of what the patient saw.\n\nPrize verification (NSF): https://www.nsf.gov/bio/updates/nsf-bio-congratulates-winners-2026-nobel-prize-physiology-or\nPrimary paper: https://pubmed.ncbi.nlm.nih.gov/34031601/'),
  'zh':('1分钟了解2026诺贝尔奖：光遗传学','一分钟了解二零二六年诺贝尔生理学或医学奖所表彰的光遗传学。\n\n线索藏在绿藻里。光开关、特制眼镜、编码和解码，一起把画面变成能传过去的消息。\n\n在 Lucas Academy，我们一起一点点探索：大脑如何思考，AI 又如何学习？\n\n影片讲的是二零二一年发表的一位病人的部分恢复。他仍需要眼镜，没有恢复正常视力。动态镜头是自制示意素材，并非病人实拍，也不模拟他看到的画面。\n\n诺奖信息（美国国家科学基金会）：https://www.nsf.gov/bio/updates/nsf-bio-congratulates-winners-2026-nobel-prize-physiology-or\n原始论文：https://pubmed.ncbi.nlm.nih.gov/34031601/'),
  'tags':['optogenetics','informatics','neuroscience','shorts']}}


def main():
    verification=json.loads((DOCS/'verification.json').read_text());assert len(verification['films'])==2
    DEST.mkdir(parents=True,exist_ok=True);copied=[]
    for film,info in COPY.items():
        folder=DEST/film;folder.mkdir(exist_ok=True)
        for name in (f'{film}.bilingual.mp4','en.m4a','zh.m4a','en.srt','zh-Hans.srt'):
            source=OUT/film/name
            if name.endswith('.mp4'):assert sha(source)==verification['films'][film]['sha256']
            target=folder/name
            if target.exists():assert sha(target)==sha(source),'Refusing differing existing package file: '+str(target)
            else:shutil.copy2(source,target)
            assert sha(source)==sha(target);copied.append(target)
        for lang in ('en','zh'):
            title,description=info[lang]
            text=f'【标题 / Title】\n{title}\n\n【简介 / Description】\n{description}\n\n{hashtags(info["tags"])}\n\n【标签 / Tags】\n{tags(info["tags"])}\n\n【上传设置 / Upload settings】\n1080×1920, 30 fps. English default audio. Add zh.m4a as Chinese audio; en.srt / zh-Hans.srt are external subtitle files. No captions are burned into the picture.\n'
            target=folder/f'youtube.{lang}.txt';target.write_text(text);copied.append(target)
    readme=DEST/'先读我.txt'
    durations={film:round(info['durationSeconds']) for film,info in verification['films'].items()}
    readme.write_text(f'''两部竖屏浓缩短片 · v3

perceptron：感知机，约{durations['perceptron']}秒。结尾：What do you want to learn about AI today? 保留矩阵乘法连接，没有二维码。
optogenetics：光遗传学，{durations['optogenetics']}秒。开场：1分钟了解2026诺贝尔奖。结尾连接大脑如何思考、AI如何学习。
两部均以在Lucas Academy一点点学习的邀请收尾。

每个文件夹内：
*.bilingual.mp4：一份共用画面，1080×1920，30fps；英文默认，中文为第二音轨。
en.m4a / zh.m4a：可单独上传的中英文音轨，与MP4内音轨一致。
en.srt / zh-Hans.srt：中英文独立字幕，画面没有烧录字幕。
youtube.en.txt / youtube.zh.txt：中英文标题、简介、标签和上传设置。

如播放器默认播放英文，可在“音轨”中切换中文。上传平台若需要独立配音，使用zh.m4a。
使用本机已有的Muse动态素材，没有额外下载。实验沿用原始数据，没有重跑。
这是本地上传包，尚未发布到任何视频平台。
''');copied.append(readme)
    (DEST/'SHA256SUMS').write_text(''.join(f'{sha(p)}  {p.relative_to(DEST)}\n' for p in sorted(copied)))
    for row in (DEST/'SHA256SUMS').read_text().splitlines():
        digest,name=row.split('  ',1);assert sha(DEST/name)==digest
    record={'path':str(DEST),'files':len(copied)+1,'sha256':{str(p.relative_to(DEST)):sha(p) for p in copied}}
    (DOCS/'upload-package.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
    print('Verified desktop package:',DEST)


if __name__=='__main__':main()
