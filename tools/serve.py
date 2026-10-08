#!/usr/bin/env python3
"""Local preview server with auto-reload.

Usage:  python3 tools/serve.py [port]      (default port 8000)
Open http://localhost:8000 . The page reloads by itself whenever a file
in the site folder is saved. The reload snippet is injected only by this
server, so the published HTML stays unchanged.
"""
import http.server, os, sys, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
SNIPPET = b"""<script>(()=>{let last=null;setInterval(async()=>{try{const r=await fetch('/__mtime',{cache:'no-store'});const t=(await r.json()).t;if(last!==null&&t!==last)location.reload();last=t;}catch(e){}},800);})();</script>"""

def latest_mtime():
    t = 0.0
    for d, dirs, files in os.walk(ROOT):
        dirs[:] = [x for x in dirs if not x.startswith('.')]
        for f in files:
            try: t = max(t, os.path.getmtime(os.path.join(d, f)))
            except OSError: pass
    return t

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k): super().__init__(*a, directory=ROOT, **k)
    def end_headers(self):
        self.send_header('Cache-Control', 'no-store'); super().end_headers()
    def log_message(self, *a): pass
    def do_GET(self):
        if self.path == '/__mtime':
            body = json.dumps({'t': latest_mtime()}).encode()
            self.send_response(200); self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body))); self.end_headers(); self.wfile.write(body); return
        path = self.translate_path(self.path)
        if os.path.isdir(path): path = os.path.join(path, 'index.html')
        if path.endswith('.html') and os.path.isfile(path):
            data = open(path, 'rb').read()
            data = data.replace(b'</body>', SNIPPET + b'</body>') if b'</body>' in data else data + SNIPPET
            self.send_response(200); self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(data))); self.end_headers(); self.wfile.write(data); return
        super().do_GET()

if __name__ == '__main__':
    http.server.ThreadingHTTPServer.allow_reuse_address = True
    with http.server.ThreadingHTTPServer(('127.0.0.1', PORT), Handler) as s:
        print(f'Preview: http://localhost:{PORT}  (Ctrl+C to stop)', flush=True)
        s.serve_forever()
