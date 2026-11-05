"""Owner-requested QR and tighter terminal crop, preserving native originals."""
from pathlib import Path
import hashlib
import json
import subprocess
import qrcode

ROOT=Path(__file__).resolve().parents[2]
PUBLIC=ROOT/'public/family-ai-lab-01'


def main():
    qr=qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M,box_size=12,border=4)
    qr.add_data('https://ai.lucasacademy.org/');qr.make(fit=True)
    qr.make_image(fill_color='#103e42',back_color='white').save(PUBLIC/'art/ai-lab-qr.png')
    crop=PUBLIC/'capture'
    # The native recording's prompt line begins below 38% of the window height.
    # Keep the original result rows and their source line, exclude the shell prompt.
    for src,dest in [('terminal.png','terminal-view.png'),('terminal.mp4','terminal-view.mp4')]:
        d=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=width,height','-of','json',str(crop/src)]))['streams'][0]
        y=int(d['height']*.035)//2*2
        h=int(d['height']*.34)//2*2
        opt=['-frames:v','1'] if src.endswith('png') else ['-an','-c:v','libx264','-crf','18','-pix_fmt','yuv420p']
        subprocess.run(['ffmpeg','-v','error','-y','-i',str(crop/src),'-vf',f'crop={d["width"]}:{h}:0:{y}',*opt,str(crop/dest)],check=True)
    model=json.loads((PUBLIC/'trained-model.json').read_text())
    tiles=[{'d':' '.join(f'M{i%20},{i//20}h1v1h-1z' for i,v in enumerate(e['pic']) if v),'yes':e['yes']} for e in model['examples']]
    (PUBLIC/'training-tiles.json').write_text(json.dumps(tiles,separators=(',',':')))
    record=ROOT/'docs/family-ai-lab-01/footage-sources.json'
    sources=json.loads(record.read_text())
    additions=[('art/ai-lab-qr.png','Authored QR · https://ai.lucasacademy.org/'),
               ('training-tiles.json','Authored paths from the 419 actual training pictures')]
    known={row['path'] for row in sources['assets']}
    for name,credit in additions:
        name=str((PUBLIC/name).relative_to(ROOT))
        if name not in known:sources['assets'].append({'path':name,'credit':credit})
    for row in sources['assets']:
        p=ROOT/row['path'];row['sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
        if 'probe' in row:
            row['probe']=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','stream=codec_type,width,height,r_frame_rate:format=duration','-of','json',str(p)]))
    sources.pop('allVideoMutedInReview',None)
    sources['allSourceVideoMuted']=True
    record.write_text(json.dumps(sources,ensure_ascii=False,indent=2)+'\n')
    print('QR ready; shell prompt excluded; actual training sprites:',len(tiles))


if __name__=='__main__':main()
