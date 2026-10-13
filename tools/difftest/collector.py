#!/usr/bin/env python3
"""Tiny HTTP collector for the runtime differential harness.

The `Probe.as` driver POSTs its report to http://127.0.0.1:8765/report. Each
body is appended to the output file given as argv[1].
"""
import http.server
import socketserver
import sys

OUT = sys.argv[1] if len(sys.argv) > 1 else "/tmp/gaz-runtime-reports.txt"
PORT = 8765


class Handler(http.server.BaseHTTPRequestHandler):
    def _ok(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(b"ok")

    def do_POST(self):
        n = int(self.headers.get("Content-Length", "0") or 0)
        body = self.rfile.read(n).decode("utf-8", "replace")
        with open(OUT, "a", encoding="utf-8") as fh:
            fh.write(body.rstrip() + "\n---8<---\n")
        self._ok()

    def do_GET(self):
        self._ok()

    def log_message(self, *args):
        pass


def main() -> int:
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", PORT), Handler) as srv:
        srv.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
