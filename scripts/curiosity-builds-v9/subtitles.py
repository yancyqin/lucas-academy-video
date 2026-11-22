"""Chinese sidecars for the visible editorial labels, using the exact video frame clock."""
import json,re,subprocess
from pathlib import Path

ROOT=Path('/Users/yqin/repo/playground/lucas-academy-video-data/curiosity-builds-20261118/v9')
OUT=ROOT/'delivery';PLAN=json.loads(Path(__file__).with_name('plan.json').read_text())
ZH={
 'chess':['好奇心能创造什么？','打造 Balanced Chess：逆转复活，加上落石。',None],
 'bible':['我们能用《圣经》做一个游戏吗？','读经文、藏词语，再按顺序复原。','阅读 → 记忆 → 复原'],
 'vangogh':['我们能一起装饰一间绘画房间吗？','让我们的画变成可以走进去的世界。','画作 → 灵动的表面 → 可以探索的房间'],
 'journey':['我们能一起设计你的艺术画廊吗？','汇聚我们的作品，建一座可以探索的画廊。',None],
 'sky':['我们能在灵动的天空中探索宇宙吗？','建一间漂浮的房间，让流水与群星充满生机。','流水 → 星光 → 开放世界'],
 'chameleon':['我们能做一个捉迷藏游戏吗？','画出伪装、藏进画作，邀请朋友来找你。','绘画 → 伪装 → 捉迷藏'],
 'cube':['我们能搭建一个 11×11 魔方吗？','搭建各种阶数的魔方，学会每一步。',None],
 'coder':['我们能在编程竞技场一较高下吗？','编写机器人、改进策略，让它上场。','规则 → 机器人 → 竞技场'],
 'roller':['我们能把公式变成过山车吗？','把公式变成一条盘旋而下的过山车轨道。','草图 → 方程 → 可乘坐的轨道'],
}
END_ZH=['你对什么感到好奇？','你想创造什么？','你想在哪里带来改变？']
def stamp(frame):
    ms=round(frame*1000/30);h,ms=divmod(ms,3600000);m,ms=divmod(ms,60000);s,ms=divmod(ms,1000)
    return f'{h:02d}:{m:02d}:{s:02d},{ms:03d}'
def write(path,cues,offset=0):
    previous=0
    for cue in cues:
        assert cue['start']-offset>=previous and cue['end']>cue['start']
        previous=cue['end']-offset
    blocks=[f'{i}\n{stamp(c["start"]-offset)} --> {stamp(c["end"]-offset)}\n{c["zh"]}' for i,c in enumerate(cues,1)]
    path.write_text('\n\n'.join(blocks)+'\n',encoding='utf-8-sig')
    assert len(re.findall(r'^\d+$',path.read_text(encoding='utf-8-sig'),re.M))==len(cues)
def frames(path):
    return int(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=nb_frames','-of','csv=p=0',str(path)]).strip().split(b',')[0])
def main():
    cues=[];cursor=0
    for i,p in enumerate(PLAN['projects'],1):
        pid=p['id'];q,prompt,steps=ZH[pid]
        local=[{'start':cursor,'end':cursor+90,'en':p['question'],'zh':q},
               {'start':cursor+96,'end':cursor+216,'en':p['prompt'],'zh':prompt}]
        at=cursor+216
        for clip in p['clips']:
            length=frames(ROOT/'edit'/(clip['file']+'.mp4'))
            if clip.get('rule')=='COMEBACK':
                local.append({'start':at,'end':at+length,'en':'COMEBACK\nOver 5 points behind? Earn points. Revive a piece. Each piece returns once.','zh':'逆转复活：落后超过 5 分时，可赚取积分复活棋子。\n每枚棋子只能复活一次。'})
            elif clip.get('rule')=='ROCKFALL':
                local.append({'start':at,'end':at+length,'en':'ROCKFALL\nRocks may hit the leader. Kings and queens stay safe. Level score? No rocks.','zh':'落石规则：石头可能击中领先的一方。\n国王和王后不会被击中；平分时不落石。'})
            elif pid=='coder':
                local.append({'start':at,'end':at+length,'en':'Coder Arena' if clip['file']=='coder-arena' else 'Monthly Ranking','zh':'编程竞技场' if clip['file']=='coder-arena' else '月度排行'})
            elif clip.get('subtitle_zh'):
                local.append({'start':at,'end':at+length,'en':clip['caption'],'zh':clip['subtitle_zh']})
            at+=length
        write(OUT/f'{i:02d}-{pid}.en.no-voice.zh-CN.srt',local,cursor)
        cues+=local;cursor=at
    ending=[]
    for i,(en,zh) in enumerate(zip(PLAN['ending_questions'],END_ZH)):
        ending.append({'start':cursor+i*180,'end':cursor+(i+1)*180,'en':en,'zh':zh})
    write(OUT/'ending-preview.en.no-voice.zh-CN.srt',ending,cursor)
    cues+=ending;total=frames(OUT/'curiosity-builds.en.no-voice.mp4')
    assert cues[-1]['end']==total and len(cues)==27
    write(OUT/'curiosity-builds.en.no-voice.zh-CN.srt',cues)
    (ROOT/'records/subtitles.json').write_text(json.dumps({'fps':30,'scope':'Visible project questions, process prompts, rule labels, mode choices, Coder labels, and closing questions. Two fixed intro layouts; no step chain. No spoken dialogue.','cue_count':len(cues),'total_frames':total,'cues':cues},ensure_ascii=False,indent=2)+'\n')
    print(f'Wrote {len(cues)} synchronized Chinese cues and the nine chapter sidecars.')
if __name__=='__main__':main()
