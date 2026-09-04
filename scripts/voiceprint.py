"""Speaker verification with ECAPA-TDNN (VoxCeleb). Stronger than Resemblyzer and
the usual reference for this task.

Everything is scored on many short segments so each pair gets a distribution, not
one number, and the same-speaker / different-speaker baselines are measured on the
same material.
"""
import subprocess, itertools, numpy as np, torch, warnings
warnings.filterwarnings('ignore')
from speechbrain.inference.speaker import EncoderClassifier
enc = EncoderClassifier.from_hparams(source="speechbrain/spkrec-ecapa-voxceleb",
        savedir="tmp/ecapa", run_opts={"device":"cpu"})
def segs(path, ss, dur, n, hop):
    """n embeddings of dur seconds, stepping hop, skipping quiet windows"""
    out=[]
    for i in range(n):
        t=ss+i*hop
        raw=subprocess.run(['ffmpeg','-v','error','-ss',str(t),'-t',str(dur),'-i',path,
            '-ac','1','-ar','16000','-f','s16le','-'],capture_output=True).stdout
        x=np.frombuffer(raw,np.int16).astype(np.float32)/32768.0
        if len(x)<16000*dur*0.8: continue
        if 20*np.log10(np.sqrt((x**2).mean())+1e-9) < -40: continue
        e=enc.encode_batch(torch.from_numpy(x).unsqueeze(0)).squeeze().numpy()
        out.append(e/np.linalg.norm(e))
    return out
R=''
SETS={
 'Yancy-a' : ('svc/voice/wav/yancy/y1.wav', 0, 3, 25, 4),
 'Yancy-b' : ('svc/voice/wav/yancy/y3.wav', 0, 3, 25, 4),
 'Yancy-c' : ('svc/voice/wav/yancy/y7.wav', 0, 3, 25, 6),
 'Shawn'   : ('svc/voice/wav/shawn/sh1.wav', 0, 3, 25, 3),
 'Suno'    : ('stems/0 Lead Vocals.mp3', 100, 3, 30, 5),
 '转换成品': ('out/vox/LEAD-dry.wav', 100, 3, 30, 5),
}
E={k:segs(*v) for k,v in SETS.items()}
for k,v in E.items(): print(f'  {k:<10} {len(v)} 段')
def pair(a,b):
    s=[float(x@y) for x in E[a] for y in E[b] if not (a==b and x is y)]
    return np.mean(s), np.std(s)
print('\n  基准线')
for a,b,lbl in [('Yancy-a','Yancy-b','同一人 y1/y3'),('Yancy-a','Yancy-c','同一人 y1/y7'),
                ('Yancy-b','Yancy-c','同一人 y3/y7'),('Yancy-a','Shawn','不同人 Y/Shawn'),
                ('Yancy-a','Suno','不同人 Y/Suno'),('Shawn','Suno','不同人 S/Suno')]:
    m,s=pair(a,b); print(f'    {lbl:<16} {m:+.3f} ± {s:.3f}')
print('\n  转换成品 vs')
for k in ['Yancy-a','Yancy-b','Yancy-c','Shawn','Suno']:
    m,s=pair('转换成品',k); print(f'    {k:<10} {m:+.3f} ± {s:.3f}')

# --- is the converted vocal closer to Yancy than to a control speaker? ---
from scipy import stats
def raw(a,b): return np.array([float(x@y) for x in E[a] for y in E[b]])
same = np.concatenate([raw('Yancy-a','Yancy-b'),raw('Yancy-a','Yancy-c'),raw('Yancy-b','Yancy-c')])
diff = np.concatenate([raw('Yancy-a','Shawn'),raw('Yancy-a','Suno'),raw('Shawn','Suno')])
conv_y = np.concatenate([raw('转换成品','Yancy-a'),raw('转换成品','Yancy-b'),raw('转换成品','Yancy-c')])
conv_s = raw('转换成品','Shawn')
print(f'\n  汇总 (n = 每组数百对)')
print(f'    同一人基准        {same.mean():+.3f}   n={len(same)}')
print(f'    不同人基准        {diff.mean():+.3f}   n={len(diff)}')
print(f'    成品 vs Yancy     {conv_y.mean():+.3f}   n={len(conv_y)}')
print(f'    成品 vs Shawn     {conv_s.mean():+.3f}   n={len(conv_s)}')
t,p = stats.ttest_ind(conv_y, conv_s, equal_var=False)
print(f'\n  成品更像 Yancy 还是 Shawn?  t={t:.1f}  p={p:.2e}')
t2,p2 = stats.ttest_ind(conv_y, same, equal_var=False)
print(f'  成品-Yancy 与 真同一人 有差别吗?  t={t2:.1f}  p={p2:.3f}')
# where does the converted vocal fall on the same/diff scale? 0=diff, 1=same
pos=(conv_y.mean()-diff.mean())/(same.mean()-diff.mean())
print(f'\n  把"不同人"记作 0、"同一人"记作 1,成品落在  {pos:.2f}')
