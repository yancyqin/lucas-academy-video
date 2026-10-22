#!/usr/bin/env python3
"""frame_sink.py OUTDIR [--port 8742] — the local frame sink for the faune living frames.

The film copy of the art lab (film_hook.py) plays each living painting and POSTs every frame as a JPEG data URL to
http://127.0.0.1:8742/frame?name=live-<id>&i=<n>; this writes OUTDIR/live-<id>/<n:04d>.jpg (then move them to
DATA/faune/film/<id>/frames-live). It listens on 127.0.0.1 only.
"""
import argparse, base64, os, re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

ap = argparse.ArgumentParser(); ap.add_argument("out"); ap.add_argument("--port", type=int, default=8742); a = ap.parse_args()


class Sink(BaseHTTPRequestHandler):
    def cors(self):
        self.send_header("Access-Control-Allow-Origin", "*"); self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(204); self.cors(); self.end_headers()

    def do_POST(self):
        q = parse_qs(urlparse(self.path).query); name = q.get("name", ["frames"])[0]; i = int(q.get("i", ["0"])[0])
        if not re.fullmatch(r"[\w-]+", name): self.send_response(400); self.cors(); self.end_headers(); return
        body = self.rfile.read(int(self.headers.get("Content-Length", 0))).decode()
        d = os.path.join(a.out, name); os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, f"{i:04d}.jpg"), "wb") as f: f.write(base64.b64decode(body.split(",", 1)[1]))
        self.send_response(200); self.cors(); self.end_headers(); self.wfile.write(b"ok")

    def log_message(self, *args): pass


print(f"frame sink on 127.0.0.1:{a.port} → {a.out}")
ThreadingHTTPServer(("127.0.0.1", a.port), Sink).serve_forever()
