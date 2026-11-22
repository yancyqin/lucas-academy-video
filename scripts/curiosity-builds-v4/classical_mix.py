"""Match the actual, previously used classical recordings to the picture chapters."""
import hashlib,json,re,subprocess,wave
from pathlib import Path
import numpy as np
ROOT=Path('/Users/yqin/repo/playground/lucas-academy-video-data/curiosity-builds-20261118/v4')
SR=48000
def render_music(plan,sheet,total):
    sources=json.loads((ROOT/'music/sources.json').read_text())
    dest=ROOT/'edit/classical-music.wav';receipt=ROOT/'records/music-cues.json'
    token=hashlib.sha256(json.dumps([plan,sheet,total]).encode()).hexdigest()
    if dest.exists() and receipt.exists() and json.loads(receipt.read_text()).get('digest')==token:return dest
    music=np.zeros((round(total*SR),2),dtype=np.float32);cues=[]
    indexed={p['id']:s for p,s in zip(plan['projects'],sheet)}
    for group in plan['music_groups']:
        ids=group['projects'];at=indexed[ids[0]]['start'];length=sum(indexed[k]['seconds'] for k in ids)
        if ids[0]==plan['projects'][0]['id']:at=0;length+=3
        skip=group.get('skip_first_seconds',0);at+=skip;length-=skip
        length+=group.get('include_next_intro_seconds',0)
        if group.get('through_ending'):length+=plan['ending_seconds']
        source_start=group.get('source_start',0)
        if group.get('end_at_source_end'):
            source_length=float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',sources[group['key']]['wav']]))
            source_start=source_length-length
        cues.append({'key':group['key'],'at':at,'seconds':length,'source_start':source_start,'target_lufs':group['target_lufs'],'project':group['label'],'project_ids':ids})
    assert abs(cues[0]['at'])<.001 and abs(cues[-1]['at']+cues[-1]['seconds']-total)<.001
    for before,after in zip(cues,cues[1:]):assert abs(before['at']+before['seconds']-after['at'])<.001
    for cue in cues:
        src=sources[cue['key']]['wav'];span=min(cue['seconds']+.55,total-cue['at'])
        measured=subprocess.run(['ffmpeg','-hide_banner','-nostats','-ss',str(cue['source_start']),'-t',str(cue['seconds']),'-i',src,'-af','loudnorm=I=-18.5:TP=-2.5:print_format=json','-f','null','-'],capture_output=True,text=True,check=True)
        meter=json.loads(re.search(r'\{\s*"input_i".*?\}',measured.stderr,re.S).group())
        gain=min(cue['target_lufs']-float(meter['input_i']),-2.5-float(meter['input_tp']))
        raw=subprocess.check_output(['ffmpeg','-v','error','-ss',str(cue['source_start']),'-t',str(span),'-i',src,'-ar',str(SR),'-ac','2','-f','f32le','-'])
        audio=np.frombuffer(raw,dtype='<f4').reshape(-1,2).copy();audio*=10**(gain/20)
        # Preserve each performance's dynamics: plain gain and short musical crossfades only.
        t=np.arange(len(audio),dtype=np.float32)/SR
        fade_in=.3 if cue['at']==0 else .55
        envelope=np.sin(np.minimum(1,t/fade_in)*np.pi/2)
        tail=1.8 if cue is cues[-1] else .8
        envelope*=np.sin(np.minimum(1,np.maximum(0,span-t)/tail)*np.pi/2)
        audio*=envelope[:,None];at=round(cue['at']*SR);n=min(len(audio),len(music)-at);music[at:at+n]+=audio[:n]
        cue.update({'plain_gain_db':round(gain,3),'source':src,'input_lufs':meter['input_i'],'nominal_lufs_after_gain':round(float(meter['input_i'])+gain,3)})
        print('Music',cue['project'],cue['key'],flush=True)
    peak=float(np.max(np.abs(music)));ceiling=10**(-1.8/20);headroom=min(1,ceiling/max(peak,1e-8));music*=headroom
    subprocess.run(['ffmpeg','-y','-v','error','-f','f32le','-ar',str(SR),'-ac','2','-i','pipe:0','-c:a','pcm_s24le',str(dest)],input=music.astype('<f4').tobytes(),check=True)
    receipt.write_text(json.dumps({'digest':token,'sample_rate':SR,'normalization':'constant gain per musical section, no dynamics compression','arrangement':'Bach → Chopin → Debussy → Mozart; sustained musical sections across chapter changes, with a stronger orchestral finale through the closing questions.','master_gain_db':float(20*np.log10(headroom)),'cues':cues},indent=2)+'\n')
    credits=[
      'MUSIC & RECORDING CREDITS — CURIOSITY BUILDS, ENGLISH REVISION 4','',
      'Mozart — The Marriage of Figaro, K. 492: Overture. Musopen Symphony, 2012. Public-domain recording.',sources['mozart']['page'],'',
      'Bach — Prelude in C major, BWV 846. Kimiko Ishizaka. Public-domain / Open Well-Tempered Clavier recording.',sources['bach']['page'],'',
      'Chopin — Nocturne in E-flat major, Op. 9 No. 2. Musopen CC0 recording, same recording as the earlier Lucas Academy film.',sources['chopin']['source'],'',
      'Debussy — Clair de lune. Laurens Goedhart, piano, 2011. Creative Commons Attribution 3.0.',sources['debussy']['page'],'https://creativecommons.org/licenses/by/3.0/','Changes: excerpts, level adjustments, and fades for this film.','',
      'Arrangement: measured Bach for Chess and Bible Sequence; lyrical Chopin for both art rooms; Debussy rising through Sky; Mozart continuing across Hide-and-Seek, Cube, and Coder Arena, then its orchestral finale for the actual roller coaster and closing questions.','All musical performances keep their original tempo and internal dynamics. There is no narration or captured application audio.','The master audio uses only the listed recordings.','',
      'Picture sources: Inception Space, Lucas Academy Weekly chess demos, Coder Arena, Painterly Chameleon, Bible Sequence.','Journey of Art: actual Sweet Home 3D v3 preview from the owner-selected open camera, followed by the previous film’s gallery walk at original speed (source 23.5–43.5 s).','The Sky: original in-app Cosmic Cliffs panorama (NASA/ESA/CSA/STScI), selected only for this local recording.','Blurred title and closing backgrounds: opening picture of the owner-supplied Jesus, Joy of Man’s Desiring.mp4 (source 6.5–24.5 s); its audio is not used.','Monthly Ranking is a genuine earlier server-battle recording from the Lucas Academy video archive; it does not claim a current-month result.'
    ]
    (ROOT/'delivery/MUSIC-CREDITS.txt').write_text('\n'.join(credits)+'\n')
    return dest
