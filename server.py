#!/usr/bin/env python3
import sqlite3
import json
import os
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from datetime import datetime

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
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>hasib404 Dashboard</title>
    <style>
        body {{ margin: 0; font-family: 'Courier New', Courier, monospace; background-color: #050505; color: #e0e0e0; overflow-x: hidden; }}

        #loader {{ position: fixed; width: 100%; height: 100%; background: #000; display: flex; align-items: center; justify-content: center; z-index: 9999; flex-direction: column; transition: opacity 0.5s; }}
        .spinner {{ border: 3px solid #222; border-top: 3px solid #fff; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; margin-bottom: 20px; }}
        @keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}

        .container {{ max-width: 900px; margin: 0 auto; padding: 40px 20px; display: none; }}

        .glitch-wrapper {{ text-align: center; margin-bottom: 40px; }}
        .glitch {{ font-size: 3.5rem; font-weight: bold; position: relative; color: white; text-transform: uppercase; letter-spacing: 6px; display: inline-block; }}
        .glitch::before, .glitch::after {{ content: "hasib404"; position: absolute; top: 0; left: 0; background: #050505; overflow: hidden; }}
        .glitch::before {{ left: 2px; text-shadow: -2px 0 red; animation: glitch-anim 2s infinite linear alternate-reverse; }}
        .glitch::after {{ left: -2px; text-shadow: -2px 0 blue; animation: glitch-anim 3s infinite linear alternate-reverse; }}
        @keyframes glitch-anim {{
            0% {{ clip: rect(24px, 9999px, 9px, 0); }}
            20% {{ clip: rect(85px, 9999px, 14px, 0); }}
            40% {{ clip: rect(66px, 9999px, 5px, 0); }}
            60% {{ clip: rect(92px, 9999px, 73px, 0); }}
            80% {{ clip: rect(50px, 9999px, 30px, 0); }}
            100% {{ clip: rect(10px, 9999px, 45px, 0); }}
        }}

        .panel {{ background: #0f0f0f; border: 1px solid #333; padding: 25px; margin-bottom: 25px; border-radius: 4px; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }}
        .panel-title {{ border-bottom: 1px solid #333; padding-bottom: 10px; margin-top: 0; margin-bottom: 20px; font-size: 1.2rem; color: #fff; letter-spacing: 2px; }}
        .info-row {{ display: flex; justify-content: space-between; padding: 12px 0; border-bottom: 1px dashed #222; font-size: 0.95rem; }}
        .info-row:last-child {{ border-bottom: none; }}
        .val {{ font-weight: bold; color: #fff; }}

        .btn {{ background: transparent; color: #fff; border: 1px solid #fff; padding: 10px 20px; cursor: pointer; font-family: inherit; font-weight: bold; text-transform: uppercase; transition: all 0.3s; margin-top: 15px; display: inline-block; }}
        .btn:hover {{ background: #fff; color: #000; }}
        .footer {{ text-align: center; margin-top: 50px; font-size: 0.8rem; color: #666; border-top: 1px solid #222; padding-top: 20px; }}
        .top-bar {{ display: flex; justify-content: space-between; margin-bottom: 30px; color: #888; font-size: 0.9rem; }}
    </style>
</head>
<body>

    <div id="loader">
        <div class="spinner"></div>
        <p>Loading Webpage... this won't take a minute.</p>
    </div>

    <div class="container" id="main-content">
        <div class="top-bar">
            <span id="real-time-clock">--:--:--</span>
            <span>HASIB HOSSEN TECH NETWORK</span>
        </div>

        <div class="glitch-wrapper">
            <div class="glitch">hasib404</div>
        </div>

        <div class="panel">
            <h3 class="panel-title">[+] HOST INFO</h3>
            <div class="info-row"><span>HOST:</span> <span class="val" id="val-host">Detecting...</span></div>
            <div class="info-row"><span>POINTED SERVER:</span> <span class="val">{TARGET_IP}</span></div>
            <div class="info-row"><span>UPTIME:</span> <span class="val">{uptime_str}</span></div>
            <div class="info-row"><span>SERVER STATUS:</span> <span class="val" style="color: #00ff88;">ONLINE</span></div>
            <div class="info-row"><span>HOST IP REGION:</span> <span class="val" id="val-region">Detecting...</span></div>
            <div class="info-row"><span>PROTOCOL:</span> <span class="val">VMESS + WS</span></div>
        </div>

        <div class="panel">
            <h3 class="panel-title">[*] NETWORK METRICS</h3>
            <div class="info-row"><span>YOUR IP ADDRESS:</span> <span class="val"><span id="val-ip">Detecting...</span> [IP]</span></div>
            <div class="info-row"><span>CONNECTED USERS:</span> <span class="val" id="val-users">0</span></div>
            <div class="info-row"><span>SERVER PING:</span> <span class="val" id="val-ping">0 ms</span></div>
        </div>

        <div style="text-align: center;">
            <button class="btn" onclick="location.reload()">Refresh Data</button>
        </div>

        <div class="footer">
            SYSTEM DESIGNED BY HASIB HOSSEN TECH NETWORK | AUTHORIZED ACCESS ONLY
        </div>
    </div>

    <script>
        setTimeout(() => {{
            document.getElementById('loader').style.opacity = '0';
            setTimeout(() => {{
                document.getElementById('loader').style.display = 'none';
                document.getElementById('main-content').style.display = 'block';
            }}, 500);
        }}, 2000);

        setInterval(() => {{
            document.getElementById('real-time-clock').innerText = new Date().toLocaleString();
        }}, 1000);

        fetch('https://ipapi.co/json/')
            .then(res => res.json())
            .then(data => {{
                document.getElementById('val-ip').innerText = data.ip;
                document.getElementById('val-region').innerText = data.city + ', ' + data.country_name;
            }}).catch(() => {{
                document.getElementById('val-ip').innerText = "Unavailable";
                document.getElementById('val-region').innerText = "Unavailable";
            }});

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
    print(f"Manager running on port {HTTP_PORT}")
    server.serve_forever()