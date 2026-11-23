import os
import sys
from pathlib import Path

here=Path(__file__).resolve().parent
media=here.parents[3]/'lucas-academy-media'
name,profile,speed,threads,*extra=sys.argv[1:]
os.chdir(media)
sys.path.insert(0,str(media/'src'))
os.environ['TOKENIZERS_PARALLELISM']='false'
import torch
torch.set_num_threads(int(threads))
torch.set_num_interop_threads(1)
from lucas_media.narrate import main
sys.argv=['lucas-narrate',str(here/'voices'/f'{name}.json'),'--profile',profile,
          '--language','en','--speed',speed,'--output-dir',str(here/'voices'/name),*extra]
main()
