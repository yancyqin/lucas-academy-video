#!/usr/bin/env python3
"""What does the song demand, and does the singer cover it?

    range_check.py song <vocal-stem>              # what the song needs
    range_check.py cover <vocal-stem> <take...>   # what the singer has, per semitone

Run this BEFORE recording more and BEFORE training. A reference that misses the
song's top makes the model extrapolate, and extrapolated high notes sound fake.
"""
import subprocess, sys, numpy as np, torch, torchaudio
SR=16000; NAMES=['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
def nm(s): return f'{NAMES[s%12]}{s//12}'
def note(f): return nm(int(round(12*np.log2(f/440.0)))+57)
def f0(p):
    raw=subprocess.run(['ffmpeg','-v','error','-i',p,'-ac','1','-ar',str(SR),'-f','s16le','-'],
                       capture_output=True).stdout
    x=torch.from_numpy(np.frombuffer(raw,np.int16).astype(np.float32)/32768.0)
    W=int(SR*0.05); n=len(x)//W
    rms=torch.tensor([x[i*W:(i+1)*W].pow(2).mean().sqrt() for i in range(n)])
    loud=(20*torch.log10(rms+1e-9))>-38
    p0=torchaudio.functional.detect_pitch_frequency(x.unsqueeze(0),SR,frame_time=0.05,
                                                    freq_low=60,freq_high=1400)[0]
    m=min(len(p0),len(loud)); p0=p0[:m][loud[:m]]
    return p0[(p0>70)&(p0<1300)].numpy()
def sem(f): return np.round(12*np.log2(f/440.0)).astype(int)+57
mode=sys.argv[1]; song=sem(f0(sys.argv[2]))
need={s:(song==s).sum()/len(song) for s in set(song.tolist()) if (song==s).sum()/len(song)>0.008}
if mode=='song':
    lo,hi=np.percentile(song,2),np.percentile(song,98)
    print(f'  音域 {nm(int(lo))} - {nm(int(hi))}   中位 {nm(int(np.median(song)))}')
    print(f'\n  {"音":<6}{"占比":>8}')
    for s in sorted(need): print(f'  {nm(s):<6}{need[s]*100:7.1f}%')
else:
    takes=np.concatenate([f0(p) for p in sys.argv[3:]]); tk=sem(takes)
    print(f'  素材共 {len(takes)*0.05:.0f} 秒发声\n')
    print(f'  {"音":<6}{"歌里":>7}{"你有":>9}{"":>4}')
    gap=[]
    for s in sorted(need):
        c=(tk==s).sum()*0.05
        flag='  <-- 不足' if c<10 else ''
        if c<10: gap.append(nm(s))
        print(f'  {nm(s):<6}{need[s]*100:6.1f}%{c:8.1f}s{flag}')
    print(f'\n  {"全部达标(每音 >=10 秒)" if not gap else "还缺: "+" ".join(gap)}')
