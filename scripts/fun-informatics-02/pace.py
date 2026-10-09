"""Compare English take pacing with the owner-selected episode 1 v4 reference."""
import importlib.util
import json
import re
import statistics
import wave
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
for parent in ROOT.parents:
    if (parent / "lucas-academy-media").is_dir():
        MEDIA=parent/"lucas-academy-media";break
spec=importlib.util.spec_from_file_location("fi01_narration",ROOT/"scripts/fun-informatics-01/narration.py")
first=importlib.util.module_from_spec(spec);spec.loader.exec_module(first)

def metrics(lines,directory):
    ratios=[];seconds=0;words=0;by_id={}
    for line in lines:
        file=directory/(line["id"]+".wav")
        if not file.exists():continue
        with wave.open(str(file)) as w:duration=w.getnframes()/w.getframerate()
        count=len(re.findall(r"[a-zA-Z]+(?:'[a-zA-Z]+)?",first.plain(line["text"])))
        ratios.append(duration/count);seconds+=duration;words+=count
        by_id[line["id"]]={"seconds":round(duration,3),"words":count,"secondsPerWord":round(duration/count,3)}
    return {"takes":len(ratios),"medianSecondsPerWord":statistics.median(ratios),"wordsPerMinute":words*60/seconds,"totalSeconds":seconds,"words":words,"cues":by_id}

def main():
    en,_=first.parse(ROOT/"docs/fun-informatics-01/en-edit.md")
    reference=metrics([{"id":cid,"text":first.SPOKEN["en"].get(cid,cue["text"])} for cid,cue in en.items()],MEDIA/"outputs/louise/en/fun-informatics-01-v4")
    current=metrics(json.loads((ROOT/"public/fun-informatics-02/narration/en.json").read_text())["lines"],MEDIA/"outputs/louise/en/fun-informatics-02-v1")
    ratio=current["medianSecondsPerWord"]/reference["medianSecondsPerWord"]
    result={"reference":"fun-informatics-01.en / Louise v4","referenceMetrics":reference,"currentMetrics":current,"medianPaceRatio":ratio,"withinFifteenPercent":.85<=ratio<=1.15}
    (ROOT/"out/fun-informatics-02/pace.en.json").write_text(json.dumps(result,indent=2)+"\n")
    print(f"Reference {reference['wordsPerMinute']:.1f} wpm; current {current['wordsPerMinute']:.1f} wpm; median ratio {ratio:.3f} ({current['takes']}/84 takes)")
if __name__=="__main__":main()
