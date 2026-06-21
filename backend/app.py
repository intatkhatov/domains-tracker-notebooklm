from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from database import get_db, init_db
from similarity import check_duplicates
from import_module import import_bp
from datetime import datetime, timezone

app = Flask(__name__, static_folder='/app/frontend', static_url_path='')
CORS(app)
app.register_blueprint(import_bp)

init_db()


@app.route('/')
def index():
    return send_from_directory('/app/frontend', 'index.html')


@app.route('/import.html')
def import_page():
    return send_from_directory('/app/frontend', 'import.html')


@app.route('/api/domains', methods=['GET'])
def get_domains():
    conn = get_db()
    domains = conn.execute('SELECT * FROM domains ORDER BY rank').fetchall()
    result = []
    for d in domains:
        sources = conn.execute(
            'SELECT * FROM sources WHERE domain_rank = ? ORDER BY CAST(source_id AS INTEGER)',
            (d['rank'],)
        ).fetchall()
        result.append({
            'id': d['id'],
            'rank': d['rank'],
            'name': d['name'],
            'defense': d['defense'],
            'intersections': d['intersections'],
            'sources': [dict(s) for s in sources]
        })
    conn.close()
    return jsonify(result)


@app.route('/api/sources/check-duplicate', methods=['POST'])
def check_duplicate_route():
    data = request.json
    citation = (data or {}).get('citation', '').strip()
    if not citation:
        return jsonify({'matches': []})

    conn = get_db()
    rows = conn.execute('SELECT id, short_name, citation FROM sources').fetchall()
    conn.close()

    existing = [dict(r) for r in rows]
    matches = check_duplicates(citation, existing)
    return jsonify({'matches': matches})


@app.route('/api/sources', methods=['POST'])
def add_source():
    data = request.json
    conn = get_db()
    c = conn.cursor()

    # Находим максимальный существующий номер (как число) и берём следующий
    c.execute('SELECT source_id FROM sources')
    existing = [r['source_id'] for r in c.fetchall()]
    max_num = 0
    for sid in existing:
        try:
            n = int(sid)
            if n > max_num:
                max_num = n
        except (ValueError, TypeError):
            pass
    next_id = max_num + 1

    raw_name = (data.get('short_name') or '').strip()
    short_name = f"{next_id}. {raw_name}" if raw_name else f"{next_id}."
    now = datetime.now(timezone.utc).isoformat()

    c.execute('''
        INSERT INTO sources
        (domain_rank, source_id, short_name, citation, original_language, original_lost, authoritative_translation_language, notebook_url, processed, listened, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data.get('domain_rank', 1),
        str(next_id),
        short_name,
        data['citation'],
        data.get('original_language', ''),
        1 if data.get('original_lost') else 0,
        data.get('authoritative_translation_language', ''),
        data.get('notebook_url', ''),
        0,
        0,
        now
    ))
    new_id = c.lastrowid
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok', 'id': new_id})


@app.route('/api/sources/<int:source_id>', methods=['PUT'])
def update_source(source_id):
    data = request.json
    conn = get_db()
    conn.execute('''
        UPDATE sources SET
            short_name=?,
            citation=?,
            original_language=?,
            original_lost=?,
            authoritative_translation_language=?,
            notebook_url=?,
            processed=?,
            listened=?
        WHERE id=?
    ''', (
        data['short_name'],
        data['citation'],
        data.get('original_language', ''),
        1 if data.get('original_lost') else 0,
        data.get('authoritative_translation_language', ''),
        data.get('notebook_url', ''),
        1 if data.get('processed') else 0,
        1 if data.get('listened') else 0,
        source_id
    ))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})


@app.route('/api/sources/<int:source_id>', methods=['DELETE'])
def delete_source(source_id):
    conn = get_db()
    conn.execute('DELETE FROM sources WHERE id=?', (source_id,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})


@app.route('/api/sources/<int:source_id>/processed', methods=['PATCH'])
def toggle_processed(source_id):
    data = request.json
    conn = get_db()
    conn.execute(
        'UPDATE sources SET processed=? WHERE id=?',
        (1 if data.get('processed') else 0, source_id)
    )
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})


@app.route('/api/sources/<int:source_id>/listened', methods=['PATCH'])
def toggle_listened(source_id):
    data = request.json
    conn = get_db()
    conn.execute(
        'UPDATE sources SET listened=? WHERE id=?',
        (1 if data.get('listened') else 0, source_id)
    )
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})


@app.route('/api/sources/<int:source_id>/rating', methods=['PATCH'])
def update_rating(source_id):
    data = request.json
    rating = data.get('rating')
    if rating is not None:
        rating = int(rating)
        if rating < 1 or rating > 10:
            return jsonify({'error': 'Оценка должна быть от 1 до 10'}), 400
    conn = get_db()
    conn.execute(
        'UPDATE sources SET rating=? WHERE id=?',
        (rating, source_id)
    )
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})


@app.route('/api/sources/<int:source_id>/comment', methods=['PATCH'])
def update_comment(source_id):
    data = request.json
    comment = (data.get('comment') or '').strip()
    conn = get_db()
    conn.execute(
        'UPDATE sources SET comment=? WHERE id=?',
        (comment if comment else None, source_id)
    )
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})


@app.route('/api/sources/<int:source_id>/notebook', methods=['PATCH'])
def update_notebook(source_id):
    data = request.json
    conn = get_db()
    conn.execute(
        'UPDATE sources SET notebook_url=? WHERE id=?',
        (data.get('notebook_url', ''), source_id)
    )
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5051, debug=False)
