import os
import sys
import time
import webbrowser
import threading
import urllib.request
from flask import Flask
import models
from routes import bp


def create_app():
    app = Flask(__name__)
    app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024 * 1024  # 10GB max upload
    app.register_blueprint(bp)
    models.init_db()
    return app


def wait_and_open(url, timeout=30):
    """Poll the server until it responds, then open the browser."""
    elapsed = 0
    while elapsed < timeout:
        try:
            urllib.request.urlopen(url, timeout=1)
            webbrowser.open(url)
            return
        except Exception:
            time.sleep(0.5)
            elapsed += 0.5
    print(f'[警告] 服务启动超时，请手动访问: {url}')


def main():
    app = create_app()
    port = 5000
    url = f'http://127.0.0.1:{port}'

    # Open browser only after server is actually listening
    threading.Thread(target=wait_and_open, args=[url], daemon=True).start()

    print('📚 网课视频管理器已启动')
    print(f'   浏览器访问: {url}')
    library_path = os.path.join(os.path.expanduser('~'), 'Desktop', '网课视频库')
    print(f'   视频库目录: {library_path}')
    print('   按 Ctrl+C 退出')

    app.run(host='127.0.0.1', port=port, debug=False)


if __name__ == '__main__':
    main()
