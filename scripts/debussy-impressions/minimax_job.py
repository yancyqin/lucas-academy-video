#!/usr/bin/env python3
"""MiniMax Hailuo-02 image-to-video jobs for the Debussy film (rules: MINIMAX-VIDEO-EXPERIENCE.md).

  prepare ID --res 768P|1080P --dur 6|10 (--action "动作" | --prompt "整句") [--last-same]
                                                          new run dir DATA/minimax/ID/vN with first.jpg,
                                                          prompt.txt, request-metadata.json (no key, no base64)
  submit RUNDIR [--again]   POST once; refuses if the run already has submission.json (--again only resends a
                     run that was rejected with no task id, e.g. quota 2067); saves base_resp + task_id
  poll RUNDIR [--wait]   GET the task status (every 30 s with --wait, until Success/Fail); on Success fetch
                     the download URL and save original.mp4 (via .part, checked with ffprobe), write probe.json
The API key is read from ~/.netrc (machine api.minimaxi.com) into the request header only; never printed or saved.
"""
import argparse, base64, hashlib, json, netrc, os, pathlib, ssl, subprocess, sys, time, urllib.request
from PIL import Image

DATA = pathlib.Path("/Users/yqin/repo/playground/lucas-academy-video-data/debussy-impressions")
BASE = "https://api.minimax.cn"
MODEL = "MiniMax-Hailuo-02"
CTX = ssl.create_default_context(cafile="/etc/ssl/cert.pem")
TEMPLATE = "[固定] 固定镜头，保持这幅油画的笔触、颜色和构图不变，像画布上的颜料在慢慢流动。{action}。人物和建筑保持不动。连续单镜头，不切镜。"

def key():
    e = netrc.netrc(str(pathlib.Path.home() / ".netrc")).authenticators("api.minimaxi.com")
    if not e or not e[2]: sys.exit("MiniMax API key missing in ~/.netrc (machine api.minimaxi.com)")
    return e[2]

def call(method, path, body=None, timeout=60):
    req = urllib.request.Request(BASE + path, method=method, data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Authorization": "Bearer " + key(), "Content-Type": "application/json"})
    with urllib.request.urlopen(req, context=CTX, timeout=timeout) as r:
        return json.loads(r.read().decode())

def now(): return time.strftime("%Y-%m-%dT%H:%M:%S%z")

def prepare(a):
    root = DATA / "minimax" / a.id; root.mkdir(parents=True, exist_ok=True)
    n = 1 + max([int(p.name[1:]) for p in root.glob("v*") if p.name[1:].isdigit()] or [0]); run = root / f"v{n}"; run.mkdir()
    src = pathlib.Path(a.image) if a.image else DATA / "art" / f"{a.id}.jpg"      # a painting, or any prepared image
    im = Image.open(src).convert("RGB")
    if max(im.size) > 2048: im.thumbnail((2048, 2048), Image.LANCZOS)
    im.save(run / "first.jpg", quality=93)
    prompt = a.prompt if a.prompt else TEMPLATE.format(action=a.action.rstrip("。"))
    (run / "prompt.txt").write_text(prompt + "\n")
    meta = {"id": a.id, "model": MODEL, "resolution": a.res, "duration": a.dur, "prompt_optimizer": False,
            "first_frame": str(run / "first.jpg"), "first_frame_size": list(im.size), "first_frame_sha256": hashlib.sha256((run / "first.jpg").read_bytes()).hexdigest(),
            "source_image": str(src), "prompt": prompt, "prepared": now(),
            "last_frame": str(run / "first.jpg") if a.last_same else None}
    (run / "request-metadata.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1))
    print(run)

def submit(a):
    run = pathlib.Path(a.run)
    if (run / "submission.json").exists():
        prev = json.loads((run / "submission.json").read_text())
        if not (a.again and prev.get("state") == "rejected" and not prev.get("task_id")):
            sys.exit(f"{run} was already submitted ({prev.get('state')}) — not sending again"
                     + ("" if prev.get("task_id") else "; a quota rejection with no task can be resent with --again"))
        (run / f"submission-rejected-{prev.get('at', 'earlier').replace(':', '')}.json").write_text(json.dumps(prev, ensure_ascii=False, indent=1))
    meta = json.loads((run / "request-metadata.json").read_text())
    (run / "submission.json").write_text(json.dumps({"state": "sending", "at": now()}))     # guard against double sends
    img = "data:image/jpeg;base64," + base64.b64encode((run / "first.jpg").read_bytes()).decode("ascii")
    body = {"model": meta["model"], "duration": meta["duration"], "resolution": meta["resolution"], "prompt_optimizer": False,
            "prompt": meta["prompt"], "first_frame_image": img}
    if meta.get("last_frame"):                                          # first/last-frame mode; same painting at both ends
        body["last_frame_image"] = "data:image/jpeg;base64," + base64.b64encode(pathlib.Path(meta["last_frame"]).read_bytes()).decode("ascii")
    try:
        r = call("POST", "/v1/video_generation", body, timeout=120)
    except Exception as e:
        (run / "submission.json").write_text(json.dumps({"state": "unknown", "error": str(e)[:300], "at": now()}, ensure_ascii=False))
        sys.exit(f"POST failed or timed out ({e}); NOT retrying — check the platform before resubmitting")
    ok = r.get("base_resp", {}).get("status_code") == 0 and r.get("task_id")
    (run / "submission.json").write_text(json.dumps({"state": "created" if ok else "rejected", "task_id": r.get("task_id"), "base_resp": r.get("base_resp"), "at": now()}, ensure_ascii=False, indent=1))
    print(run.parent.name, run.name, "task created" if ok else "REJECTED", r.get("task_id") or "", r.get("base_resp"))

def poll(a):
    run = pathlib.Path(a.run); sub = json.loads((run / "submission.json").read_text())
    if not sub.get("task_id"): sys.exit(f"{run}: no task id ({sub.get('state')})")
    while True:
        r = call("GET", f"/v1/query/video_generation?task_id={sub['task_id']}")
        (run / "status.json").write_text(json.dumps({**r, "checked": now()}, ensure_ascii=False, indent=1))
        st = r.get("status")
        if st in ("Success", "Fail") or not a.wait: break
        time.sleep(30)
    print(run.parent.name, run.name, st, r.get("file_id") or "", r.get("base_resp", {}).get("status_msg", ""))
    if st == "Success" and not (run / "original.mp4").exists():
        f = call("GET", f"/v1/files/retrieve?file_id={r['file_id']}")
        url = f["file"]["download_url"]; part = run / "original.mp4.part"
        with urllib.request.urlopen(urllib.request.Request(url), context=CTX, timeout=300) as resp, open(part, "wb") as out:
            out.write(resp.read())
        pr = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height,codec_name,r_frame_rate,nb_frames:format=duration,size", "-of", "json", str(part)], capture_output=True, text=True)
        if pr.returncode != 0: sys.exit(f"downloaded file does not decode: {pr.stderr[:200]}")
        part.rename(run / "original.mp4"); (run / "probe.json").write_text(pr.stdout)
        j = json.loads(pr.stdout); s = j["streams"][0]
        print("  saved original.mp4", s["width"], "x", s["height"], s["r_frame_rate"], "fps", j["format"]["duration"], "s")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("prepare"); p.add_argument("id"); p.add_argument("--res", default="1080P"); p.add_argument("--dur", type=int, default=6); p.add_argument("--action", default=""); p.add_argument("--prompt", default=""); p.add_argument("--last-same", action="store_true", help="also send the painting as last_frame_image"); p.add_argument("--image", help="first frame from this file instead of DATA/art/ID.jpg")
    s = sp.add_parser("submit"); s.add_argument("run"); s.add_argument("--again", action="store_true", help="resend a run that was rejected without a task id (e.g. quota 2067)")
    q = sp.add_parser("poll"); q.add_argument("run"); q.add_argument("--wait", action="store_true")
    a = ap.parse_args(); {"prepare": prepare, "submit": submit, "poll": poll}[a.cmd](a)
