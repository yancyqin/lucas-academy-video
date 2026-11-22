"""Put the verified English film and Chinese label sidecars in a Desktop folder."""
import hashlib,json,shutil,tempfile
from pathlib import Path

ROOT=Path('/Users/yqin/repo/playground/lucas-academy-video-data/curiosity-builds-20261118/v5')
OUT=ROOT/'delivery';DESKTOP=Path('/Users/yqin/Desktop')
def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for part in iter(lambda:f.read(4*1024*1024),b''):h.update(part)
    return h.hexdigest()
def clock(t):
    ms=round(t*1000);m,ms=divmod(ms,60000);s,ms=divmod(ms,1000)
    return f'{m:02d}:{s:02d}.{ms:03d}'
def main():
    verification=json.loads((ROOT/'records/verification.json').read_text())
    assert verification['decode']=={'returncode':0,'errors':''}
    assert verification['full']['file']==str(OUT/'curiosity-builds.en.no-voice.mp4')
    assert verification['full']['bytes']==(OUT/'curiosity-builds.en.no-voice.mp4').stat().st_size
    assert (ROOT/'records/verification.json').stat().st_mtime>=(OUT/'curiosity-builds.en.no-voice.mp4').stat().st_mtime
    subs=json.loads((ROOT/'records/subtitles.json').read_text());assert subs['cue_count']==27
    plan=json.loads(Path(__file__).with_name('plan.json').read_text())
    cues=json.loads((ROOT/'records/music-cues.json').read_text())['cues']
    music=['配乐清单（按最终视频播放顺序）','',
      f'1. {clock(cues[0]["at"])}–{clock(cues[1]["at"])}　开场、Chess','   肖邦：《降 D 大调前奏曲》Op. 28 No. 15「雨滴」','   Jeannette Fang / Musopen，CC0。','',
      f'2. {clock(cues[1]["at"])}–{clock(cues[2]["at"])}　Bible','   德彪西：《月光》Clair de lune','   Laurens Goedhart，CC BY 3.0。','',
      f'3. {clock(cues[2]["at"])}–{clock(cues[3]["at"])}　梵高房间、Journey of Art','   肖邦：《降 E 大调夜曲》Op. 9 No. 2','   Musopen，CC0；与此前视频使用同版录音。','',
      f'4. {clock(cues[3]["at"])}–{clock(cues[4]["at"])}　Sky','   巴赫：《G 弦上的咏叹调》Air，BWV 1068','   Air Force Strings / United States Air Force Band，公版录音。','',
      f'5. {clock(cues[4]["at"])}–{clock(verification["full"]["seconds"])}　Hide-and-Seek、Cube、Coder Arena、过山车与片尾','   莫扎特：《费加罗的婚礼》序曲，K. 492','   Musopen Symphony，公版录音。','   两段相接剪辑，后段接入乐曲终曲。','',
      '巴赫现在只用于 Sky。原先开场的 BWV 846《C 大调前奏曲》已替换。',
      'Jesus 视频只用于淡化、虚化的背景画面，没有使用它的音轨。',
      '各曲保留原演奏速度；Bible 画面约 2 倍速，配乐不加速。',
      '完整来源和署名见「音乐来源与署名.txt」。']
    (OUT/'音乐清单.txt').write_text('\n'.join(music)+'\n',encoding='utf-8-sig')
    staging=Path(tempfile.mkdtemp(prefix='.Curiosity-Builds-',dir=DESKTOP));segments=staging/'分段';segments.mkdir()
    copies=[(OUT/'curiosity-builds.en.no-voice.mp4',staging/'Curiosity Builds.mp4'),(OUT/'curiosity-builds.en.no-voice.zh-CN.srt',staging/'Curiosity Builds.zh-CN.srt'),(OUT/'音乐清单.txt',staging/'音乐清单.txt'),(OUT/'MUSIC-CREDITS.txt',staging/'音乐来源与署名.txt')]
    for i,p in enumerate(plan['projects'],1):
        base=f'{i:02d}-{p["id"]}.en.no-voice'
        copies.extend((OUT/(base+suffix),segments/(base+suffix)) for suffix in ['.mp4','.zh-CN.srt'])
    copies.extend((OUT/('ending-preview.en.no-voice'+suffix),segments/('ending-preview.en.no-voice'+suffix)) for suffix in ['.mp4','.zh-CN.srt'])
    receipts=[]
    for source,target in copies:
        shutil.copy2(source,target);sha=digest(source);assert sha==digest(target)
        receipts.append({'file':str(target.relative_to(staging)),'bytes':target.stat().st_size,'sha256':sha})
    note=['Curiosity Builds — 最终版','',f'英文 · 无配音 · 1920×1080 · 30 fps · 总长 {verification["full"]["seconds"]:.1f} 秒','',
      'Curiosity Builds.mp4：完整视频。','Curiosity Builds.zh-CN.srt：与完整视频同步的中文外挂字幕，翻译画面上的标题、提示词、规则标签、玩法选择和片尾。','字幕与视频放在同一文件夹，可在支持 SRT 的播放器中加载、开关；字幕没有写入画面。','',
      '分段：九个项目视频及各自的中文 SRT，另附三句片尾预览。','Bible：31.2 秒；首页选择 → Sequence/Rebuild → 首页选择 → Next Word；游戏卡片完整呈现，画面约 2 倍速。','配乐的曲目、时间和顺序见「音乐清单.txt」。']
    (staging/'使用说明.txt').write_text('\n'.join(note)+'\n',encoding='utf-8-sig')
    target=DESKTOP/'Curiosity Builds - Final';index=5
    while target.exists():target=DESKTOP/f'Curiosity Builds - Final v{index}';index+=1
    staging.rename(target)
    (ROOT/'records/desktop-delivery.json').write_text(json.dumps({'folder':str(target),'files':receipts,'subtitles':subs['cue_count'],'video_seconds':verification['full']['seconds']},ensure_ascii=False,indent=2)+'\n')
    print(str(target))
if __name__=='__main__':main()
