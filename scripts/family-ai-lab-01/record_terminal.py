"""Record a native Terminal window viewing ORIGINAL saved JSON; no model calls."""
from pathlib import Path
import json
import subprocess

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "public/family-ai-lab-01/capture"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    command = f"cd '{ROOT}' && python3 scripts/family-ai-lab-01/show_results.py"
    # JSON string literals also safely quote this fixed-path AppleScript argument.
    script = f'''tell application "Terminal"
 set t to do script {json.dumps(command)}
 set current settings of t to settings set "Pro"
 set font size of t to 22
 set number of columns of t to 100
 set number of rows of t to 22
 set custom title of t to "Family AI Lab — Original experiment records"
 set bounds of front window to {{30, 80, 1510, 980}}
 activate
 return id of front window
end tell'''
    window = subprocess.check_output(["osascript", "-e", script], text=True).strip()
    # Wait only for the viewer script's four printed lines, never for a benchmark.
    import time
    time.sleep(2)
    subprocess.run(["screencapture", "-x", "-o", "-l", window, str(OUT / "terminal.png")], check=True)
    subprocess.run(["screencapture", "-x", "-v", "-V", "3", "-l", window, str(OUT / "terminal.mov")], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(OUT / "terminal.mov"), "-an", "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-r", "30", str(OUT / "terminal.mp4")], check=True)
    for source, dest in [("terminal.png", "terminal-view.png"), ("terminal.mp4", "terminal-view.mp4")]:
        dims = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "json", str(OUT / source)]))["streams"][0]
        y = int(dims["height"] * .035) // 2 * 2
        h = int(dims["height"] * .425) // 2 * 2
        extra = ["-frames:v", "1"] if source.endswith("png") else ["-an", "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p"]
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(OUT / source), "-vf", f"crop={dims['width']}:{h}:0:{y}", *extra, str(OUT / dest)], check=True)
    print("Recorded native Terminal; original result viewer only:", OUT / "terminal-view.mp4")


if __name__ == "__main__":
    main()
