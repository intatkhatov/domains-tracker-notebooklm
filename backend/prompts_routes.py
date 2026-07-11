from flask import Blueprint, jsonify, request
import sqlite3

prompts_bp = Blueprint('prompts', __name__)
PROMPTS_DB = '/app/data/prompts.db'


def get_prompts_db():
    conn = sqlite3.connect(PROMPTS_DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_prompts_db():
    conn = get_prompts_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS prompts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            prompt TEXT NOT NULL,
            position INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()
    print('Prompts DB инициализирована.')


@prompts_bp.route('/api/prompts', methods=['GET'])
def get_prompts():
    conn = get_prompts_db()
    rows = conn.execute('SELECT * FROM prompts ORDER BY position, id').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@prompts_bp.route('/api/prompts', methods=['POST'])
def add_prompt():
    data = request.json
    conn = get_prompts_db()
    c = conn.cursor()
    max_pos = conn.execute('SELECT MAX(position) FROM prompts').fetchone()[0] or 0
    c.execute('INSERT INTO prompts (name, prompt, position) VALUES (?, ?, ?)',
              (data.get('name', ''), data.get('prompt', ''), max_pos + 1))
    new_id = c.lastrowid
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok', 'id': new_id})


@prompts_bp.route('/api/prompts/<int:row_id>', methods=['PUT'])
def update_prompt(row_id):
    data = request.json
    conn = get_prompts_db()
    conn.execute('UPDATE prompts SET name=?, prompt=? WHERE id=?',
                 (data.get('name', ''), data.get('prompt', ''), row_id))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})


@prompts_bp.route('/api/prompts/reorder', methods=['POST'])
def reorder_prompts():
    data = request.json
    order = data.get('order', [])
    conn = get_prompts_db()
    for i, row_id in enumerate(order):
        conn.execute('UPDATE prompts SET position=? WHERE id=?', (i, row_id))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})


@prompts_bp.route('/api/prompts/<int:row_id>', methods=['DELETE'])
def delete_prompt(row_id):
    conn = get_prompts_db()
    conn.execute('DELETE FROM prompts WHERE id=?', (row_id,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})
