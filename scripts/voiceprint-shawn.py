"""Speaker verification for the Shawn model — is the converted vocal Shawn?

Same method as voiceprint.py (ECAPA-TDNN / VoxCeleb, many 3-second segments so each
pair gets a distribution), but the roles are swapped: Shawn is the target and Yancy
is the control speaker. A single similarity number means nothing, so every run
measures the same-person and different-people baselines on this same material.

  voiceprint-shawn.py [converted.wav]

The three Shawn sets are deliberately from different recording sessions, otherwise
"same person, different takes" just measures the same room and mic.
"""
import subprocess, sys, numpy as np, torch, warnings
warnings.filterwarnings('ignore')
import os
LEAD_REF = os.environ.get('LEAD_REF', 'stems/one-breath/0 Lead Vocals.mp3')
from speechbrain.inference.speaker import EncoderClassifier
from scipy import stats

CONV = sys.argv[1] if len(sys.argv) > 1 else 'rvc/out/shawn-lead-dry.wav'

enc = EncoderClassifier.from_hparams(source="speechbrain/spkrec-ecapa-voxceleb",
        savedir="tmp/ecapa", run_opts={"device": "cpu"})

def segs(path, ss, dur, n, hop):
    """n embeddings of dur seconds, stepping hop, skipping quiet windows"""
    out = []
    for i in range(n):
        t = ss + i*hop
        raw = subprocess.run(['ffmpeg','-v','error','-ss',str(t),'-t',str(dur),'-i',path,
            '-ac','1','-ar','16000','-f','s16le','-'], capture_output=True).stdout
        x = np.frombuffer(raw, np.int16).astype(np.float32)/32768.0
        if len(x) < 16000*dur*0.8: continue
        if 20*np.log10(np.sqrt((x**2).mean())+1e-9) < -40: continue
        e = enc.encode_batch(torch.from_numpy(x).unsqueeze(0)).squeeze().numpy()
        out.append(e/np.linalg.norm(e))
    return out

# Shawn-a/b/c are separate sessions: sh3 low range, sh5 high range, sh7 the new take.
# sh1/sh2 are excluded here for the same reason they are out of the training set.
SETS = {
 'Shawn-a' : ('svc/voice/wav/shawn/sh3.wav', 0, 3, 25, 4),
 'Shawn-b' : ('svc/voice/wav/shawn/sh5.wav', 0, 3, 25, 4),
 'Shawn-c' : ('svc/voice/wav/shawn/sh7.wav', 0, 3, 25, 3),
 'Yancy'   : ('svc/voice/wav/yancy/y1.wav',  0, 3, 25, 4),   # control speaker
 'Suno'    : (LEAD_REF,   100, 3, 30, 5),   # source singer
 '转换成品': (CONV,                         100, 3, 30, 5),
}
E = {k: segs(*v) for k, v in SETS.items()}
for k, v in E.items(): print(f'  {k:<10} {len(v)} 段')
if not E['转换成品']:
    sys.exit(f'\n  没有从 {CONV} 取到任何片段 — 文件缺失或全是静音')

def pair(a, b):
    s = [float(x@y) for x in E[a] for y in E[b] if not (a == b and x is y)]
    return np.mean(s), np.std(s)

print('\n  基准线')
for a, b, lbl in [('Shawn-a','Shawn-b','同一人 sh3/sh5'), ('Shawn-a','Shawn-c','同一人 sh3/sh7'),
                  ('Shawn-b','Shawn-c','同一人 sh5/sh7'), ('Shawn-a','Yancy','不同人 S/Yancy'),
                  ('Shawn-a','Suno','不同人 S/Suno'),     ('Yancy','Suno','不同人 Y/Suno')]:
    m, s = pair(a, b); print(f'    {lbl:<18} {m:+.3f} ± {s:.3f}')

print('\n  转换成品 vs')
for k in ['Shawn-a','Shawn-b','Shawn-c','Yancy','Suno']:
    m, s = pair('转换成品', k); print(f'    {k:<10} {m:+.3f} ± {s:.3f}')

def raw(a, b): return np.array([float(x@y) for x in E[a] for y in E[b]])
same = np.concatenate([raw('Shawn-a','Shawn-b'), raw('Shawn-a','Shawn-c'), raw('Shawn-b','Shawn-c')])
diff = np.concatenate([raw('Shawn-a','Yancy'), raw('Shawn-a','Suno'), raw('Yancy','Suno')])
conv_s = np.concatenate([raw('转换成品','Shawn-a'), raw('转换成品','Shawn-b'), raw('转换成品','Shawn-c')])
conv_y = raw('转换成品','Yancy')

print(f'\n  汇总')
print(f'    同一人基准        {same.mean():+.3f}   n={len(same)}')
print(f'    不同人基准        {diff.mean():+.3f}   n={len(diff)}')
print(f'    成品 vs Shawn     {conv_s.mean():+.3f}   n={len(conv_s)}')
print(f'    成品 vs Yancy     {conv_y.mean():+.3f}   n={len(conv_y)}   <- 对照,应落回"不同人"区间')

t, p = stats.ttest_ind(conv_s, conv_y, equal_var=False)
print(f'\n  成品更像 Shawn 还是 Yancy?  t={t:.1f}  p={p:.2e}')
t2, p2 = stats.ttest_ind(conv_s, same, equal_var=False)
print(f'  成品-Shawn 与 真同一人 有差别吗?  t={t2:.1f}  p={p2:.3f}')
pos = (conv_s.mean()-diff.mean())/(same.mean()-diff.mean())
print(f'\n  把"不同人"记作 0、"同一人"记作 1,成品落在  {pos:.2f}')
