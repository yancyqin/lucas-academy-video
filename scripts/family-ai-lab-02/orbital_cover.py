"""Compose the approved question over the exact first frame of the film."""
from pathlib import Path
from io import BytesIO
import hashlib,json,subprocess
from PIL import Image,ImageChops,ImageDraw,ImageFilter,ImageFont

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'out/family-ai-lab-02/orbital-v2'
DOC=ROOT/'docs/family-ai-lab-02/design-v2'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def save(image,path):
    data=BytesIO();image.save(data,format='PNG',optimize=True)
    if not path.exists() or path.read_bytes()!=data.getvalue():path.write_bytes(data.getvalue())


def main():
    movie=OUT/'delivery/family-ai-lab-02.bilingual.mp4';folder=OUT/'cover';folder.mkdir(parents=True,exist_ok=True)
    # No seeking: ffmpeg decodes video frame zero. The whole composition is
    # retained; only a uniform 1920x1080 -> 1280x720 resize is applied.
    raw=subprocess.check_output(['ffmpeg','-v','error','-i',str(movie),'-frames:v','1','-f','image2pipe','-vcodec','png','-'])
    frame=Image.open(BytesIO(raw)).convert('RGB');assert frame.size==(1920,1080)
    save(frame,folder/'first-frame.png');base=frame.resize((1280,720),Image.Resampling.LANCZOS)
    script=json.loads((Path(__file__).parent/'orbital-script.json').read_text())
    assert script['workingTitle']=={'zh':'0和1，能聊天吗？','en':'Can 0 and 1 Talk?'}
    rows={'en':[('Can 0 and 1',68,60),('Talk?',116,150)],'zh':[('0和1，',88,57),('能聊天吗？',84,170)]}
    report={'sourceMovie':str(movie.relative_to(ROOT)),'sourceMovieSha256':sha(movie),'sourceFrame':0,'sourceFrameSha256':sha(folder/'first-frame.png'),'sourceSize':list(frame.size),'outputSize':[1280,720],'composition':'Full original frame, unchanged outside title; no crop, repositioning, retouching, ribbon or byline.','titles':script['workingTitle'],'covers':{}}
    for lang,lines in rows.items():
        fonts='/System/Library/Fonts/Supplemental/Arial Black.ttf' if lang=='en' else '/System/Library/Fonts/Hiragino Sans GB.ttc'
        font_index=0 if lang=='en' else 2
        layer=Image.new('RGBA',base.size);shadow=Image.new('RGBA',base.size);d=ImageDraw.Draw(layer);s=ImageDraw.Draw(shadow)
        for i,(text,size,top) in enumerate(lines):
            font=ImageFont.truetype(fonts,size,index=font_index);box=d.textbbox((0,0),text,font=font);position=(1225-box[2],top-box[1])
            s.text((position[0]+2,position[1]+4),text,font=font,fill=(0,0,0,240),stroke_width=6,stroke_fill=(0,0,0,240))
            d.text(position,text,font=font,fill=(255,248,232,255) if i==0 else (255,197,88,255),stroke_width=2,stroke_fill=(9,19,27,255))
        result=Image.alpha_composite(base.convert('RGBA'),shadow.filter(ImageFilter.GaussianBlur(5)))
        result=Image.alpha_composite(result,layer).convert('RGB');bounds=ImageChops.difference(base,result).getbbox()
        assert bounds and bounds[0]>750 and bounds[1]>20 and bounds[2]<1270 and bounds[3]<310,bounds
        path=folder/f'family-ai-lab-02.{lang}.png';save(result,path);assert path.stat().st_size<2_000_000
        report['covers'][lang]={'file':str(path.relative_to(ROOT)),'sha256':sha(path),'bytes':path.stat().st_size,'titlePixelBounds':list(bounds),'font':fonts,'fontIndex':font_index,'unchangedOutsideTitle':True}
    (DOC/'cover.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
