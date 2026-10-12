"""Sustained guide tones to sing against.

A pure sine is hard to match -- there is nothing to lock onto. These carry a few
harmonics, which is why an organ or a hummed note is easy to tune to.

    guide_tone.py                                   # the two song-specific runs
    guide_tone.py chromatic [low] [high] [hold] [passes] [out]

The chromatic run walks up one semitone at a time so a singer can record their
whole usable range in one take, for covers that are not yet chosen. It always
walks in small steps: jumping straight to a high target is what makes a singer
drop an octave without noticing (see VOICE-GUIDE.md).

Every C is preceded by a short high pip, so a singer ten minutes into a
featureless chromatic run still knows where they are.
"""
import sys
import numpy as np, soundfile as sf, subprocess, os
SR = 44100
NAMES=['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
def hz(n):   # 'F#4' -> Hz
    name, octv = n[:-1], int(n[-1]); s = NAMES.index(name) + 12*octv - 57
    return 440.0 * 2**(s/12)
def semi(n):
    name, octv = n[:-1], int(n[-1]); return NAMES.index(name) + 12*octv
def name_of(s): return f"{NAMES[s%12]}{s//12}"
def tone(f, dur):
    t = np.arange(int(SR*dur))/SR
    y = np.zeros_like(t)
    for k, a in [(1,1.0),(2,0.5),(3,0.28),(4,0.16),(5,0.08)]:
        y += a*np.sin(2*np.pi*f*k*t)
    y /= 2.05
    a, r = int(SR*0.04), int(SR*0.12)          # soft edges, no clicks
    y[:a] *= np.linspace(0,1,a); y[-r:] *= np.linspace(1,0,r)
    return y*0.5
def pip(f=1760.0, dur=0.07):
    t = np.arange(int(SR*dur))/SR
    y = 0.22*np.sin(2*np.pi*f*t)
    e = int(SR*0.008); y[:e]*=np.linspace(0,1,e); y[-e:]*=np.linspace(1,0,e)
    return y
def build(seq, passes, gap=0.6, between=1.6, out='x.wav'):
    parts=[]
    for p in range(passes):
        for n,d in seq:
            parts += [tone(hz(n), d), np.zeros(int(SR*gap))]
        parts.append(np.zeros(int(SR*between)))
    y = np.concatenate(parts)
    sf.write(out, y, SR)
    return len(y)/SR

def chromatic(low='E2', high='C6', hold=3.5, passes=3, out='svc/voice/guide-chromatic.mp3'):
    """Walk up chromatically, three passes: sing 'ah', then 'ee', then 'oo'."""
    lo, hi = semi(low), semi(high)
    notes = [name_of(s) for s in range(lo, hi+1)]
    gap, between = 0.8, 3.0
    parts=[]
    for p in range(passes):
        for n in notes:
            if n.startswith('C') and len(n)==2:        # octave landmark
                parts += [pip(), np.zeros(int(SR*0.12))]
            parts += [tone(hz(n), hold), np.zeros(int(SR*gap))]
        parts.append(np.zeros(int(SR*between)))
    y=np.concatenate(parts)
    wav = out if out.endswith('.wav') else out[:-4]+'.wav'
    sf.write(wav, y, SR)
    if out.endswith('.mp3'):
        subprocess.run(['ffmpeg','-v','error','-i',wav,'-b:a','192k','-y',out], check=True)
        os.remove(wav)
    per = passes*hold
    print(f'  {out}')
    print(f'    {notes[0]} -> {notes[-1]}   {len(notes)} semitones x {passes} passes'
          f'   {len(y)/SR/60:.1f} min   {per:.1f}s per semitone')
    return len(y)/SR

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'chromatic':
        a = sys.argv[2:]
        chromatic(a[0] if len(a)>0 else 'E2',
                  a[1] if len(a)>1 else 'C6',
                  float(a[2]) if len(a)>2 else 3.5,
                  int(a[3]) if len(a)>3 else 3,
                  a[4] if len(a)>4 else 'svc/voice/guide-chromatic.mp3')
    else:
        # Yancy: only F#4 and G4 are missing, so the run just walks up to them and sits there.
        HIGH = [('C4',3),('E4',3),('F#4',6),('G4',6),('F#4',4),('E4',3)]
        d1 = build(HIGH, 3, out='svc/voice/guide-high.wav')
        # Shawn: nothing above C#4 exists yet, so this covers the whole sung range.
        FULL = [('A3',3),('C4',3),('D4',5),('E4',4),('F#4',5),('G4',5),('E4',3),('C4',3)]
        d2 = build(FULL, 3, out='svc/voice/guide-full.wav')
        print(f'guide-high.wav  {d1:.1f}s   ' + ' '.join(f'{n}({hz(n):.0f}Hz)' for n,_ in HIGH))
        print(f'guide-full.wav  {d2:.1f}s   ' + ' '.join(f'{n}({hz(n):.0f}Hz)' for n,_ in FULL))
