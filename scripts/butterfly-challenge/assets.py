"""Put the film's pictures where Remotion can read them: public/butterfly-challenge/ (git-ignored).

  python3 scripts/butterfly-challenge/assets.py

- pairs/NN-A.jpg, NN-B.jpg: copied byte for byte from the data folder's pairs/, i.e. exactly what both models saw
  (blind_test.py; never re-run `pairs` for the film).
- clips/<key>.mp4: each real video, 1920x1080 H.264 at its own frame rate, no sound (the film's sound is the
  narration and the music bed). g1 is a VP8 webm, p44 and p67 are 4K, p15 and p69 are 1440p.
- clips/<key>.last.jpg: the frame at the end of the clip's usable stretch (USABLE), for a held, slowly pushed-in
  ending when the narration runs longer than the clip.
Existing outputs are kept; delete one to make it again.
"""
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = next(p / "lucas-academy-video-data/butterfly-challenge" for p in ROOT.parents
            if (p / "lucas-academy-video-data").is_dir())
PUB = ROOT / "public/butterfly-challenge"

# usable stretch of each clip, seconds, checked on frames 2026-11-12: g1 goes out of focus from 14.5 s, p08's
# butterfly is leaving the frame by 7 s (6.5 s still has it whole), p69's is gone at 6 s (5.5 s still has it)
USABLE = {"g1-greta-oto-commons": (0.0, 14.0), "p08-2901459": (0.0, 6.5), "p15-5129671": (0.0, 17.6),
          "p16-5241558": (0.0, 5.9), "p17-7855586": (0.0, 33.5), "p18-8450772": (0.0, 9.1),
          "p26-16001770": (0.0, 30.0), "p44-38657643": (0.0, 22.9), "p67-36683557": (0.0, 18.6),
          "p69-37672883": (0.0, 5.5),
          # pair 6's second clip, a male Common Blue with its wings open (Yancy 11-12: 「眼灰蝶 找一找展开视频看看」 → OK'd):
          # Commons, NaIzletuSi, CC BY 3.0, 4K 23.976 fps
          "c06-polyommatus-icarus-open-commons": (0.0, 45.5)}


def main():
    (PUB / "pairs").mkdir(parents=True, exist_ok=True)
    (PUB / "clips").mkdir(parents=True, exist_ok=True)
    for src in sorted((DATA / "pairs").glob("*.jpg")):
        dst = PUB / "pairs" / src.name
        if not dst.exists() or dst.read_bytes() != src.read_bytes():
            shutil.copyfile(src, dst)
    for key, (_, out) in USABLE.items():
        src = next((DATA / "footage").glob(f"{key}.*"))
        mp4 = PUB / "clips" / f"{key}.mp4"
        if not mp4.exists():
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-an",
                            "-vf", "scale=1920:1080:flags=lanczos,format=yuv420p", "-c:v", "libx264", "-preset", "slow",
                            "-crf", "16", "-movflags", "+faststart", str(mp4)], check=True)
            print("clip", mp4.name, flush=True)
        last = PUB / "clips" / f"{key}.last.jpg"
        if not last.exists():
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{max(0.0, out - 0.05):.3f}", "-i", str(mp4),
                            "-frames:v", "1", "-q:v", "2", str(last)], check=True)
    print("assets in", PUB)


if __name__ == "__main__":
    main()
