"""Preserve all native cropped Sweet Home frames without a second video decoder."""
import json, subprocess
from pathlib import Path
ROOT=Path('/Users/yqin/repo/playground/lucas-academy-video-data/curiosity-builds-20261118/v10')
source=ROOT/'captures/sweet-home-v3-model-only.mp4'
output=ROOT/'captures/sweet-home-model-frames';output.mkdir(exist_ok=True)
subprocess.run(['ffmpeg','-y','-v','error','-i',str(source),'-q:v','2',str(output/'frame-%03d.jpg')],check=True)
assert len(list(output.glob('frame-*.jpg')))==105
(ROOT/'records/house-model-frames.json').write_text(json.dumps({'source':str(source),'native_source_frames':105,'output_intro_frames':[96,216],'output_process_frames':120,'source_playback_rate':.875,'image_sequence_count':105,'same_fixed_right_hand_picture':True},indent=2)+'\n')
