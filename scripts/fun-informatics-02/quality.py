"""Delivery checks: full Chinese narration, captions, codec, black frames and audio."""
import hashlib
import json
import math
import re
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
PUB=ROOT / "public/fun-informatics-02"
OUT=ROOT / "out/fun-informatics-02"
DELIVERY=OUT / "delivery"


def main():
    tl=json.loads((PUB / "timeline.zh.json").read_text())
    if tl["draft"]: raise SystemExit("Draft timeline is not deliverable")
    assert len(tl["cues"])==84 and tl["cues"][-1]["id"]=="cl07-01"
    film=DELIVERY / "fun-informatics-02.zh.mp4"
    probe=json.loads(subprocess.check_output(["ffprobe","-v","error","-show_streams","-show_format","-of","json",str(film)]))
    video=next(s for s in probe["streams"] if s["codec_type"]=="video")
    audio=next(s for s in probe["streams"] if s["codec_type"]=="audio")
    assert (video["width"],video["height"],video["r_frame_rate"],video["codec_name"])==(1920,1080,"30/1","h264")
    expected_frames=math.ceil(tl["durationSeconds"]*tl["fps"])
    assert int(video["nb_frames"])==expected_frames,(video["nb_frames"],expected_frames)
    assert audio["codec_name"]=="aac" and audio["channels"]==2
    duration=float(probe["format"]["duration"])
    assert abs(duration-tl["durationSeconds"])<.15
    counts={}
    for language in ["zh-Hans","en"]:
        caption=DELIVERY / f"fun-informatics-02.zh.{language}.srt"
        blocks=caption.read_text().strip().split("\n\n")
        previous=-1
        for number,block in enumerate(blocks,1):
            lines=block.splitlines();assert int(lines[0])==number
            times=re.findall(r"(\d+):(\d+):(\d+),(\d+)",lines[1]);assert len(times)==2
            a,b=[int(h)*3600+int(m)*60+int(s)+int(ms)/1000 for h,m,s,ms in times]
            assert 0<=a<b<=tl["endCardStart"] and a>=previous-.002, (caption,number,a,b,previous)
            assert 1<=len(lines[2:])<=2 and max(map(len,lines[2:]))<=42
            assert "<strong>" not in block
            previous=b
        counts[language]=len(blocks)
    print("Codec, duration and both external caption files passed",flush=True)
    stats=OUT / "blackframe-statistics.txt"
    subprocess.run(["ffmpeg","-v","error","-y","-i",str(film),"-an","-vf",f"signalstats,metadata=print:file={stats}","-f","null","-"],check=True)
    maxima=[float(line.split('=',1)[1]) for line in stats.read_text().splitlines() if line.startswith("lavfi.signalstats.YMAX=")]
    assert len(maxima)==expected_frames,(len(maxima),expected_frames)
    # H.264 limited-range black is Y=16. Retain the project's YMAX<12
    # check and also catch that ordinary encoded black with a small margin.
    superblack=sum(v<12 for v in maxima)
    black=sum(v<=18 for v in maxima)
    assert maxima and black==0,f"{black} black frames"
    print(f"Black-frame scan: {len(maxima)} frames, {black} black",flush=True)
    loud=subprocess.run(["ffmpeg","-hide_banner","-nostats","-i",str(film),"-vn","-af","ebur128=peak=sample+true:framelog=quiet","-f","null","-"],capture_output=True,text=True,check=True).stderr
    (OUT / "loudness.txt").write_text(loud)
    lufs=float(re.findall(r"I:\s+(-?[\d.]+) LUFS",loud)[-1]);peak=float(re.findall(r"Peak:\s+(-?[\d.]+) dBFS",loud)[-1])
    assert abs(lufs+16)<=.5 and peak<=-1.5,(lufs,peak)
    report={"language":"zh","englishNarration":"on hold; not generated","approvedCues":84,"duration":duration,"resolution":[1920,1080],"fps":30,"captionBlocks":counts,"blackFrames":black,"projectYMAXBelow12":superblack,"encodedBlackThresholdYMAX":18,"scannedFrames":len(maxima),"integratedLUFS":lufs,"truePeakDBTP":peak,"sha256":hashlib.sha256(film.read_bytes()).hexdigest(),"bytes":film.stat().st_size}
    (OUT / "delivery-check.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    print(f"Final encoded film: {lufs} LUFS, {peak} dBTP; passed",flush=True)


if __name__=="__main__":main()
