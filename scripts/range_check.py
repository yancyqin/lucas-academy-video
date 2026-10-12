#!/usr/bin/env python3
"""What does the song demand, and does the singer cover it?

    range_check.py song <vocal-stem>              # what the song needs
    range_check.py cover <vocal-stem> <take...>   # what the singer has, per semitone

Run this BEFORE recording more and BEFORE training. A reference that misses the
song's top makes the model extrapolate, and extrapolated high notes sound fake.

Pitch comes from librosa's pyin. The obvious cheaper choice, torchaudio's
detect_pitch_frequency, is autocorrelation-based and octave-HALVES on sung high
notes: it reported the Shawn takes as 8.7 s of F#4 and 42.2 s of F#3, where the
truth is 47.8 s and 14.0 s. The totals are nearly conserved, which is the
signature of the error. A direct check settled it -- on frames pyin calls F#4 the
energy at f0/2 is 50-60 dB down and no frame carries a sub-harmonic. Believing
the old numbers would have sent a singer back to re-record a range he already had.

pyin runs at 16 kHz here: nothing sung reaches 900 Hz, and the shorter lag search
is what keeps a whole song under a minute.
"""
import subprocess, sys, numpy as np, librosa

SR=16000; HOP=800                      # 50 ms frames, so counts stay in 0.05 s units
NAMES=['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
def nm(s): return f'{NAMES[s%12]}{s//12}'

def f0(p):
    raw=subprocess.run(['ffmpeg','-v','error','-i',p,'-ac','1','-ar',str(SR),'-f','s16le','-'],
                       capture_output=True).stdout
    x=np.frombuffer(raw,np.int16).astype(np.float32)/32768.0
    if len(x) < SR: return np.array([])
    f,_,_=librosa.pyin(x, fmin=65, fmax=900, sr=SR,
                       frame_length=2048, hop_length=HOP, fill_na=np.nan)
    # keep the old loudness gate: quiet frames are breath and room, not notes
    rms=librosa.feature.rms(y=x, frame_length=2048, hop_length=HOP)[0]
    n=min(len(f),len(rms)); f=f[:n]; rms=rms[:n]
    loud=(20*np.log10(rms+1e-9))>-38
    v=f[loud & ~np.isnan(f)]
    return v[(v>70)&(v<1300)]

def sem(f): return np.round(12*np.log2(f/440.0)).astype(int)+57

mode=sys.argv[1]
song=sem(f0(sys.argv[2]))
if not len(song): sys.exit('  没有从歌里取到音高')
need={s:(song==s).sum()/len(song) for s in set(song.tolist())
      if (song==s).sum()/len(song)>0.008}

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
