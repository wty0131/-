import sqlite3
import json
import os

DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
DB_PATH = os.path.join(DB_DIR, 'library.db')


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    os.makedirs(DB_DIR, exist_ok=True)
    conn = get_db()
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            icon TEXT DEFAULT '📁',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            file_path TEXT NOT NULL UNIQUE,
            file_size INTEGER,
            duration REAL,
            category_id INTEGER,
            tags TEXT DEFAULT '[]',
            watch_status TEXT DEFAULT 'unwatched',
            watch_progress REAL DEFAULT 0,
            notes TEXT DEFAULT '',
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
        );
    ''')
    conn.commit()
    conn.close()


# ── Category CRUD ──

def get_all_categories():
    conn = get_db()
    rows = conn.execute('SELECT * FROM categories ORDER BY name').fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_category(name, icon='📁'):
    conn = get_db()
    conn.execute('INSERT INTO categories (name, icon) VALUES (?, ?)', (name, icon))
    conn.commit()
    conn.close()


def update_category(cat_id, name, icon):
    conn = get_db()
    conn.execute('UPDATE categories SET name=?, icon=? WHERE id=?', (name, icon, cat_id))
    conn.commit()
    conn.close()


def delete_category(cat_id):
    conn = get_db()
    conn.execute('UPDATE videos SET category_id=NULL WHERE category_id=?', (cat_id,))
    conn.execute('DELETE FROM categories WHERE id=?', (cat_id,))
    conn.commit()
    conn.close()


# ── Video CRUD ──

def add_video(title, file_path, file_size=None, duration=None, category_id=None, tags=None):
    conn = get_db()
    conn.execute(
        'INSERT OR IGNORE INTO videos (title, file_path, file_size, duration, category_id, tags) VALUES (?, ?, ?, ?, ?, ?)',
        (title, file_path, file_size, duration, category_id, json.dumps(tags or [], ensure_ascii=False))
    )
    conn.commit()
    conn.close()


def get_all_videos(category_id=None, watch_status=None, search=None, tag=None):
    conn = get_db()
    query = '''
        SELECT v.*, c.name as category_name, c.icon as category_icon
        FROM videos v LEFT JOIN categories c ON v.category_id = c.id
        WHERE 1=1
    '''
    params = []
    if category_id:
        query += ' AND v.category_id = ?'
        params.append(category_id)
    if watch_status:
        query += ' AND v.watch_status = ?'
        params.append(watch_status)
    if search:
        query += ' AND v.title LIKE ?'
        params.append(f'%{search}%')
    if tag:
        query += ' AND v.tags LIKE ?'
        params.append(f'%"{tag}"%')
    query += ' ORDER BY v.added_at DESC'
    rows = conn.execute(query, params).fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        d['tags'] = json.loads(d['tags'])
        result.append(d)
    return result


def get_video(video_id):
    conn = get_db()
    row = conn.execute(
        'SELECT v.*, c.name as category_name, c.icon as category_icon FROM videos v LEFT JOIN categories c ON v.category_id = c.id WHERE v.id = ?',
        (video_id,)
    ).fetchone()
    conn.close()
    if row:
        d = dict(row)
        d['tags'] = json.loads(d['tags'])
        return d
    return None


def update_video(video_id, **kwargs):
    if 'tags' in kwargs and kwargs['tags'] is not None:
        kwargs['tags'] = json.dumps(kwargs['tags'], ensure_ascii=False)
    allowed = {'title', 'category_id', 'tags', 'watch_status', 'watch_progress', 'notes', 'duration', 'file_size'}
    sets = []
    values = []
    for k, v in kwargs.items():
        if k in allowed:
            sets.append(f'{k}=?')
            values.append(v)
    if not sets:
        return
    values.append(video_id)
    conn = get_db()
    conn.execute(f'UPDATE videos SET {", ".join(sets)} WHERE id=?', values)
    conn.commit()
    conn.close()


def delete_video(video_id):
    conn = get_db()
    conn.execute('DELETE FROM videos WHERE id=?', (video_id,))
    conn.commit()
    conn.close()


def get_all_tags():
    conn = get_db()
    rows = conn.execute('SELECT tags FROM videos').fetchall()
    conn.close()
    tags_set = set()
    for r in rows:
        try:
            tags = json.loads(r['tags'])
            tags_set.update(tags)
        except Exception:
            pass
    return sorted(tags_set)
