#!/usr/bin/env python3
"""Warp (a segment of) a Muse clip into its painting's frame, so clip and painting dissolve into each other without a
jump (owner 2026-11-02: 「codex 生成仿古图，muse 做，和油画切换」).

The transform is found on the segment's FIRST frame, then applied to every frame of the segment:
  --to photo     (default) the first frame is (nearly) the Codex reconstruction Muse started from: refine clip -> photo
                 with ECC (affine, both are photographs) and compose with the photo -> painting transform align.py found
                 (real/aligned/report.json "A")
  --to painting  the segment starts after a cut inside the clip (owner 11-03: the dance-class clip changes at ~1 s —
                 「拆成两段，不要一起用」), so register its first frame straight onto the painting with align.py's search
Uncovered edges are mirrored (the film crops a 16:9 window inside the painting, so they rarely show).

  --ref F        the segment starts after a change inside the clip but the room stayed put: register its first frame
                 onto frame F of the same clip (ECC) and compose with frame F's own transform

usage: .venv-reframe/bin/python align_video.py ID CLIP [--start F] [--end F] [--to photo|painting] [--ref F] [--out OUT.mp4]
       frames are clip frame numbers, end exclusive; default OUT footage/muse/aligned/<id>[-from<F>].mp4
"""
import argparse, glob, json, os, subprocess, sys
import cv2
import numpy as np

DATA = os.environ.get("BLUE_WAVE_DATA", "/Users/yqin/repo/playground/lucas-academy-video-data/blue-wave")
os.environ.setdefault("ALIGN_DATA", DATA)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "debussy-impressions"))
import align as AL                                   # structure(), ecc(), sift_init(), template_init(), score(), decompose()
LAST_SCORES = {}

def probe(clip):
    m = json.loads(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height,r_frame_rate,nb_frames",
                                   "-of", "json", clip], capture_output=True, text=True, check=True).stdout)["streams"][0]
    return m["width"], m["height"], m["r_frame_rate"], int(m["nb_frames"])

def stream(clip, w, h, start=0, end=None):
    """Frames start..end-1, one at a time (a sharpened clip is ~23 MB a frame — never hold all 240)."""
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", clip, "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL)          # stopped early on purpose: no broken-pipe noise
    i = 0
    while end is None or i < end:
        b = p.stdout.read(w * h * 3)
        if len(b) < w * h * 3: break
        if i >= start: yield np.frombuffer(b, np.uint8).reshape(h, w, 3)
        i += 1
    p.stdout.close(); p.terminate(); p.wait()

def frame_at(clip, w, h, n):
    return next(stream(clip, w, h, n, n + 1))

def to_photo(frame, rep):
    """clip px -> aligned-output px: ECC (affine) of the frame onto the 4K photo, then the photo's own transform."""
    photo = cv2.imread(os.path.realpath(AL.photo_path(rep["_id"])))
    pw, ph = rep["photo_size"]; assert photo.shape[1] == pw, "photo changed since align.py ran"
    k = AL.WORK / max(pw, ph); size = (round(pw * k), round(ph * k))
    P = AL.structure(cv2.resize(photo, size, interpolation=cv2.INTER_AREA))
    F = AL.structure(cv2.resize(frame, size, interpolation=cv2.INTER_AREA))
    M = AL.ecc(P, F, np.float32([[1, 0, 0], [0, 1, 0]]), size)               # work-size frame -> work-size photo
    LAST_SCORES.update({"clip_to_photo": round(AL.score(P, cv2.resize(frame, size), M, size)[0], 4), "photo_to_painting": rep["score"]})
    fh, fw = frame.shape[:2]
    clip_to_photo = np.diag([1 / k, 1 / k, 1.0]) @ np.vstack([M, [0, 0, 1]]) @ np.diag([size[0] / fw, size[1] / fh, 1.0])
    return (np.vstack([np.array(rep["A"]), [0, 0, 1]]) @ clip_to_photo)[:2]

def to_painting(frame, rep):
    """clip px -> aligned-output px, searched directly against the painting (align.py's candidates, best NCC)."""
    P0 = cv2.imread(f"{AL.ART}/{rep['_id']}.jpg"); h, w = P0.shape[:2]
    k = AL.WORK / max(h, w); size = (int(round(w * k)), int(round(h * k)))
    P = cv2.resize(P0, size, interpolation=cv2.INTER_AREA)
    kr = AL.WORK / max(frame.shape[:2]); R = cv2.resize(frame, (int(frame.shape[1] * kr), int(frame.shape[0] * kr)), interpolation=cv2.INTER_AREA)
    Ps, Rs = AL.structure(P), AL.structure(R)
    stretch = np.float32([[size[0] / R.shape[1], 0, 0], [0, size[1] / R.shape[0], 0]])
    cands = {"stretch": stretch, "ecc": AL.ecc(Ps, Rs, stretch, size)}
    Ms, _ = AL.sift_init(P, R)
    if Ms is not None: cands["sift+ecc"] = AL.ecc(Ps, Rs, Ms.astype(np.float32), size, levels=(0.5, 1.0))
    Mt = AL.template_init(Ps, Rs, size)
    if Mt is not None: cands["tmpl+ecc"] = AL.ecc(Ps, Rs, Mt, size, levels=(0.5, 1.0))
    scored = {n: AL.score(Ps, R, M, size) for n, M in cands.items()}
    best = max((n for n in scored if scored[n][1] > 0.85) or scored, key=lambda n: scored[n][0])
    LAST_SCORES.update({"method": best, "score": round(scored[best][0], 4), "candidates": {key: [float(v) for v in val] for key,val in scored.items()}})
    print(f"  painting registration: {best} (NCC {scored[best][0]:.3f}, stretch {scored['stretch'][0]:.3f})")
    ow, oh = rep["out_size"]
    return (np.diag([ow / size[0], oh / size[1], 1.0]) @ np.vstack([cands[best], [0, 0, 1]]) @ np.diag([kr, kr, 1.0]))[:2]

def to_frame(frame, ref):
    """clip px -> clip px: ECC (affine) of one frame onto another frame of the same clip. Muse keeps the room where it
    was across a change inside the clip, so the room carries the registration even when the dancers differ."""
    k = AL.WORK / max(ref.shape[:2]); size = (round(ref.shape[1] * k), round(ref.shape[0] * k))
    R = AL.structure(cv2.resize(ref, size, interpolation=cv2.INTER_AREA))
    F = AL.structure(cv2.resize(frame, size, interpolation=cv2.INTER_AREA))
    M = AL.ecc(R, F, np.float32([[1, 0, 0], [0, 1, 0]]), size)
    return (np.diag([1 / k, 1 / k, 1.0]) @ np.vstack([M, [0, 0, 1]]) @ np.diag([k, k, 1.0]))[:2]

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("id"); ap.add_argument("clip")
    ap.add_argument("--start", type=int, default=0); ap.add_argument("--end", type=int)
    ap.add_argument("--to", choices=["photo", "painting"], default="photo"); ap.add_argument("--out")
    ap.add_argument("--ref", type=int, help="register the segment's first frame onto this frame of the clip, then use that frame's transform")
    a = ap.parse_args()
    rep = json.load(open(f"{DATA}/real/aligned/report.json"))[a.id]; rep["_id"] = a.id
    vw, vh, fps, total = probe(a.clip)
    end = min(a.end or total, total); first = frame_at(a.clip, vw, vh, a.start)
    if a.ref is None:
        M = (to_photo if a.to == "photo" else to_painting)(first, rep).astype(np.float32)
    else:
        ref = frame_at(a.clip, vw, vh, a.ref)
        Mr = (to_photo if a.to == "photo" else to_painting)(ref, rep)
        M = (np.vstack([Mr, [0, 0, 1]]) @ np.vstack([to_frame(first, ref), [0, 0, 1]]))[:2].astype(np.float32)
    ow, oh = rep["out_size"]; ow, oh = ow & ~1, oh & ~1          # yuv420p needs even sizes
    fallback = a.id == "impression-sunrise" and LAST_SCORES.get("score", 0) < 0.5
    if fallback:
        M = np.float32([[ow / vw, 0, 0], [0, oh / vh, 0]])
        print("  NCC below 0.5: ordinary dissolve, no structural warp", flush=True)
    full_frame = a.id == "wanderer-extended"
    if full_frame:
        M = np.float32([[ow / vw, 0, 0], [0, oh / vh, 0]])
        LAST_SCORES["selected_method"] = "full-frame stretch (preserve all of the 16:9 source)"
        LAST_SCORES["selected_score"] = LAST_SCORES["candidates"]["stretch"][0]
    cover = cv2.warpAffine(np.full((vh, vw), 255, np.uint8), M, (ow, oh), flags=cv2.INTER_NEAREST) > 128
    out = a.out or f"{DATA}/footage/muse/aligned/{a.id}{'' if a.start == 0 else f'-from{a.start}'}.mp4"
    os.makedirs(os.path.dirname(out), exist_ok=True)
    # the clip's real picture inside the painting frame, as fractions — 16:9 crops must stay inside it (no mirrored edge)
    q = cv2.transform(np.float32([[[0, 0], [vw, 0], [vw, vh], [0, vh]]]), M)[0]
    inner = [max(q[0][0], q[3][0]) / ow, max(q[0][1], q[1][1]) / oh, min(q[1][0], q[2][0]) / ow, min(q[2][1], q[3][1]) / oh]
    inner = [round(min(max(float(v), 0.0), 1.0), 4) for v in inner]
    json.dump({"id": a.id, "clip": a.clip, "start": a.start, "frames": end - a.start, "fps": fps, "to": a.to, "ref": a.ref, "M": M.tolist(),
               "out_size": [ow, oh], "inner_x0y0x1y1": inner, "scores": LAST_SCORES, "ordinary_dissolve": fallback, "preserve_fullframe": full_frame}, open(out[:-4] + ".json", "w"), indent=1)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{ow}x{oh}", "-r", fps, "-i", "-",
                            "-c:v", "libx264", "-crf", "12", "-preset", "medium", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    count = 0
    for f in stream(a.clip, vw, vh, a.start, end):
        enc.stdin.write(cv2.warpAffine(f, M, (ow, oh), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT).tobytes())
        count += 1
    enc.stdin.close()
    if enc.wait() != 0 or count != end-a.start or probe(out)[3] != count:
        raise RuntimeError(f"Aligned video frame mismatch: {a.id}, {count}/{end-a.start}")
    print(f"{a.id}: frames {a.start}-{end - 1} of {total}, {vw}x{vh} -> {ow}x{oh}, "
          f"{100 * (1 - cover.mean()):.1f}% mirrored edge, {AL.decompose(M, (ow, oh))} -> {out}")

if __name__ == "__main__":
    main()
