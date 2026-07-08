"""
Изолированный модуль массового импорта источников из JSON.
Можно полностью удалить этот файл + блок import_bp в app.py
без последствий для остального приложения.
"""

import json
import os
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
from database import get_db
from similarity import check_duplicates

import_bp = Blueprint('import_bp', __name__)

TEMP_DIR = '/app/data/import_temp'
os.makedirs(TEMP_DIR, exist_ok=True)
TEMP_FILE = os.path.join(TEMP_DIR, 'pending_import.json')


@import_bp.route('/api/import/upload', methods=['POST'])
def upload_import_file():
    if 'file' not in request.files:
        return jsonify({'error': 'Файл не найден'}), 400

    file = request.files['file']
    try:
        content = file.read().decode('utf-8')
        items = json.loads(content)
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        return jsonify({'error': f'Некорректный JSON: {str(e)}'}), 400

    if not isinstance(items, list):
        return jsonify({'error': 'JSON должен быть массивом источников'}), 400

    # Базовая валидация и нормализация
    cleaned = []
    for idx, item in enumerate(items):
        citation = (item.get('citation') or '').strip()
        if not citation:
            continue
        cleaned.append({
            'row_index': idx,
            'short_name': (item.get('short_name') or '').strip(),
            'citation': citation,
            'original_language': (item.get('original_language') or '').strip(),
            'original_lost': bool(item.get('original_lost', False)),
            'authoritative_translation_language': (item.get('authoritative_translation_language') or '').strip(),
            'notebook_url': (item.get('notebook_url') or '').strip()
        })

    # Временно сохраняем на диск
    with open(TEMP_FILE, 'w', encoding='utf-8') as f:
        json.dump(cleaned, f, ensure_ascii=False)

    # Анализ на дубликаты против текущей базы
    conn = get_db()
    rows = conn.execute('SELECT id, short_name, citation FROM sources').fetchall()
    conn.close()
    existing = [dict(r) for r in rows]

    results = []
    for item in cleaned:
        matches = check_duplicates(item['citation'], existing, threshold=0.45, max_results=3)
        results.append({
            'row_index': item['row_index'],
            'short_name': item['short_name'],
            'citation': item['citation'],
            'matches': matches,
            'status': 'duplicate_candidate' if matches else 'new'
        })

    return jsonify({
        'total': len(cleaned),
        'new_count': sum(1 for r in results if r['status'] == 'new'),
        'duplicate_count': sum(1 for r in results if r['status'] == 'duplicate_candidate'),
        'items': results
    })


@import_bp.route('/api/import/confirm', methods=['POST'])
def confirm_import():
    data = request.json or {}
    row_indices_to_import = set(data.get('row_indices', []))

    if not os.path.exists(TEMP_FILE):
        return jsonify({'error': 'Нет данных для импорта. Загрузите файл заново.'}), 400

    with open(TEMP_FILE, 'r', encoding='utf-8') as f:
        cleaned = json.load(f)

    conn = get_db()
    c = conn.cursor()

    # Определяем текущий максимальный номер
    c.execute('SELECT source_id FROM sources')
    existing_ids = [r['source_id'] for r in c.fetchall()]
    max_num = 0
    for sid in existing_ids:
        try:
            n = int(sid)
            if n > max_num:
                max_num = n
        except (ValueError, TypeError):
            pass

    imported_count = 0
    now = datetime.now(timezone.utc).isoformat()

    for item in cleaned:
        if item['row_index'] not in row_indices_to_import:
            continue

        max_num += 1
        raw_name = item['short_name'].strip()
        short_name = f"{max_num}. {raw_name}" if raw_name else f"{max_num}."

        c.execute('''
            INSERT INTO sources
            (domain_rank, source_id, short_name, citation, original_language, original_lost,
             authoritative_translation_language, notebook_url, processed, listened, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, 0, ?)
        ''', (
            1,
            str(max_num),
            short_name,
            item['citation'],
            item['original_language'],
            1 if item['original_lost'] else 0,
            item['authoritative_translation_language'],
            item['notebook_url'],
            now
        ))
        new_id = c.lastrowid
        c.execute('INSERT INTO tasks (source_id, text, done, created_at) VALUES (?, ?, 0, ?)', (new_id, 'Аудио на тайском', now))
        c.execute('INSERT INTO tasks (source_id, text, done, created_at) VALUES (?, ?, 0, ?)', (new_id, 'Опубликован на тайском', now))
        imported_count += 1

    conn.commit()
    conn.close()

    # Удаляем временный файл после импорта
    if os.path.exists(TEMP_FILE):
        os.remove(TEMP_FILE)

    return jsonify({'status': 'ok', 'imported': imported_count})


@import_bp.route('/api/import/cancel', methods=['POST'])
def cancel_import():
    if os.path.exists(TEMP_FILE):
        os.remove(TEMP_FILE)
    return jsonify({'status': 'ok'})
