"""The listening page's little server: serves a report folder and saves Yancy's 通过 / 重配 to decisions.json.

    python3 scripts/qa/qa.py serve out/qa/<film> [--port 8766]

Local only (127.0.0.1). Each decision is keyed to a finding's key, which is tied to the line's text and what was
heard, so an unchanged line keeps its decision after a re-render and a re-voiced line is asked again.
"""
from __future__ import annotations

import datetime as dt
import json
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

LOCK = threading.Lock()


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, folder: Path, **kwargs):
        self.folder = folder
        super().__init__(*args, directory=str(folder), **kwargs)

    def log_message(self, fmt, *args):  # keep the console for decisions
        pass

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self.path = "/review.html"
        if self.path.split("?")[0] == "/decisions.json" and not (self.folder / "decisions.json").exists():
            return self.reply({})
        if self.path == "/ping":
            return self.reply({"ok": True})
        return super().do_GET()

    def reply(self, obj, code=200):
        body = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path != "/decision":
            return self.reply({"error": "not found"}, 404)
        data = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        key, decision = data.get("key"), data.get("decision")
        if not key or decision not in ("pass", "redo", None):
            return self.reply({"error": "bad request"}, 400)
        path = self.folder / "decisions.json"
        with LOCK:
            all_ = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
            if decision is None:
                all_.pop(key, None)
            else:
                all_[key] = {"decision": decision, "note": (data.get("note") or "").strip(),
                             "title": data.get("title", ""), "at": dt.datetime.now().isoformat(timespec="seconds")}
            tmp = path.with_suffix(".tmp")
            tmp.write_text(json.dumps(all_, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
            tmp.replace(path)
        print(f"{decision or '撤销'}: {data.get('title', key)}" + (f" — {data['note']}" if data.get("note") else ""), flush=True)
        return self.reply({"ok": True, "decisions": all_})


def run(folder: Path, port: int = 8766) -> None:
    if not (folder / "review.html").exists():
        raise SystemExit(f"{folder} 里没有 review.html：先运行 qa.py check")
    server = ThreadingHTTPServer(("127.0.0.1", port), partial(Handler, folder=folder))
    print(f"试听页：http://127.0.0.1:{port}/   （{folder}）", flush=True)
    server.serve_forever()
