import os
import shutil
import sqlite3
from pathlib import Path
from typing import Optional, Union
from fastapi import APIRouter, File, HTTPException, Query, UploadFile, status
from pydantic import BaseModel, Field
from schemas.database import UpdateDatabase

from core.utility import sanitize_sql_for_sqlite
from database import (
    DATABASES_DIR,
    delete_database_record,
    get_active_database_info,
    get_active_database_path,
    get_sqlite_conn,
    list_registered_databases,
    register_database,
    update_database,
)

router = APIRouter(
    prefix="/database",
    tags=["database"],
    responses={404: {"description": "Not found"}},
)


def get_tables_for_conn(conn: sqlite3.Connection) -> list[str]:
    """Helper to discover all non-system table names in a SQLite connection."""
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
        return [row[0] for row in cur.fetchall()]
    finally:
        cur.close()


@router.post("/import")
async def import_database_file(
    file: UploadFile = File(
        ...,
        description="Imports an SQLite database (.db / .sqlite) or an SQL script (.sql)",
    ),
    is_active: bool = Query(
        False, description="Set this database as active default immediately"
    ),
):
    """Imports an SQLite database (.db / .sqlite) or an SQL script (.sql)"""
    filename = file.filename or ""
    suffix = Path(filename).suffix.lower()
    if file.size is not None and file.size > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail="Maximum allowed file size is 5 MB",
        )

    if suffix not in (".db", ".sqlite", ".sqlite3", ".sql"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{suffix}'. Please upload a .db, .sqlite, or .sql file.",
        )

    db_name = Path(filename).stem
    target_path = DATABASES_DIR / f"{db_name}.db"

    try:
        if suffix in (".db", ".sqlite", ".sqlite3"):
            # Write uploaded binary database file directly to databases/ directory
            with open(target_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

        elif suffix == ".sql":
            # Start from a clean database file if one already exists
            if target_path.exists():
                target_path.unlink()

            content = await file.read()
            sql_text = content.decode("utf-8", errors="replace")
            sanitized_sql = sanitize_sql_for_sqlite(sql_text)

            conn = get_sqlite_conn(target_path)
            try:
                conn.execute("PRAGMA foreign_keys = OFF")
                conn.executescript(sanitized_sql)
            finally:
                conn.close()

        # Register entry in app.db catalog without forcing default
        db_entry = register_database(db_name, status=1 if is_active else 0)
        if is_active:
            db_entry = update_database(db_name, status=1)
        # Inspect populated tables
        conn = get_sqlite_conn(target_path)
        try:
            tables = get_tables_for_conn(conn)
        finally:
            conn.close()

        return {
            "status": "success",
            "message": f"Successfully imported {filename} into databases/{db_name}.db",
            "database": {
                "id": db_entry["id"],
                "name": db_entry["name"],
                "filename": f"{db_entry['name']}.db",
                "is_default": bool(db_entry["is_default"]),
                "status": db_entry["status"],
            },
            "total_tables": len(tables),
            "tables": tables,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to import database: {str(e)}",
        )


@router.get("/list")
async def list_databases():
    """Returns all registered databases from app.db with table counts and active status for the frontend."""
    records = list_registered_databases()
    active_info = get_active_database_info()
    active_name = active_info["name"] if active_info else None
    result = []
    for rec in records:
        name = rec["name"]
        file_path = DATABASES_DIR / f"{name}.db"
        exists = file_path.exists()
        tables = []
        size_bytes = 0

        if exists:
            size_bytes = file_path.stat().st_size
            try:
                conn = get_sqlite_conn(file_path)
                tables = get_tables_for_conn(conn)
                conn.close()
            except Exception:
                tables = []

        result.append(
            {
                "id": rec["id"],
                "name": name,
                "filename": f"{name}.db",
                "is_default": bool(rec["is_default"]),
                "status": rec["status"],
                "size_bytes": size_bytes,
                "exists": exists,
                "total_tables": len(tables),
                "tables": tables,
            }
        )

    return {
        "active_database": active_name,
        "total_databases": len(result),
        "databases": result,
    }

@router.put("/{db_identifier}")
async def select_active_database(
    db_identifier: str, database: Optional[UpdateDatabase] = None
):
    """Updates database active status or default flags in registry."""
    is_default = database.is_default if database else None
    status_val = database.status if database else 1
    updated = update_database(db_identifier, is_default=is_default, status=status_val)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Database '{db_identifier}' not found in registry.",
        )

    file_path = DATABASES_DIR / f"{updated['name']}.db"
    return {
        "status": "success",
        "message": f"Database '{updated['name']}' updated successfully.",
        "database": {
            "id": updated["id"],
            "name": updated["name"],
            "filename": f"{updated['name']}.db",
            "is_default": bool(updated["is_default"]),
            "status": updated["status"],
            "exists": file_path.exists(),
        },
    }


@router.delete("/{db_identifier}")
async def delete_database(db_identifier: str):
    """Deletes a database from the registry and removes its physical file."""
    success, message = delete_database_record(db_identifier)
    if not success:
        if message == "not_found":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Database '{db_identifier}' not found.",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        )

    return {
        "status": "success",
        "message": f"Successfully deleted database '{db_identifier}'.",
    }


@router.get("/info")
async def get_database_info(
    db: Optional[str] = Query(None, description="Database name (defaults to active)")
):
    """Returns metadata and table summary of the specified or active SQLite database."""
    if db:
        target_path = DATABASES_DIR / f"{Path(db).stem}.db"
    else:
        target_path = get_active_database_path()

    if not target_path.exists():
        return {
            "database_file": str(target_path),
            "exists": False,
            "total_tables": 0,
            "tables": [],
        }

    conn = get_sqlite_conn(target_path)
    try:
        tables = get_tables_for_conn(conn)
        return {
            "database_file": str(target_path),
            "exists": True,
            "size_bytes": target_path.stat().st_size,
            "total_tables": len(tables),
            "tables": tables,
        }
    finally:
        conn.close()


@router.get("/tables")
async def list_tables_overview(
    db: Optional[str] = Query(None, description="Database name (defaults to active)")
):
    """Returns an overview of all tables in the specified or active database with row and column counts."""
    if db:
        target_path = DATABASES_DIR / f"{Path(db).stem}.db"
    else:
        target_path = get_active_database_path()

    if not target_path.exists():
        return {"total_tables": 0, "tables": []}

    conn = get_sqlite_conn(target_path)
    try:
        table_names = get_tables_for_conn(conn)
        cur = conn.cursor()
        tables_data = []
        for name in table_names:
            cur.execute(f'PRAGMA table_info("{name}")')
            col_count = len(cur.fetchall())
            cur.execute(f'SELECT COUNT(*) FROM "{name}"')
            row_count = cur.fetchone()[0]

            tables_data.append(
                {
                    "name": name,
                    "total_columns": col_count,
                    "total_rows": row_count,
                }
            )

        return {
            "database": target_path.stem,
            "total_tables": len(tables_data),
            "tables": tables_data,
        }
    finally:
        conn.close()


@router.get("/tables/{table_name}")
async def get_table_details(
    table_name: str,
    db: Optional[str] = Query(None, description="Database name (defaults to active)"),
):
    """Returns detailed structure for a given table including column definitions and row count."""
    if db:
        target_path = DATABASES_DIR / f"{Path(db).stem}.db"
    else:
        target_path = get_active_database_path()

    if not target_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Database file '{target_path.name}' does not exist.",
        )

    conn = get_sqlite_conn(target_path)
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND LOWER(name) = LOWER(?) AND name NOT LIKE 'sqlite_%'",
            (table_name,),
        )
        match = cur.fetchone()
        if not match:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Table '{table_name}' does not exist.",
            )

        actual_name = match[0]
        cur.execute(f'PRAGMA table_info("{actual_name}")')
        pragma_rows = cur.fetchall()

        columns = [
            {
                "name": row["name"],
                "type": row["type"] or "TEXT",
                "nullable": not bool(row["notnull"]),
                "primary_key": bool(row["pk"]),
                "default_value": row["dflt_value"],
            }
            for row in pragma_rows
        ]

        cur.execute(f'SELECT COUNT(*) FROM "{actual_name}"')
        row_count = cur.fetchone()[0]

        return {
            "database": target_path.stem,
            "table": actual_name,
            "total_rows": row_count,
            "total_columns": len(columns),
            "columns": columns,
        }
    finally:
        conn.close()
