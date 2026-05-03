import os
import shutil
from flask import Blueprint, render_template, request, jsonify, send_file, url_for
import models
import scanner

bp = Blueprint('main', __name__)


@bp.route('/')
def index():
    categories = models.get_all_categories()
    all_tags = models.get_all_tags()
    return render_template('index.html', categories=categories, all_tags=all_tags)


@bp.route('/video/<int:video_id>')
def video_detail(video_id):
    video = models.get_video(video_id)
    if not video:
        return '视频不存在', 404
    categories = models.get_all_categories()
    return render_template('video_detail.html', video=video, categories=categories)


@bp.route('/categories')
def categories_page():
    categories = models.get_all_categories()
    return render_template('categories.html', categories=categories)


# ── Video API ──

@bp.route('/api/videos')
def api_videos():
    category_id = request.args.get('category_id', type=int)
    watch_status = request.args.get('watch_status')
    search = request.args.get('search')
    tag = request.args.get('tag')
    videos = models.get_all_videos(category_id, watch_status, search, tag)
    for v in videos:
        v['size_display'] = scanner.get_file_size_mb(v.get('file_size'))
        v['duration_display'] = scanner.format_duration(v.get('duration'))
    return jsonify(videos)


@bp.route('/api/videos/<int:video_id>', methods=['GET'])
def api_get_video(video_id):
    v = models.get_video(video_id)
    if not v:
        return jsonify({'error': 'not found'}), 404
    v['size_display'] = scanner.get_file_size_mb(v.get('file_size'))
    v['duration_display'] = scanner.format_duration(v.get('duration'))
    return jsonify(v)


@bp.route('/api/videos/<int:video_id>', methods=['PUT'])
def api_update_video(video_id):
    data = request.get_json()
    models.update_video(video_id, **data)
    return jsonify({'ok': True})


@bp.route('/api/videos/<int:video_id>', methods=['DELETE'])
def api_delete_video(video_id):
    models.delete_video(video_id)
    return jsonify({'ok': True})


@bp.route('/api/scan', methods=['POST'])
def api_scan():
    directory = request.get_json().get('directory') if request.is_json else None
    videos = scanner.scan_directory(directory)
    count = 0
    for v in videos:
        models.add_video(v['title'], v['file_path'], v['file_size'], v['duration'])
        count += 1
    return jsonify({'ok': True, 'total': count})


@bp.route('/api/import', methods=['POST'])
def api_import():
    data = request.get_json()
    paths = data.get('paths', [])
    count = 0
    for p in paths:
        if os.path.isfile(p):
            ext = os.path.splitext(p)[1].lower()
            if ext in scanner.VIDEO_EXTENSIONS:
                title = os.path.splitext(os.path.basename(p))[0]
                size = os.path.getsize(p)
                duration = scanner.get_video_duration(p)
                models.add_video(title, p, size, duration)
                count += 1
    return jsonify({'ok': True, 'imported': count})


@bp.route('/api/import-upload', methods=['POST'])
def api_import_upload():
    uploaded = request.files.getlist('files')
    os.makedirs(scanner.VIDEO_LIBRARY, exist_ok=True)
    count = 0
    for f in uploaded:
        if f.filename:
            ext = os.path.splitext(f.filename)[1].lower()
            if ext in scanner.VIDEO_EXTENSIONS:
                filepath = os.path.join(scanner.VIDEO_LIBRARY, f.filename)
                f.save(filepath)
                title = os.path.splitext(f.filename)[0]
                size = os.path.getsize(filepath)
                duration = scanner.get_video_duration(filepath)
                models.add_video(title, filepath, size, duration)
                count += 1
    return jsonify({'ok': True, 'imported': count})


@bp.route('/api/open-library', methods=['POST'])
def api_open_library():
    os.makedirs(scanner.VIDEO_LIBRARY, exist_ok=True)
    os.startfile(scanner.VIDEO_LIBRARY)
    return jsonify({'ok': True})


@bp.route('/api/videos/<int:video_id>/open', methods=['POST'])
def api_open_video(video_id):
    video = models.get_video(video_id)
    if not video:
        return jsonify({'error': 'not found'}), 404
    filepath = video['file_path']
    if os.path.exists(filepath):
        os.startfile(filepath)
        models.update_video(video_id, watch_status='watching')
        return jsonify({'ok': True})
    return jsonify({'error': 'file not found'}), 404


@bp.route('/api/videos/<int:video_id>/open-folder', methods=['POST'])
def api_open_folder(video_id):
    video = models.get_video(video_id)
    if not video:
        return jsonify({'error': 'not found'}), 404
    folder = os.path.dirname(video['file_path'])
    if os.path.exists(folder):
        os.startfile(folder)
        return jsonify({'ok': True})
    return jsonify({'error': 'folder not found'}), 404


@bp.route('/api/videos/<int:video_id>/stream')
def api_stream_video(video_id):
    video = models.get_video(video_id)
    if not video or not os.path.exists(video['file_path']):
        return '视频文件不存在', 404
    return send_file(video['file_path'], mimetype='video/mp4')


# ── Category API ──

@bp.route('/api/categories', methods=['GET'])
def api_categories():
    cats = models.get_all_categories()
    for c in cats:
        conn = models.get_db()
        c['video_count'] = conn.execute(
            'SELECT COUNT(*) FROM videos WHERE category_id=?', (c['id'],)
        ).fetchone()[0]
        conn.close()
    return jsonify(cats)


@bp.route('/api/categories', methods=['POST'])
def api_add_category():
    data = request.get_json()
    models.add_category(data['name'], data.get('icon', '📁'))
    return jsonify({'ok': True})


@bp.route('/api/categories/<int:cat_id>', methods=['PUT'])
def api_update_category(cat_id):
    data = request.get_json()
    models.update_category(cat_id, data['name'], data.get('icon', '📁'))
    return jsonify({'ok': True})


@bp.route('/api/categories/<int:cat_id>', methods=['DELETE'])
def api_delete_category(cat_id):
    models.delete_category(cat_id)
    return jsonify({'ok': True})


# ── Tag API ──

@bp.route('/api/tags')
def api_tags():
    return jsonify(models.get_all_tags())


# ── Serve video library files directly ──

@bp.route('/library/<path:filepath>')
def serve_library(filepath):
    full_path = os.path.join(scanner.VIDEO_LIBRARY, filepath)
    if os.path.exists(full_path):
        return send_file(full_path)
    return 'File not found', 404
