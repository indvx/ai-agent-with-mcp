import os
import sqlite3
from pathlib import Path
from typing import Optional, Union
from dotenv import load_dotenv

load_dotenv()

SYSTEM_DB_PATH = Path(os.getenv("SYSTEM_DB_PATH", "app.db"))
DATABASES_DIR = Path(os.getenv("DATABASES_DIR", "databases"))


def init_system_db() -> None:
    """Ensures app.db exists and initializes the databases catalog table."""
    DATABASES_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(SYSTEM_DB_PATH)
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS databases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                is_default INTEGER NOT NULL DEFAULT 0,
                status INTEGER NOT NULL DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
        conn.commit()
    finally:
        conn.close()


# Ensure catalog table is ready at import time
init_system_db()


def get_system_conn() -> sqlite3.Connection:
    """Returns a connection to the system metadata database (app.db)."""
    conn = sqlite3.connect(SYSTEM_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def register_database(name: str, status: int = 1) -> dict:
    """Registers or updates a database entry in app.db, keeping is_default = 0."""
    clean_name = Path(name).stem
    conn = get_system_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO databases (name, is_default, status)
            VALUES (?, 0, ?)
            ON CONFLICT(name) DO UPDATE SET
                status = excluded.status
            """,
            (clean_name, status),
        )
        conn.commit()

        cur.execute(
            "SELECT id, name, is_default, status, created_at FROM databases WHERE name = ?",
            (clean_name,),
        )
        row = cur.fetchone()
        return dict(row)
    finally:
        cur.close()
        conn.close()


def update_database(
    identifier: Union[str, int],
    is_default: Optional[bool] = None,
    status: Optional[int] = None,
) -> Optional[dict]:
    """Updates database flags in app.db."""
    conn = get_system_conn()
    cur = conn.cursor()
    try:
        if str(identifier).isdigit():
            cur.execute(
                "SELECT id, name, is_default, status FROM databases WHERE id = ?",
                (int(identifier),),
            )
        else:
            clean_name = Path(str(identifier)).stem
            cur.execute(
                "SELECT id, name, is_default, status FROM databases WHERE LOWER(name) = LOWER(?)",
                (clean_name,),
            )

        target = cur.fetchone()
        if not target:
            return None

        target_id = target["id"]

        if is_default is True:
            cur.execute("UPDATE databases SET is_default = 0")
            cur.execute("UPDATE databases SET is_default = 1 WHERE id = ?", (target_id,))
        elif is_default is False and not bool(target["is_default"]):
            cur.execute("UPDATE databases SET is_default = 0 WHERE id = ?", (target_id,))

        if status is not None:
            if status == 1:
                cur.execute("UPDATE databases SET status = 0")
            cur.execute("UPDATE databases SET status = ? WHERE id = ?", (status, target_id))

        conn.commit()

        cur.execute(
            "SELECT id, name, is_default, status, created_at FROM databases WHERE id = ?",
            (target_id,),
        )
        row = cur.fetchone()
        return dict(row)
    finally:
        cur.close()
        conn.close()


def get_active_database_info() -> Optional[dict]:
    """Returns the catalog record of the currently active default database."""
    conn = get_system_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT id, name, is_default, status, created_at FROM databases WHERE status=1 LIMIT 1"
        )
        row = cur.fetchone()
        if row:
            return dict(row)

        # Fallback to the latest database if none is explicitly marked default
        cur.execute(
            "SELECT id, name, is_default, status, created_at FROM databases WHERE is_default = 1 ORDER BY id DESC LIMIT 1"
        )
        fallback = cur.fetchone()
        return dict(fallback) if fallback else None
    finally:
        cur.close()
        conn.close()


def get_active_database_path() -> Path:
    """Returns the resolved file path for the active database in databases/."""
    active_info = get_active_database_info()
    if active_info:
        db_path = DATABASES_DIR / f"{active_info['name']}.db"
        if db_path.exists():
            return db_path

    # Check for any existing database in databases/
    existing = list(DATABASES_DIR.glob("*.db"))
    if existing:
        return existing[0]

    return SYSTEM_DB_PATH


def list_registered_databases() -> list[dict]:
    """Returns all database entries registered in the app.db catalog."""
    conn = get_system_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT id, name, is_default, status, created_at FROM databases ORDER BY is_default DESC, id DESC"
        )
        return [dict(row) for row in cur.fetchall()]
    finally:
        cur.close()
        conn.close()


def delete_database_record(identifier: Union[str, int]) -> tuple[bool, str]:
    """Removes a database record from app.db and deletes its file from databases/."""
    conn = get_system_conn()
    cur = conn.cursor()
    try:
        if str(identifier).isdigit():
            cur.execute(
                "SELECT id, name, is_default FROM databases WHERE id = ?", (int(identifier),)
            )
        else:
            clean_name = Path(str(identifier)).stem
            cur.execute(
                "SELECT id, name, is_default FROM databases WHERE LOWER(name) = LOWER(?)",
                (clean_name,),
            )

        target = cur.fetchone()
        if not target:
            return False, "not_found"

        if bool(target["is_default"]):
            return False, "Predefined default database cannot be deleted."

        target_name = target["name"]
        cur.execute("DELETE FROM databases WHERE id = ?", (target["id"],))
        conn.commit()

        # Remove physical database file if it exists
        file_path = DATABASES_DIR / f"{target_name}.db"
        if file_path.exists():
            file_path.unlink()

        return True, "success"
    finally:
        cur.close()
        conn.close()


def get_sqlite_conn(db_identifier: Union[str, Path] = None) -> sqlite3.Connection:
    """Returns a connection to the specified database or the active default database."""
    if db_identifier:
        path = Path(db_identifier)
        if not path.is_file():
            # If a simple name like 'world' or 'world.db' was passed, resolve in databases/
            clean_name = path.stem
            candidate = DATABASES_DIR / f"{clean_name}.db"
            path = candidate if candidate.exists() else path
    else:
        env_path = os.getenv("SQLITE_DB_PATH")
        if env_path and Path(env_path).exists():
            path = Path(env_path)
        else:
            path = get_active_database_path()

    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn
