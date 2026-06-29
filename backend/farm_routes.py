from flask import Blueprint, jsonify, request
from farm_db import get_farm_db

farm_bp = Blueprint('farm', __name__)


@farm_bp.route('/api/farm', methods=['GET'])
def get_farm():
    conn = get_farm_db()
    rows = conn.execute('SELECT * FROM farm ORDER BY number').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@farm_bp.route('/api/farm', methods=['POST'])
def add_farm():
    data = request.json
    conn = get_farm_db()
    c = conn.cursor()

    # Автономер если не передан
    if data.get('number'):
        number = int(data['number'])
    else:
        row = c.execute('SELECT MAX(number) FROM farm').fetchone()
        number = (row[0] or 0) + 1

    c.execute('''
        INSERT INTO farm (number, name, day, month, year, gender, email, phone_confirm, phone_account, password, lost, loss_reason)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        number,
        data.get('name', ''),
        data.get('day'),
        data.get('month', ''),
        data.get('year'),
        data.get('gender', 'Не указан'),
        data.get('email', ''),
        data.get('phone_confirm', ''),
        data.get('phone_account', ''),
        data.get('password', ''),
        1 if data.get('lost') else 0,
        data.get('loss_reason', '')
    ))
    new_id = c.lastrowid
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok', 'id': new_id})


@farm_bp.route('/api/farm/<int:row_id>', methods=['PUT'])
def update_farm(row_id):
    data = request.json
    conn = get_farm_db()
    conn.execute('''
        UPDATE farm SET
            number=?, name=?, day=?, month=?, year=?,
            gender=?, email=?, phone_confirm=?, phone_account=?, password=?, lost=?, loss_reason=?
        WHERE id=?
    ''', (
        data.get('number'),
        data.get('name', ''),
        data.get('day'),
        data.get('month', ''),
        data.get('year'),
        data.get('gender', 'Не указан'),
        data.get('email', ''),
        data.get('phone_confirm', ''),
        data.get('phone_account', ''),
        data.get('password', ''),
        1 if data.get('lost') else 0,
        data.get('loss_reason', ''),
        row_id
    ))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})


@farm_bp.route('/api/farm/<int:row_id>', methods=['DELETE'])
def delete_farm(row_id):
    conn = get_farm_db()
    conn.execute('DELETE FROM farm WHERE id=?', (row_id,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})
