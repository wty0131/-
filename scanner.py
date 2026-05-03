import os
import subprocess
import json

VIDEO_EXTENSIONS = {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.mpg', '.mpeg', '.rmvb', '.ts', '.3gp'}

VIDEO_LIBRARY = os.path.join(os.path.expanduser('~'), 'Desktop', '网课视频库')


def get_video_duration(filepath):
    try:
        cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', filepath]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            data = json.loads(result.stdout)
            duration = float(data['format'].get('duration', 0))
            return duration
    except Exception:
        pass
    return None


def scan_directory(directory=None):
    if directory is None:
        directory = VIDEO_LIBRARY
    if not os.path.exists(directory):
        return []
    videos = []
    for root, dirs, files in os.walk(directory):
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in VIDEO_EXTENSIONS:
                filepath = os.path.join(root, f)
                stat = os.stat(filepath)
                title = os.path.splitext(f)[0]
                videos.append({
                    'title': title,
                    'file_path': filepath,
                    'file_size': stat.st_size,
                    'duration': None,
                })
    return videos


def get_file_size_mb(size_bytes):
    if size_bytes is None:
        return '未知'
    mb = size_bytes / (1024 * 1024)
    if mb >= 1024:
        return f'{mb / 1024:.1f} GB'
    return f'{mb:.1f} MB'


def format_duration(seconds):
    if seconds is None:
        return '未知'
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    if h > 0:
        return f'{h}:{m:02d}:{s:02d}'
    return f'{m}:{s:02d}'
