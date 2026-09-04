"""Spectrum match, with two corrections learned the hard way:

 - gains are capped at +-6 dB. Bigger boosts land on intermittent sibilance and
   blow the loudness range open (LRA went 1.4 -> 3.6 with +12 dB allowed).
 - a gentle compressor runs *after* the EQ as well, so what the EQ lifts is still
   controlled. Compression only before the EQ leaves those peaks loose.
 - level is matched in LUFS, not RMS: the ear tracks loudness, and RMS matching
   is what made the vocal read as quiet.

  matcheq2.py <in> <out> [ref_start] [ref_dur] [target_lufs]
"""
import subprocess, sys, os, re, numpy as np
SR=44100; N=8192
REF='stems/0 Lead Vocals.mp3'
BANDS=[(120,250),(250,500),(500,1000),(1000,2000),(2000,3000),
       (3000,5000),(5000,8000),(8000,12000)]
PRE='highpass=f=130:poles=2,highpass=f=130:poles=2,acompressor=threshold=0.09:ratio=4:attack=6:release=110:makeup=3'
POST='acompressor=threshold=0.25:ratio=3:attack=10:release=180:makeup=1,alimiter=limit=0.95'
def pcm(p,ss=None,t=None):
    c=['ffmpeg','-v','error']
    if ss is not None: c+=['-ss',str(ss),'-t',str(t)]
    c+=['-i',p,'-ac','1','-ar',str(SR),'-f','s16le','-']
    return np.frombuffer(subprocess.run(c,capture_output=True).stdout,np.int16).astype(np.float32)/32768.0
def spec(x):
    w=np.hanning(N); fr=max(1,(len(x)-N)//(N//2)); S=np.zeros(N//2+1)
    for i in range(fr): S+=np.abs(np.fft.rfft(x[i*N//2:i*N//2+N]*w))**2
    return S/max(1,fr)
def loud(p):
    out=subprocess.run(['ffmpeg','-hide_banner','-nostats','-i',p,'-af',
        'ebur128=framelog=quiet','-f','null','-'],capture_output=True,text=True).stderr
    tail=out[out.rfind('Summary'):]
    g=lambda k: float((re.search(rf'{k}:\s*([-\d.]+)', tail) or [0,'0'])[1])
    return g('I'), g('LRA')
src,out = sys.argv[1], sys.argv[2]
rs,rd = (float(sys.argv[3]),float(sys.argv[4])) if len(sys.argv)>4 else (117.7,13.3)
if rd < 0: rs,rd = None,None
target = float(sys.argv[5]) if len(sys.argv)>5 else None
tmp='/tmp/_pre2.wav'
subprocess.run(['ffmpeg','-v','error','-i',src,'-af',PRE,'-y',tmp],check=True)
fr=np.fft.rfftfreq(N,1/SR)
a=spec(pcm(REF,rs,rd) if rs is not None else pcm(REF)); a/=a.sum()
b=spec(pcm(tmp));       b/=b.sum()
parts=[]
for lo,hi in BANDS:
    m=(fr>=lo)&(fr<hi)
    d=10*np.log10(b[m].sum()+1e-20)-10*np.log10(a[m].sum()+1e-20)
    g=max(-6.0,min(6.0,-d))
    if abs(g)>0.4: parts.append(f'equalizer=f={int(np.sqrt(lo*hi))}:t=q:w=1.1:g={g:.1f}')
chain=PRE + (',' + ','.join(parts) if parts else '') + ',' + POST
subprocess.run(['ffmpeg','-v','error','-i',src,'-af',chain,'-y',out],check=True)
if target is not None:                       # LUFS-match to the original vocal
    I,_ = loud(out)
    subprocess.run(['ffmpeg','-v','error','-i',out,'-af',f'volume={target-I:.2f}dB',
                    '-y','/tmp/_lv.wav'],check=True)
    os.replace('/tmp/_lv.wav', out)
I,L = loud(out)
print(f'  {os.path.basename(out):<26} I={I:6.1f} LUFS   LRA={L:.1f}   ({len(parts)} 段校正)')
