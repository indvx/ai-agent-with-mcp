import os
import re
import shutil
import sqlite3
from pathlib import Path
from fastapi import APIRouter, File, HTTPException, UploadFile, status

from database import SQLITE_DB_PATH, get_sqlite_conn

router = APIRouter(
    prefix="/database",
    tags=["database"],
    responses={404: {"description": "Not found"}},
)


def sanitize_sql_for_sqlite(sql: str) -> str:
    """Translates SQL dumps (e.g. MySQL mysqldump) into SQLite-compatible DDL and DML."""
    # Strip MySQL conditional comments (/*!40101 ... */;) and standard block comments
    sql = re.sub(r"/\*![\s\S]*?\*/;?", "", sql)
    sql = re.sub(r"/\*[\s\S]*?\*/;?", "", sql)

    out_lines = []
    for line in sql.splitlines():
        trimmed = line.strip()
        # Skip comment lines (-- or #) and empty lines
        if not trimmed or trimmed.startswith("--") or trimmed.startswith("#"):
            continue
        # Skip MySQL session variable assignments and table lock directives
        if re.match(r"^(SET|LOCK\s+TABLES|UNLOCK\s+TABLES)\b", trimmed, re.IGNORECASE):
            continue
        out_lines.append(line)

    sql = "\n".join(out_lines)

    # Convert MySQL backslash quote escaping (\' -> '') to standard SQLite string escaping
    sql = sql.replace(r"\'", "''")
    sql = sql.replace(r'\"', '"')

    # Strip character set introducers: _utf8mb4 'text' -> 'text'
    sql = re.sub(r"\b_(?:utf8mb4|utf8|latin1|binary)\s*'", "'", sql, flags=re.IGNORECASE)

    def fix_create_table(match):
        body = match.group(0)

        # Strip table options after closing parenthesis: ') ENGINE=... DEFAULT CHARSET=...;' -> ');'
        body = re.sub(
            r"\)\s*(?:ENGINE|DEFAULT\s+CHARSET|CHARSET|COLLATE|AUTO_INCREMENT|ROW_FORMAT|COMMENT)[^;]*;",
            ");",
            body,
            flags=re.IGNORECASE,
        )

        # Convert AUTO_INCREMENT column to SQLite INTEGER PRIMARY KEY AUTOINCREMENT
        has_auto_inc = bool(re.search(r"\bAUTO_INCREMENT\b", body, re.IGNORECASE))
        if has_auto_inc:
            body = re.sub(
                r'([`"\[]?\w+[`"\]]?)\s+(?:(?:TINY|SMALL|MEDIUM|BIG)?INT(?:\(\d+\))?)\s*(?:UNSIGNED\s*)?(?:NOT\s+NULL\s*)?AUTO_INCREMENT',
                r"\1 INTEGER PRIMARY KEY AUTOINCREMENT",
                body,
                flags=re.IGNORECASE,
            )
            # Remove redundant table-level PRIMARY KEY definition if converted at column level
            body = re.sub(r",\s*PRIMARY\s+KEY\s*\([^)]+\)", "", body, flags=re.IGNORECASE)

        # Remove secondary index definitions inside CREATE TABLE
        body = re.sub(
            r",\s*(?:FULLTEXT\s+|SPATIAL\s+)?KEY\s+[`\"\[]?\w+[`\"\]]?\s*\([^)]+\)",
            "",
            body,
            flags=re.IGNORECASE,
        )
        body = re.sub(
            r",\s*INDEX\s+[`\"\[]?\w+[`\"\]]?\s*\([^)]+\)",
            "",
            body,
            flags=re.IGNORECASE,
        )
        body = re.sub(
            r"\bUNIQUE\s+KEY\s+[`\"\[]?\w+[`\"\]]?\s*(\([^)]+\))",
            r"UNIQUE \1",
            body,
            flags=re.IGNORECASE,
        )

        # Strip column collations and character sets not supported by SQLite
        body = re.sub(r"\bCOLLATE\s+[a-zA-Z0-9_]+\b", "", body, flags=re.IGNORECASE)
        body = re.sub(
            r"\b(?:DEFAULT\s+)?(?:CHARACTER\s+SET|CHARSET)\s+[a-zA-Z0-9_]+\b",
            "",
            body,
            flags=re.IGNORECASE,
        )

        # Normalize data types to SQLite affinities
        body = re.sub(
            r"\b(?:TINY|SMALL|MEDIUM|BIG)?INT(?:\(\d+\))?(?:\s+UNSIGNED)?\b",
            "INTEGER",
            body,
            flags=re.IGNORECASE,
        )
        body = re.sub(r"\b(?:VARCHAR|CHAR)(?:\(\d+\))?\b", "TEXT", body, flags=re.IGNORECASE)
        body = re.sub(r"\b(?:LONG|MEDIUM|TINY)?TEXT\b", "TEXT", body, flags=re.IGNORECASE)
        body = re.sub(r"\b(?:LONG|MEDIUM|TINY)?BLOB\b", "BLOB", body, flags=re.IGNORECASE)
        body = re.sub(r"\b(?:ENUM|SET)\s*\([^)]+\)", "TEXT", body, flags=re.IGNORECASE)
        body = re.sub(r"\bDOUBLE(?:\(\d+,\d+\))?\b", "REAL", body, flags=re.IGNORECASE)
        body = re.sub(r"\bFLOAT(?:\(\d+,\d+\))?\b", "REAL", body, flags=re.IGNORECASE)
        body = re.sub(r"\bDATETIME(?:\(\d+\))?\b", "TEXT", body, flags=re.IGNORECASE)
        body = re.sub(r"\bTIMESTAMP(?:\(\d+\))?\b", "TEXT", body, flags=re.IGNORECASE)

        # Clean trailing commas before the closing parenthesis
        body = re.sub(r",\s*\)", "\n)", body)

        return body

    return re.sub(r"CREATE\s+TABLE[\s\S]*?;", fix_create_table, sql, flags=re.IGNORECASE)


@router.post("/import")
async def import_database_file(file: UploadFile = File(...)):
    """Imports an SQLite database (.db / .sqlite) or an SQL script (.sql) into the active database."""
    filename = file.filename or ""
    suffix = Path(filename).suffix.lower()

    if suffix not in (".db", ".sqlite", ".sqlite3", ".sql"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{suffix}'. Please upload a .db, .sqlite, or .sql file.",
        )

    target_path = Path(os.getenv("SQLITE_DB_PATH", "app.db"))

    try:
        if suffix in (".db", ".sqlite", ".sqlite3"):
            # Write the uploaded binary database file directly to target_path
            with open(target_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

        elif suffix == ".sql":
            # Sanitize and execute SQL script to support both SQLite and MySQL dump dialects
            content = await file.read()
            sql_text = content.decode("utf-8", errors="replace")
            sanitized_sql = sanitize_sql_for_sqlite(sql_text)

            conn = get_sqlite_conn(str(target_path))
            try:
                conn.executescript(sanitized_sql)
            finally:
                conn.close()

        # Verify tables in the newly populated database
        conn = get_sqlite_conn(str(target_path))
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
            )
            tables = [row[0] for row in cur.fetchall()]
        finally:
            conn.close()

        return {
            "status": "success",
            "message": f"Successfully imported {filename}",
            "database_file": str(target_path),
            "total_tables": len(tables),
            "tables": tables,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to import database: {str(e)}",
        )


@router.get("/info")
async def get_database_info():
    """Returns metadata and table summary of the currently active SQLite database."""
    target_path = Path(os.getenv("SQLITE_DB_PATH", "app.db"))

    if not target_path.exists():
        return {
            "database_file": str(target_path),
            "exists": False,
            "total_tables": 0,
            "tables": [],
        }

    conn = get_sqlite_conn(str(target_path))
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
        tables = [row[0] for row in cur.fetchall()]
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
async def list_tables_overview():
    """Returns a list of all tables in the active database with column and row counts."""
    target_path = Path(os.getenv("SQLITE_DB_PATH", "app.db"))

    if not target_path.exists():
        return {"total_tables": 0, "tables": []}

    conn = get_sqlite_conn(str(target_path))
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
        table_names = [row[0] for row in cur.fetchall()]

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
            "total_tables": len(tables_data),
            "tables": tables_data,
        }
    finally:
        conn.close()


@router.get("/tables/{table_name}")
async def get_table_details_endpoint(table_name: str):
    """Returns detailed structure for a given table including column definitions and row count."""
    target_path = Path(os.getenv("SQLITE_DB_PATH", "app.db"))

    if not target_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Table '{table_name}' does not exist.",
        )

    conn = get_sqlite_conn(str(target_path))
    try:
        cur = conn.cursor()
        # Find exact case-insensitive table name
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
            "table": actual_name,
            "total_rows": row_count,
            "total_columns": len(columns),
            "columns": columns,
        }
    finally:
        conn.close()
