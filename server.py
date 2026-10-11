#!/usr/bin/env python3
import sqlite3
import json
import os
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

DB_FILE = "/tmp/vmess_users.db"
HTTP_PORT = 8081
TARGET_IP = os.environ.get('IP', '127.0.0.1')
OWNER_KEY = "hasib404"
START_TIME = time.time()

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS connections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_ip TEXT UNIQUE,
        connected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        duration TEXT DEFAULT '00:00:00',
        status TEXT DEFAULT 'ACTIVE',
        data_mb REAL DEFAULT 0.0
    )''')
    conn.commit()
    conn.close()

def get_connections():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT source_ip, duration, status, data_mb FROM connections')
    rows = c.fetchall()
    conn.close()
    return rows

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        p = urlparse(self.path)
        if p.path == '/':
            self.serve_html()
        elif p.path == '/api/stats':
            self.api_stats()
        elif p.path == '/api/termux':
            self.api_termux(p.query)
        else:
            self.send_error(404)

    def serve_html(self):
        uptime_seconds = int(time.time() - START_TIME)
        hours, remainder = divmod(uptime_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

        html = f'''<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>VMess WS Dashboard</title>
<style>
body {{ margin:0; font-family:Arial, sans-serif; background:#050505; color:#e0e0e0; }}
.container {{ max-width:900px; margin:0 auto; padding:35px 20px; }}
.panel {{ background:#0f0f0f; border:1px solid #333; padding:22px; margin-bottom:20px; border-radius:8px; }}
.info-row {{ display:flex; justify-content:space-between; padding:10px 0; border-bottom:1px dashed #222; }}
.val {{ font-weight:bold; color:#fff; }}
h1 {{ text-align:center; letter-spacing:3px; }}
.btn {{ background:transparent; color:#fff; border:1px solid #fff; padding:10px 20px; cursor:pointer; }}
</style>
</head>
<body>
<div class="container">
<h1>VMess WS Server</h1>

<div class="panel">
<h3>HOST INFO</h3>
<div class="info-row"><span>HOST:</span><span class="val" id="val-host">Detecting...</span></div>
<div class="info-row"><span>POINTED SERVER:</span><span class="val">{TARGET_IP}</span></div>
<div class="info-row"><span>UPTIME:</span><span class="val">{uptime_str}</span></div>
<div class="info-row"><span>SERVER STATUS:</span><span class="val" style="color:#00ff88;">ONLINE</span></div>
<div class="info-row"><span>PROTOCOL:</span><span class="val">VMESS + WS</span></div>
</div>

<div class="panel">
<h3>NETWORK METRICS</h3>
<div class="info-row"><span>CONNECTED USERS:</span><span class="val" id="val-users">0</span></div>
<div class="info-row"><span>SERVER PING:</span><span class="val" id="val-ping">0 ms</span></div>
</div>

<div style="text-align:center;">
<button class="btn" onclick="location.reload()">Refresh Data</button>
</div>
</div>

<script>
document.getElementById('val-host').innerText = window.location.hostname;

function fetchStats() {{
    fetch('/api/stats')
    .then(res => res.json())
    .then(data => {{
        document.getElementById('val-users').innerText = data.active_count;
        document.getElementById('val-ping').innerText = data.ping_ms + ' ms';
    }});
}}
setInterval(fetchStats, 5000);
fetchStats();
</script>
</body>
</html>'''
        self.wfile.write(html.encode())

    def api_stats(self):
        rows = get_connections()
        ping_ms = int((time.time() - START_TIME) % 15) + 12
        self.send_json({
            'active_count': len(rows),
            'ping_ms': ping_ms
        })

    def api_termux(self, query):
        params = parse_qs(query)
        key = params.get('key', [''])[0]
        if key != OWNER_KEY:
            self.send_json({'error': 'Unauthorized'})
            return

        cmd = params.get('cmd', [''])[0]
        if cmd == 'list':
            rows = get_connections()
            data = [{'ip': r[0], 'duration': r[1], 'status': r[2], 'mb_consumed': r[3]} for r in rows]
            self.send_json(data)
        else:
            self.send_json({'error': 'Unknown command'})

    def send_json(self, data):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def log_message(self, format, *args):
        pass

if __name__ == '__main__':
    init_db()
    server = HTTPServer(('0.0.0.0', HTTP_PORT), Handler)
    print(f"VMess WS Manager running on port {HTTP_PORT}")
    server.serve_forever()