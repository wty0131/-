"""
Double-click this file to start the WangKe Video Manager.
Uses pythonw.exe (no console window).
"""
import os
import sys
import time
import threading
import webbrowser
import urllib.request
import subprocess

DESKTOP = os.path.join(os.path.expanduser('~'), 'Desktop')
APP_DIR = os.path.join(DESKTOP, '网课管理器')

os.chdir(APP_DIR)
sys.path.insert(0, APP_DIR)

from app import create_app

def wait_and_open(url, timeout=30):
    elapsed = 0
    while elapsed < timeout:
        try:
            urllib.request.urlopen(url, timeout=1)
            webbrowser.open(url)
            return
        except Exception:
            time.sleep(0.5)
            elapsed += 0.5

def main():
    app = create_app()
    port = 5000
    url = f'http://127.0.0.1:{port}'

    threading.Thread(target=wait_and_open, args=[url], daemon=True).start()

    print(f'WangKe Manager: {url}')
    app.run(host='127.0.0.1', port=port, debug=False)

if __name__ == '__main__':
    main()
