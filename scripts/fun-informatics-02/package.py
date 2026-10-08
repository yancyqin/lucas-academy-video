"""Prepare the approved local upload folder; this never uploads/publishes."""
import hashlib
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
PUB=ROOT / "public/fun-informatics-02"
OUT=ROOT / "out/fun-informatics-02"
DELIVERY=OUT / "delivery"
DEST=Path.home() / "Desktop/你认识Claude吗-上传"
sys.path.insert(0,str(ROOT / "scripts"))
from youtube_tags import hashtags, tags
TOPICS=["趣味信息学","信息论","claude","莫奈","香农","德彪西"]


def stamp(seconds):
    minutes,second=divmod(int(seconds),60)
    return f"{minutes:02d}:{second:02d}"


def main():
    tl=json.loads((PUB / "timeline.zh.json").read_text())
    qa=json.loads((OUT / "delivery-check.json").read_text())
    film=DELIVERY / "fun-informatics-02.zh.mp4"
    assert not tl["draft"] and hashlib.sha256(film.read_bytes()).hexdigest()==qa["sha256"]
    titles={"cl00":"从笔触开始的小游戏","cl01":"三个 Claude","cl02":"莫奈：把冗余去掉","cl03":"香农：一个字母一个字母猜","cl04":"Claude：从猜词到语言模型","cl05":"三个 Claude 的共同问题","cl06":"第四个 Claude：德彪西","cl07":"把问题带回自己的生活"}
    chapters=[]
    for prefix,title in titles.items():
        cue=next(c for c in tl["cues"] if c["id"].startswith(prefix))
        chapters.append(f"{'00:00' if prefix=='cl00' else stamp(cue['start'])} {title}")
    sources=json.loads((ROOT / "docs/fun-informatics-02/assets.json").read_text())["assets"]
    source_text="\n".join(f"- {a['title']}：{a['source']}（{a['license']}）" for a in sources)
    title="你认识 Claude 吗？｜趣味信息学2 Fun Informatics 2"
    description=f'''冗余，就是你能猜到的那部分。
从莫奈的睡莲，到香农的猜字母，再到 Claude 的语言模型：几个同名的朋友，带我们看看什么可以去掉，什么值得保留。

作者 Yancy Qin, Louise Yang | Lucas Academy
文案与 Claude 合作完成；中文配音为 AI 合成，使用 Louise 的授权声线。

一起玩：
https://bible.lucasacademy.org/?passage=JHN.3.16&translation=CUV&game=letters
https://bible.lucasacademy.org/?passage=PSA.23.1&translation=CUV&game=words

{chr(10).join(chapters)}

猜字与猜词采用四选一的教学简化。「界、代、上、人」那一步标注为教学示意；其余游戏过程来自线上实录。陌生经文的试错为脚本模拟，不是受试者实验，也不测量语言冗余率。候选概率、注意力连线和和声路线均为示意。

画面中的实景／莫奈风配对图及独轮车插图由 AI 生成，已在画面标识。莫奈真迹与老照片来源：
{source_text}

音乐：Claude Debussy《Clair de lune（月光）》，Suite bergamasque 第三首。
钢琴及录音：Laurens Goedhart（2011）。录音许可：CC BY 3.0。
https://soundcloud.com/laurensgoedhart/claude-debussys-clair-de-lune
https://commons.wikimedia.org/wiki/File:Clair_de_lune_(Claude_Debussy)_Suite_bergamasque.ogg
https://creativecommons.org/licenses/by/3.0/
本片对录音做循环、淡入淡出、音量调整及选段；和声音乐彩蛋保留真实末段与最后的和弦。
《月光》和声路线的参考分析：John Hooker，Carnegie Mellon University，Music: Under the Hood，2017。
https://johnhooker.tepper.cmu.edu/osherMusicDebussy.pdf

香农的实验与信息论：
Claude E. Shannon, A Mathematical Theory of Communication（1948）；Prediction and Entropy of Printed English（1951）。
注意力论文：Vaswani 等，Attention Is All You Need（2017）。
https://arxiv.org/abs/1706.03762

那么，在今天这个充满 AI 信息冗余的时代，你怎么分辨，这里面，有多少是新的呢？有多少是真的呢？什么是重要的呢？什么是可以忽略的呢？
这也是我们在 Lucas Academy 一起学习、一起思考的问题。

{hashtags(TOPICS)}
'''
    assert len(description)<=5000, len(description)
    content=f'''【标题 / Title】
{title}

【简介 / Description】（可直接粘贴，{len(description)} 字符）
{description}
【标签 / Tags】
{tags(TOPICS)}

【上传设置 / Upload settings】
· 视频：你认识Claude吗-中文版.mp4（1920×1080，{stamp(round(tl['durationSeconds']))}，−16 LUFS）
· 字幕：你认识Claude吗-中文字幕.srt、你认识Claude吗-English.srt
· 缩略图：你认识Claude吗-封面.jpg（1920×1080）
· 视频语言：中文（简体）
· 观众：由作者选择
· 修改过或合成的内容：是（合成配音；AI 配图）
· 类别：教育
'''
    text=DELIVERY / "upload.zh.txt";text.write_text(content)
    files={film:"你认识Claude吗-中文版.mp4",DELIVERY / "fun-informatics-02.zh.zh-Hans.srt":"你认识Claude吗-中文字幕.srt",DELIVERY / "fun-informatics-02.zh.en.srt":"你认识Claude吗-English.srt",DELIVERY / "cover.zh.jpg":"你认识Claude吗-封面.jpg",text:"你认识Claude吗-上传描述.txt"}
    assert files and all(p.is_file() for p in files)
    assert (DELIVERY / "cover.zh.jpg").stat().st_size<2_000_000
    DEST.mkdir(parents=True,exist_ok=True)
    manifest=[]
    for source,name in files.items():
        target=DEST / name
        if target.exists() and hashlib.sha256(target.read_bytes()).digest()!=hashlib.sha256(source.read_bytes()).digest():
            backup=Path.home() / "Desktop/你认识Claude吗-旧版" / datetime.now().strftime('%Y%m%d-%H%M%S')
            backup.mkdir(parents=True,exist_ok=True);shutil.copy2(target,backup / name)
        shutil.copy2(source,target)
        manifest.append({"file":name,"sha256":hashlib.sha256(target.read_bytes()).hexdigest(),"bytes":target.stat().st_size})
    (OUT / "package-manifest.json").write_text(json.dumps({"destination":str(DEST),"files":manifest},ensure_ascii=False,indent=2)+"\n")
    print(f"Chinese film, two captions, cover and description -> {DEST}",flush=True)


if __name__=="__main__":main()
