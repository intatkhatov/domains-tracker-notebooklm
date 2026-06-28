import sqlite3
import os
from cryptography.fernet import Fernet

FARM_DB_PATH = '/app/data/farm.db'
FARM_KEY_PATH = '/app/data/.farm_key'
FARM_ENC_PATH = '/app/data/farm.db.enc'


def get_or_create_key():
    """Загружает ключ из файла или создаёт новый."""
    if os.path.exists(FARM_KEY_PATH):
        with open(FARM_KEY_PATH, 'rb') as f:
            return f.read()
    else:
        key = Fernet.generate_key()
        with open(FARM_KEY_PATH, 'wb') as f:
            f.write(key)
        os.chmod(FARM_KEY_PATH, 0o600)
        print('Farm: новый ключ шифрования создан.')
        return key


def encrypt_farm_db():
    """Шифрует farm.db -> farm.db.enc для бэкапа."""
    if not os.path.exists(FARM_DB_PATH):
        return
    key = get_or_create_key()
    f = Fernet(key)
    with open(FARM_DB_PATH, 'rb') as db_file:
        data = db_file.read()
    encrypted = f.encrypt(data)
    with open(FARM_ENC_PATH, 'wb') as enc_file:
        enc_file.write(encrypted)
    print('Farm: база зашифрована -> farm.db.enc')


def decrypt_farm_db():
    """Расшифровывает farm.db.enc -> farm.db при восстановлении."""
    if not os.path.exists(FARM_ENC_PATH):
        return
    if not os.path.exists(FARM_KEY_PATH):
        print('Farm: ключ не найден, расшифровка невозможна.')
        return
    key = get_or_create_key()
    f = Fernet(key)
    with open(FARM_ENC_PATH, 'rb') as enc_file:
        encrypted = enc_file.read()
    data = f.decrypt(encrypted)
    with open(FARM_DB_PATH, 'wb') as db_file:
        db_file.write(data)
    print('Farm: база расшифрована -> farm.db')


def get_farm_db():
    conn = sqlite3.connect(FARM_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_farm_db():
    """Инициализирует таблицу farm при старте."""
    # Если есть зашифрованный файл, но нет расшифрованного — восстанавливаем
    if not os.path.exists(FARM_DB_PATH) and os.path.exists(FARM_ENC_PATH):
        decrypt_farm_db()

    conn = get_farm_db()
    c = conn.cursor()
    c.executescript('''
        CREATE TABLE IF NOT EXISTS farm (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            number INTEGER,
            name TEXT,
            day INTEGER,
            month TEXT,
            year INTEGER,
            gender TEXT DEFAULT 'Не указан',
            email TEXT,
            password TEXT,
            lost INTEGER DEFAULT 0,
            loss_reason TEXT
        );
    ''')
    conn.commit()
    conn.close()
    print('Farm DB инициализирована.')
