"""Match the actual, previously used classical recordings to the picture chapters."""
import hashlib,json,re,subprocess,wave
from pathlib import Path
import numpy as np
ROOT=Path('/Users/yqin/repo/playground/lucas-academy-video-data/curiosity-builds-20261118/v2')
SR=48000
def render_music(plan,sheet,total):
    sources=json.loads((ROOT/'music/sources.json').read_text())
    dest=ROOT/'edit/classical-music.wav';receipt=ROOT/'records/music-cues.json'
    token=hashlib.sha256(json.dumps([plan,sheet,total]).encode()).hexdigest()
    if dest.exists() and receipt.exists() and json.loads(receipt.read_text()).get('digest')==token:return dest
    music=np.zeros((round(total*SR),2),dtype=np.float32);cues=[]
    for i,(p,s) in enumerate(zip(plan['projects'],sheet)):
        key,source_start=p['music'];at=s['start'];length=s['seconds']
        if i==0:at=0;length+=3;source_start=0
        cues.append({'key':key,'at':at,'seconds':length,'source_start':source_start,'project':p['name']})
    cues.append({'key':'chopin','at':total-plan['ending_seconds'],'seconds':plan['ending_seconds'],'source_start':84,'project':'Five closing questions'})
    for cue in cues:
        src=sources[cue['key']]['wav'];span=min(cue['seconds']+.55,total-cue['at'])
        measured=subprocess.run(['ffmpeg','-hide_banner','-nostats','-ss',str(cue['source_start']),'-t',str(cue['seconds']),'-i',src,'-af','loudnorm=I=-18.5:TP=-2.5:print_format=json','-f','null','-'],capture_output=True,text=True,check=True)
        meter=json.loads(re.search(r'\{\s*"input_i".*?\}',measured.stderr,re.S).group())
        gain=min(-18.5-float(meter['input_i']),-2.5-float(meter['input_tp']))
        raw=subprocess.check_output(['ffmpeg','-v','error','-ss',str(cue['source_start']),'-t',str(span),'-i',src,'-ar',str(SR),'-ac','2','-f','f32le','-'])
        audio=np.frombuffer(raw,dtype='<f4').reshape(-1,2).copy();audio*=10**(gain/20)
        # Preserve each performance's dynamics: plain gain and short musical crossfades only.
        t=np.arange(len(audio),dtype=np.float32)/SR
        fade_in=.18 if cue['at']==0 else .55
        envelope=np.sin(np.minimum(1,t/fade_in)*np.pi/2)
        tail=2.4 if cue is cues[-1] else .8
        envelope*=np.sin(np.minimum(1,np.maximum(0,span-t)/tail)*np.pi/2)
        audio*=envelope[:,None];at=round(cue['at']*SR);n=min(len(audio),len(music)-at);music[at:at+n]+=audio[:n]
        cue.update({'plain_gain_db':round(gain,3),'source':src,'input_lufs':meter['input_i']})
        print('Music',cue['project'],cue['key'],flush=True)
    peak=float(np.max(np.abs(music)));ceiling=10**(-1.8/20);headroom=min(1,ceiling/max(peak,1e-8));music*=headroom
    subprocess.run(['ffmpeg','-y','-v','error','-f','f32le','-ar',str(SR),'-ac','2','-i','pipe:0','-c:a','pcm_s24le',str(dest)],input=music.astype('<f4').tobytes(),check=True)
    receipt.write_text(json.dumps({'digest':token,'sample_rate':SR,'normalization':'constant gain, no dynamics compression','master_gain_db':float(20*np.log10(headroom)),'cues':cues},indent=2)+'\n')
    credits=[
      'MUSIC & RECORDING CREDITS — CURIOSITY BUILDS, ENGLISH REVISION 2','',
      'Mozart — The Marriage of Figaro, K. 492: Overture. Musopen Symphony, 2012. Public-domain recording.',sources['mozart']['page'],'',
      'Bach — Prelude in C major, BWV 846. Kimiko Ishizaka. Public-domain / Open Well-Tempered Clavier recording.',sources['bach']['page'],'',
      'Chopin — Nocturne in E-flat major, Op. 9 No. 2. Musopen CC0 recording, same recording as the earlier Lucas Academy film.',sources['chopin']['source'],'',
      'Debussy — Clair de lune. Laurens Goedhart, piano, 2011. Creative Commons Attribution 3.0.',sources['debussy']['page'],'https://creativecommons.org/licenses/by/3.0/','Changes: excerpts, level adjustments, and fades for this film.','',
      'All musical performances keep their original tempo. There is no narration or captured application audio.','The master audio uses only the listed recordings.','',
      'Picture sources: Inception Space, Lucas Academy Weekly chess demos, Coder Arena, Painterly Chameleon, Bible Sequence.','Monthly Ranking is a genuine earlier server-battle recording from the Lucas Academy video archive; it does not claim a current-month result.'
    ]
    (ROOT/'delivery/MUSIC-CREDITS.txt').write_text('\n'.join(credits)+'\n')
    return dest
