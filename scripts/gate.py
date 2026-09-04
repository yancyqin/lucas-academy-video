"""Silence whatever the original singer did not sing.

RVC emits a constant ~-53 dB bed through digital silence; convolution reverb then
turns it into a drifting echo. The source stem is the ground truth for when a
voice exists, so use it as the mask.

  gate.py <converted> <source> <out> [threshold_db]
"""
import subprocess, sys, numpy as np, soundfile as sf
SR=44100
def pcm(p):
    return np.frombuffer(subprocess.run(['ffmpeg','-v','error','-i',p,'-ac','1','-ar',str(SR),
        '-f','s16le','-'],capture_output=True).stdout,np.int16).astype(np.float32)/32768.0
conv, src, out = sys.argv[1], sys.argv[2], sys.argv[3]
thr = float(sys.argv[4]) if len(sys.argv)>4 else -58.0
x, s = pcm(conv), pcm(src)
n = min(len(x), len(s)); x, s = x[:n], s[:n]
W = int(SR*0.010)                                  # 10 ms envelope
m = len(s)//W
env = np.array([np.sqrt((s[i*W:(i+1)*W]**2).mean()) for i in range(m)])
db = 20*np.log10(env+1e-12)
open_ = db > thr
# widen a little so consonant onsets and natural tails are not clipped
pre, post = int(0.08/0.010), int(0.35/0.010)
g = np.zeros(m)
idx = np.where(open_)[0]
for i in idx: g[max(0,i-pre):min(m,i+post)] = 1.0
# smooth the gate itself, otherwise the edges click
k = int(0.05/0.010)
g = np.convolve(g, np.hanning(k*2+1)/np.hanning(k*2+1).sum(), 'same')
g = np.clip(g,0,1)
gate = np.repeat(g, W)
# m*W rarely equals n exactly; hold the last value rather than truncating x
gate = np.pad(gate, (0, max(0, n-len(gate))), mode='edge')[:n]
sf.write(out, x*gate, SR)
kept = gate.mean()
print(f'  {out.split("/")[-1]:<24} 门限 {thr} dB   保留 {kept*100:.1f}% 时长')
