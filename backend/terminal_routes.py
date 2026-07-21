from flask import Blueprint, jsonify, request
import sqlite3

terminal_bp = Blueprint('terminal', __name__)
TERMINAL_DB = '/app/data/terminal.db'


def get_terminal_db():
    conn = sqlite3.connect(TERMINAL_DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_terminal_db():
    conn = get_terminal_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS terminal_commands (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            command TEXT NOT NULL,
            position INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()
    print('Terminal DB инициализирована.')


@terminal_bp.route('/api/terminal', methods=['GET'])
def get_commands():
    conn = get_terminal_db()
    rows = conn.execute('SELECT * FROM terminal_commands ORDER BY position, id').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@terminal_bp.route('/api/terminal', methods=['POST'])
def add_command():
    data = request.json
    conn = get_terminal_db()
    c = conn.cursor()
    max_pos = conn.execute('SELECT MAX(position) FROM terminal_commands').fetchone()[0] or 0
    c.execute('INSERT INTO terminal_commands (name, command, position) VALUES (?, ?, ?)',
              (data.get('name', ''), data.get('command', ''), max_pos + 1))
    new_id = c.lastrowid
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok', 'id': new_id})


@terminal_bp.route('/api/terminal/<int:row_id>', methods=['PUT'])
def update_command(row_id):
    data = request.json
    conn = get_terminal_db()
    conn.execute('UPDATE terminal_commands SET name=?, command=? WHERE id=?',
                 (data.get('name', ''), data.get('command', ''), row_id))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})


@terminal_bp.route('/api/terminal/reorder', methods=['POST'])
def reorder_commands():
    data = request.json
    order = data.get('order', [])
    conn = get_terminal_db()
    for i, row_id in enumerate(order):
        conn.execute('UPDATE terminal_commands SET position=? WHERE id=?', (i, row_id))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})


@terminal_bp.route('/api/terminal/<int:row_id>', methods=['DELETE'])
def delete_command(row_id):
    conn = get_terminal_db()
    conn.execute('DELETE FROM terminal_commands WHERE id=?', (row_id,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})
