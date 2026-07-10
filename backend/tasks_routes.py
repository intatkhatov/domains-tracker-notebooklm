from flask import Blueprint, jsonify, request
from database import get_db
from datetime import datetime, timezone

tasks_bp = Blueprint('tasks', __name__)


@tasks_bp.route('/api/sources/<int:source_id>/tasks', methods=['GET'])
def get_tasks(source_id):
    conn = get_db()
    rows = conn.execute(
        'SELECT * FROM tasks WHERE source_id=? ORDER BY position, id',
        (source_id,)
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@tasks_bp.route('/api/sources/<int:source_id>/tasks', methods=['POST'])
def add_task(source_id):
    data = request.json
    now = datetime.now(timezone.utc).isoformat()
    conn = get_db()
    c = conn.cursor()
    c.execute(
        'INSERT INTO tasks (source_id, text, done, created_at) VALUES (?, ?, 0, ?)',
        (source_id, data.get('text', ''), now)
    )
    new_id = c.lastrowid
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok', 'id': new_id})


@tasks_bp.route('/api/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    data = request.json
    conn = get_db()
    conn.execute(
        'UPDATE tasks SET text=?, done=? WHERE id=?',
        (data.get('text', ''), 1 if data.get('done') else 0, task_id)
    )
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})


@tasks_bp.route('/api/tasks/<int:task_id>/done', methods=['PATCH'])
def toggle_task_done(task_id):
    data = request.json
    conn = get_db()
    conn.execute(
        'UPDATE tasks SET done=? WHERE id=?',
        (1 if data.get('done') else 0, task_id)
    )
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})


@tasks_bp.route('/api/tasks/reorder', methods=['POST'])
def reorder_tasks():
    data = request.json
    order = data.get('order', [])
    conn = get_db()
    for i, task_id in enumerate(order):
        conn.execute('UPDATE tasks SET position=? WHERE id=?', (i, task_id))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})


@tasks_bp.route('/api/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    conn = get_db()
    conn.execute('DELETE FROM tasks WHERE id=?', (task_id,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})


@tasks_bp.route('/api/sources/tasks/counts', methods=['GET'])
def get_task_counts():
    conn = get_db()
    rows = conn.execute(
        'SELECT source_id, COUNT(*) as cnt FROM tasks GROUP BY source_id'
    ).fetchall()
    conn.close()
    return jsonify({str(r['source_id']): r['cnt'] for r in rows})
