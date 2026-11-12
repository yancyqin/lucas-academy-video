"""Mix selected, checked bilingual takes to their common native-portrait timeline."""
import argparse
import json
import math
import subprocess
import numpy as np
import soundfile as sf
from common import ROOT,PUBLIC,DOCS,OUT,SOURCE,sha,module


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--film');args=parser.parse_args()
    normalize=module('family_loudnorm',ROOT/'scripts/family-ai-lab-01/mix_audio.py').loudnorm
    choices=json.loads((DOCS/'voice-choices.json').read_text())
    for film in SOURCE['films']:
        if args.film and film!=args.film:continue
        timeline=json.loads((PUBLIC/f'timeline.{film}.json').read_text());assert timeline['narrated']
        folder=OUT/film/'audio';folder.mkdir(parents=True,exist_ok=True)
        samples=math.ceil(timeline['durationInFrames']/timeline['fps']*24000);measurements={}
        for lang in ('en','zh'):
            output=np.zeros(samples,dtype=np.float32)
            for line in timeline['lines']:
                assert choices[f'{lang}/{line["id"]}']['checked']
                meta=timeline['voices'][lang][line['id']];path=PUBLIC/meta['path'];assert sha(path)==meta['sha256']
                speech,rate=sf.read(path,dtype='float32');assert rate==24000 and speech.ndim==1
                start=round((line['from']/timeline['fps']+.1)*rate)
                end=round((line['from']+line['duration'])/timeline['fps']*rate)
                assert start+len(speech)<=end,(lang,line['id'])
                output[start:start+len(speech)]+=speech
            dry=folder/f'{lang}.dry.wav';sf.write(dry,output,24000,subtype='PCM_24')
            measurements[lang]=normalize(dry,folder/f'{lang}.wav')
            print('Mixed',film,lang,len(output)/24000,'seconds',flush=True)
        (folder/'loudness.json').write_text(json.dumps(measurements,indent=2)+'\n')


if __name__=='__main__':main()
