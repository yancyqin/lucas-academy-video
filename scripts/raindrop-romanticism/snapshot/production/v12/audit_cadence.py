"""Measure decoded motion cadence, rather than merely checking MP4 timestamps."""
import json,subprocess
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parent
SOURCE=P.parent/'v11/delivery/01-English-full.mp4'
samples=[('opening',15,10),('history-walk',302,10),('goya-approach',343,8),('wright-walk',524,9),('nature-walk',586,9),('return-walk',774,10)]
rows=[]
for label,start,seconds in samples:
    raw=subprocess.check_output(['/opt/homebrew/bin/ffmpeg','-v','error','-ss',str(start),'-i',str(SOURCE),'-t',str(seconds),'-an','-vf','scale=320:180,format=gray','-f','rawvideo','-'])
    data=np.frombuffer(raw,np.uint8).reshape(-1,180,320)
    dif=np.mean(np.abs(np.diff(data.astype(np.int16),axis=0)),axis=(1,2))
    quiet=dif<.03
    moving=dif>.15
    row=dict(label=label,start=start,seconds=seconds,frames=len(data),nearly_identical_pairs=int(quiet.sum()),
        nearly_identical_fraction=float(quiet.mean()),motion_pairs=int(moving.sum()),
        mean_frame_difference=float(dif.mean()),quantiles=np.quantile(dif,[0,.1,.25,.5,.75,.9,1]).tolist())
    rows.append(row);print(json.dumps(row),flush=True)
(P/'old-cadence-audit.json').write_text(json.dumps(dict(source=str(SOURCE),items=rows),indent=2))
