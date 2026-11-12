"""Put the approved question over frame zero of the portrait story short."""
from pathlib import Path
from io import BytesIO
import hashlib,json,subprocess
from PIL import Image,ImageChops,ImageDraw,ImageFilter,ImageFont
from orbital_cover import save

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'out/family-ai-lab-02/orbital-v2/short'
DOC=ROOT/'docs/family-ai-lab-02/design-v2/short'
TITLES={'en':'Can 0 and 1 Talk?','zh':'0和1，能聊天吗？'}


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    verified=json.loads((DOC/'verification.json').read_text());movie=ROOT/verified['movie'];assert sha(movie)==verified['sha256']
    folder=OUT/'cover';folder.mkdir(exist_ok=True)
    raw=subprocess.check_output(['ffmpeg','-v','error','-i',str(movie),'-frames:v','1','-f','image2pipe','-vcodec','png','-'])
    base=Image.open(BytesIO(raw)).convert('RGB');assert base.size==(1080,1920)
    save(base,folder/'first-frame.png')
    rows={'en':[('Can 0 and 1',118,180),('Talk?',228,350)],'zh':[('0和1，',176,170),('能聊天吗？',154,385)]}
    report={'sourceMovie':str(movie.relative_to(ROOT)),'sourceMovieSha256':sha(movie),'sourceFrame':0,'sourceFrameSha256':sha(folder/'first-frame.png'),'sourceSize':list(base.size),'outputSize':list(base.size),'titles':TITLES,'composition':'Full portrait frame zero with text in its upper open space; no crop, repositioning, ribbon, byline or source label. Hands, paper and pipe remain unchanged.','covers':{}}
    for lang,lines in rows.items():
        fonts='/System/Library/Fonts/Supplemental/Arial Black.ttf' if lang=='en' else '/System/Library/Fonts/Hiragino Sans GB.ttc';index=0 if lang=='en' else 2
        layer=Image.new('RGBA',base.size);shadow=Image.new('RGBA',base.size);draw=ImageDraw.Draw(layer);shade=ImageDraw.Draw(shadow)
        for i,(text,size,top) in enumerate(lines):
            font=ImageFont.truetype(fonts,size,index=index)
            while draw.textbbox((0,0),text,font=font)[2]>920:
                size-=1;font=ImageFont.truetype(fonts,size,index=index)
            box=draw.textbbox((0,0),text,font=font);xy=(80-box[0],top-box[1])
            shade.text((xy[0]+3,xy[1]+5),text,font=font,fill=(0,0,0,235),stroke_width=7,stroke_fill=(0,0,0,235))
            draw.text(xy,text,font=font,fill=(255,248,232,255) if i==0 else (255,197,88,255),stroke_width=2,stroke_fill=(9,19,27,255))
        result=Image.alpha_composite(base.convert('RGBA'),shadow.filter(ImageFilter.GaussianBlur(6)))
        result=Image.alpha_composite(result,layer).convert('RGB');bounds=ImageChops.difference(base,result).getbbox()
        assert bounds and bounds[0]>40 and bounds[1]>120 and bounds[2]<1040 and bounds[3]<590,bounds
        assert ImageChops.difference(base.crop((0,600,1080,1920)),result.crop((0,600,1080,1920))).getbbox() is None
        path=folder/f'family-ai-lab-02.short.{lang}.png';save(result,path);assert path.stat().st_size<2_000_000
        report['covers'][lang]={'file':str(path.relative_to(ROOT)),'sha256':sha(path),'bytes':path.stat().st_size,'titlePixelBounds':list(bounds),'font':fonts,'fontIndex':index,'unchangedOutsideTitle':True}
    (DOC/'cover.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
