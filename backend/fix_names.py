import sqlite3
import re

DB_PATH = '/app/data/tracker.db'
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
c = conn.cursor()

c.execute('SELECT id, source_id, short_name FROM sources')
rows = c.fetchall()

updated = 0
for r in rows:
    new_name = re.sub(r'^\d+\.\d+\.\s*', '', r['short_name'])
    new_name = f"{r['source_id']}. {new_name}"
    if new_name != r['short_name']:
        c.execute('UPDATE sources SET short_name=? WHERE id=?', (new_name, r['id']))
        updated += 1

conn.commit()
print(f'Updated {updated} of {len(rows)} rows.')
conn.close()
