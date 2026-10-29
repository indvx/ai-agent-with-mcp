import os
import sqlite3
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", "app.db")


def get_sqlite_conn(db_path: str = None) -> sqlite3.Connection:
    """Returns a connection to the active SQLite database with dictionary rows enabled."""
    path = db_path or os.getenv("SQLITE_DB_PATH", "app.db")
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn
