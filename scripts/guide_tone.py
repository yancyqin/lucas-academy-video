"""Sustained guide tones to sing against.

A pure sine is hard to match -- there is nothing to lock onto. These carry a few
harmonics, which is why an organ or a hummed note is easy to tune to.
"""
import numpy as np, soundfile as sf, math
SR = 44100
NAMES=['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
def hz(n):   # 'F#4' -> Hz
    name, octv = n[:-1], int(n[-1]); s = NAMES.index(name) + 12*octv - 57
    return 440.0 * 2**(s/12)
def tone(f, dur):
    t = np.arange(int(SR*dur))/SR
    y = np.zeros_like(t)
    for k, a in [(1,1.0),(2,0.5),(3,0.28),(4,0.16),(5,0.08)]:
        y += a*np.sin(2*np.pi*f*k*t)
    y /= 2.05
    a, r = int(SR*0.04), int(SR*0.12)          # soft edges, no clicks
    y[:a] *= np.linspace(0,1,a); y[-r:] *= np.linspace(1,0,r)
    return y*0.5
def build(seq, passes, gap=0.6, between=1.6, out='x.wav'):
    parts=[]
    for p in range(passes):
        for n,d in seq:
            parts += [tone(hz(n), d), np.zeros(int(SR*gap))]
        parts.append(np.zeros(int(SR*between)))
    y = np.concatenate(parts)
    sf.write(out, y, SR)
    return len(y)/SR

# Yancy: only F#4 and G4 are missing, so the run just walks up to them and sits there.
HIGH = [('C4',3),('E4',3),('F#4',6),('G4',6),('F#4',4),('E4',3)]
d1 = build(HIGH, 3, out='svc/voice/guide-high.wav')
# Shawn: nothing above C#4 exists yet, so this covers the whole sung range.
FULL = [('A3',3),('C4',3),('D4',5),('E4',4),('F#4',5),('G4',5),('E4',3),('C4',3)]
d2 = build(FULL, 3, out='svc/voice/guide-full.wav')
print(f'guide-high.wav  {d1:.1f}s   ' + ' '.join(f'{n}({hz(n):.0f}Hz)' for n,_ in HIGH))
print(f'guide-full.wav  {d2:.1f}s   ' + ' '.join(f'{n}({hz(n):.0f}Hz)' for n,_ in FULL))
