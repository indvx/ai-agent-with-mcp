import re

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
    sql = sql.replace(r"\"", '"')

    # Strip character set introducers: _utf8mb4 'text' -> 'text'
    sql = re.sub(
        r"\b_(?:utf8mb4|utf8|latin1|binary)\s*'", "'", sql, flags=re.IGNORECASE
    )

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
            body = re.sub(
                r",\s*PRIMARY\s+KEY\s*\([^)]+\)", "", body, flags=re.IGNORECASE
            )

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

        # Strip column-level comments: COMMENT '...' or COMMENT "..."
        body = re.sub(
            r"\bCOMMENT\s+(?:'(?:''|[^'])*'|\"(?:\"\"|[^\"])*\")",
            "",
            body,
            flags=re.IGNORECASE,
        )

        # Strip MySQL ON UPDATE CURRENT_TIMESTAMP clause
        body = re.sub(
            r"\bON\s+UPDATE\s+CURRENT_TIMESTAMP(?:\(\))?",
            "",
            body,
            flags=re.IGNORECASE,
        )

        # Normalize CURRENT_TIMESTAMP() call to standard CURRENT_TIMESTAMP keyword
        body = re.sub(
            r"\bCURRENT_TIMESTAMP\(\)",
            "CURRENT_TIMESTAMP",
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
        body = re.sub(r"\b(?:UNSIGNED|ZEROFILL)\b", "", body, flags=re.IGNORECASE)

        # Normalize data types to SQLite affinities
        body = re.sub(
            r"\b(?:TINY|SMALL|MEDIUM|BIG)?INT(?:\(\d+\))?(?:\s+UNSIGNED)?\b",
            "INTEGER",
            body,
            flags=re.IGNORECASE,
        )
        body = re.sub(
            r"\b(?:VARCHAR|CHAR)(?:\(\d+\))?\b", "TEXT", body, flags=re.IGNORECASE
        )
        body = re.sub(
            r"\b(?:LONG|MEDIUM|TINY)?TEXT\b", "TEXT", body, flags=re.IGNORECASE
        )
        body = re.sub(
            r"\b(?:LONG|MEDIUM|TINY)?BLOB\b", "BLOB", body, flags=re.IGNORECASE
        )
        body = re.sub(r"\b(?:ENUM|SET)\s*\([^)]+\)", "TEXT", body, flags=re.IGNORECASE)
        body = re.sub(r"\bDOUBLE(?:\(\d+,\d+\))?\b", "REAL", body, flags=re.IGNORECASE)
        body = re.sub(r"\bFLOAT(?:\(\d+,\d+\))?\b", "REAL", body, flags=re.IGNORECASE)
        body = re.sub(r"\bDATETIME(?:\(\d+\))?\b", "TEXT", body, flags=re.IGNORECASE)
        body = re.sub(r"\bTIMESTAMP(?:\(\d+\))?\b", "TEXT", body, flags=re.IGNORECASE)

        # Clean trailing commas before the closing parenthesis
        body = re.sub(r",\s*\)", "\n)", body)

        return body

    sql = re.sub(
        r"CREATE\s+TABLE[\s\S]*?;", fix_create_table, sql, flags=re.IGNORECASE
    )

    # Auto-create tables targeted by INSERT statements if their CREATE TABLE was omitted in the dump
    created_tables = set(
        re.findall(
            r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?[\"`\[]?(\w+)[\"`\]]?",
            sql,
            re.IGNORECASE,
        )
    )
    insert_pattern = re.compile(
        r"INSERT\s+INTO\s+[\"`\[]?(\w+)[\"`\]]?\s*\(([^)]+)\)",
        re.IGNORECASE,
    )
    missing_tables = {}
    for tbl, cols_str in insert_pattern.findall(sql):
        if tbl not in created_tables and tbl not in missing_tables:
            cols = [c.strip().strip('"`[]') for c in cols_str.split(",") if c.strip()]
            col_defs = ", ".join(
                [f'"{c}" INTEGER PRIMARY KEY' if c.lower() == "id" else f'"{c}" TEXT' for c in cols]
            )
            missing_tables[tbl] = f'CREATE TABLE IF NOT EXISTS "{tbl}" ({col_defs});'

    if missing_tables:
        sql = "\n".join(missing_tables.values()) + "\n" + sql

    # Disable foreign key enforcement during batch dump restore
    return "PRAGMA foreign_keys = OFF;\n" + sql