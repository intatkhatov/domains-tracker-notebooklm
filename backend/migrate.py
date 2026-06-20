import sqlite3

DB_PATH = '/app/data/tracker.db'

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
c = conn.cursor()

# 1. Добавляем колонку listened, если её ещё нет
c.execute("PRAGMA table_info(sources)")
cols = [r['name'] for r in c.fetchall()]
if 'listened' not in cols:
    c.execute('ALTER TABLE sources ADD COLUMN listened INTEGER DEFAULT 0')
    print('Column listened added.')
else:
    print('Column listened already exists.')

conn.commit()

# 2. Дедупликация по citation
c.execute('SELECT * FROM sources')
rows = [dict(r) for r in c.fetchall()]
print(f'Total rows before dedup: {len(rows)}')

groups = {}
for r in rows:
    groups.setdefault(r['citation'], []).append(r)

to_keep = []
to_delete_ids = []

for citation, group in groups.items():
    if len(group) == 1:
        to_keep.append(group[0])
        continue
    # приоритет: processed=1 или notebook_url не пустой
    priority = [r for r in group if r['processed'] == 1 or (r['notebook_url'] and r['notebook_url'].strip())]
    keeper = priority[0] if priority else group[0]
    to_keep.append(keeper)
    for r in group:
        if r['id'] != keeper['id']:
            to_delete_ids.append(r['id'])

print(f'Unique citations: {len(groups)}')
print(f'Rows to delete: {len(to_delete_ids)}')

for sid in to_delete_ids:
    c.execute('DELETE FROM sources WHERE id=?', (sid,))

conn.commit()

# 3. Пересчитываем простые ID (source_id) по порядку id записи
c.execute('SELECT id FROM sources ORDER BY id')
remaining = c.fetchall()
for idx, row in enumerate(remaining, 1):
    c.execute('UPDATE sources SET source_id=? WHERE id=?', (str(idx), row['id']))

conn.commit()

c.execute('SELECT COUNT(*) as cnt FROM sources')
print(f'Total rows after dedup: {c.fetchone()["cnt"]}')

conn.close()
print('Migration complete.')
