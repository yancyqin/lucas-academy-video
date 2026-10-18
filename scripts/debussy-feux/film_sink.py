#!/usr/bin/env python3
"""Local helper for capturing the 焰火 living paintings frame by frame from the browser.

  GET  /plan/<name>.json      serves <film>/<name>/plan.json (the section's show + per-frame night/lamps)
  POST /frame?name=N&i=K      body = JPEG or a data URL -> <film>/<name>/frames-live/<K:05d>.jpg

    python film_sink.py <film dir> [port]
"""
import base64, http.server, os, sys, urllib.parse

FILM = sys.argv[1]

class H(http.server.BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*"); self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
    def do_OPTIONS(self):
        self.send_response(204); self._cors(); self.end_headers()
    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path
        name = os.path.basename(path)[:-5] if path.startswith("/plan/") and path.endswith(".json") else None
        f = os.path.join(FILM, name, "plan.json") if name else None
        if not f or not os.path.exists(f):
            self.send_response(404); self._cors(); self.end_headers(); return
        data = open(f, "rb").read()
        self.send_response(200); self._cors(); self.send_header("Content-Type", "application/json"); self.end_headers(); self.wfile.write(data)
    def do_POST(self):
        q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        name = os.path.basename(q.get("name", ["clip"])[0]); i = int(q.get("i", ["0"])[0])
        d = os.path.join(FILM, name, "frames-live"); os.makedirs(d, exist_ok=True)
        data = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        if data[:5] == b"data:": data = base64.b64decode(data.split(b",", 1)[1])      # toDataURL (toBlob stalls in a hidden pane)
        open(os.path.join(d, f"{i:05d}.jpg"), "wb").write(data)
        self.send_response(200); self._cors(); self.end_headers(); self.wfile.write(b"ok")
    def log_message(self, *a): pass

http.server.ThreadingHTTPServer(("127.0.0.1", int(sys.argv[2]) if len(sys.argv) > 2 else 8746), H).serve_forever()
