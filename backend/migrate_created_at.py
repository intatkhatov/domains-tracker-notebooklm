import sqlite3
from datetime import datetime, timezone

DB_PATH = '/app/data/tracker.db'
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

c.execute("PRAGMA table_info(sources)")
cols = [r[1] for r in c.fetchall()]

if 'created_at' not in cols:
    c.execute('ALTER TABLE sources ADD COLUMN created_at TEXT')
    print('Column created_at added.')
else:
    print('Column created_at already exists.')

now = datetime.now(timezone.utc).isoformat()
c.execute('UPDATE sources SET created_at = ? WHERE created_at IS NULL', (now,))
conn.commit()

c.execute('SELECT COUNT(*) FROM sources WHERE created_at IS NOT NULL')
print(f'Rows with created_at set: {c.fetchone()[0]}')

conn.close()
print('Migration complete.')
