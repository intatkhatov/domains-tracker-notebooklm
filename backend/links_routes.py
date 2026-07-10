from flask import Blueprint, jsonify, request
import sqlite3

links_bp = Blueprint('links', __name__)
LINKS_DB = '/app/data/links.db'


def get_links_db():
    conn = sqlite3.connect(LINKS_DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_links_db():
    conn = get_links_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            url TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()
    print('Links DB инициализирована.')


@links_bp.route('/api/links', methods=['GET'])
def get_links():
    conn = get_links_db()
    rows = conn.execute('SELECT * FROM links ORDER BY position, id').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@links_bp.route('/api/links', methods=['POST'])
def add_link():
    data = request.json
    conn = get_links_db()
    c = conn.cursor()
    c.execute('INSERT INTO links (name, url) VALUES (?, ?)', (data.get('name', ''), data.get('url', '')))
    new_id = c.lastrowid
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok', 'id': new_id})


@links_bp.route('/api/links/<int:row_id>', methods=['PUT'])
def update_link(row_id):
    data = request.json
    conn = get_links_db()
    conn.execute('UPDATE links SET name=?, url=? WHERE id=?', (data.get('name', ''), data.get('url', ''), row_id))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})


@links_bp.route('/api/links/reorder', methods=['POST'])
def reorder_links():
    data = request.json
    order = data.get('order', [])
    conn = get_links_db()
    for i, row_id in enumerate(order):
        conn.execute('UPDATE links SET position=? WHERE id=?', (i, row_id))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})


@links_bp.route('/api/links/<int:row_id>', methods=['DELETE'])
def delete_link(row_id):
    conn = get_links_db()
    conn.execute('DELETE FROM links WHERE id=?', (row_id,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})
