import sqlite3
import json
import os

DB_PATH = '/app/data/tracker.db'
JSON_PATH = '/app/data/rating_domains_with_sources.json'


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    c = conn.cursor()

    c.executescript('''
        CREATE TABLE IF NOT EXISTS domains (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rank INTEGER UNIQUE,
            name TEXT NOT NULL,
            defense TEXT,
            intersections INTEGER
        );

        CREATE TABLE IF NOT EXISTS sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            domain_rank INTEGER NOT NULL,
            source_id TEXT NOT NULL,
            short_name TEXT NOT NULL,
            citation TEXT NOT NULL,
            original_language TEXT,
            original_lost INTEGER DEFAULT 0,
            authoritative_translation_language TEXT,
            notebook_url TEXT,
            processed INTEGER DEFAULT 0,
            FOREIGN KEY (domain_rank) REFERENCES domains(rank)
        );
    ''')

    # Миграция: добавляем relisten если нет
    try:
        c.execute('ALTER TABLE sources ADD COLUMN relisten INTEGER DEFAULT 0')
        conn.commit()
        print('Migration: relisten column added.')
    except Exception:
        pass

    conn.commit()

    # Загружаем данные из JSON если таблицы пустые
    c.execute('SELECT COUNT(*) FROM domains')
    if c.fetchone()[0] == 0:
        with open(JSON_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)

        for domain in data:
            c.execute(
                'INSERT OR IGNORE INTO domains (rank, name, defense, intersections) VALUES (?, ?, ?, ?)',
                (domain['rank'], domain['domain'], domain.get('defense', ''), domain.get('intersections', 0))
            )
            for source in domain['sources']:
                c.execute('''
                    INSERT OR IGNORE INTO sources
                    (domain_rank, source_id, short_name, citation, original_language, original_lost, authoritative_translation_language)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    domain['rank'],
                    source.get('id', ''),
                    source.get('short_name', ''),
                    source.get('citation', ''),
                    source.get('original_language', ''),
                    1 if source.get('original_lost') else 0,
                    source.get('authoritative_translation_language', '')
                ))

        conn.commit()
        print('Database initialized from JSON.')
    else:
        print('Database already exists, skipping import.')

    conn.close()
