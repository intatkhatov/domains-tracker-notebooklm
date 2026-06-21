import sqlite3

DB_PATH = '/app/data/tracker.db'
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

c.execute("PRAGMA table_info(sources)")
cols = [r[1] for r in c.fetchall()]

if 'rating' not in cols:
    c.execute('ALTER TABLE sources ADD COLUMN rating INTEGER')
    print('Column rating added.')
else:
    print('Column rating already exists.')

if 'comment' not in cols:
    c.execute('ALTER TABLE sources ADD COLUMN comment TEXT')
    print('Column comment added.')
else:
    print('Column comment already exists.')

conn.commit()
conn.close()
print('Migration complete.')
