import sqlite3
from contextlib import contextmanager
from config import DB_PATH


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    return conn


@contextmanager
def db_connection():
    conn = get_db_connection()

    try:
        yield conn
        
    finally:
        conn.close()