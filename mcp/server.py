from mcp.server.fastmcp import FastMCP
from typing import Optional
import sys
from dotenv import load_dotenv
import mysql.connector
import os

load_dotenv()


mcp = FastMCP(
    "mysql-test",
    host=os.getenv("MCP_HOST"),
    port=os.getenv("MCP_PORT"),
)


def get_conn():
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST"),
        port=os.getenv("MYSQL_PORT"),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DATABASE"),
    )


def success_response(data):
    return {
        "success": True,
        "data": data,
    }


def error_response(message, **kwargs):
    return {
        "success": False,
        "error": message,
        **kwargs,
    }


@mcp.tool(description="Count records in a table")
def count_records_table(
    table: str,
    field: Optional[str] = None,
    value: Optional[str] = None,
    desc: bool = False,
):

    try:
        print(f"Counting records in table {table}")
        print("field", field)
        conn = get_conn()
        validation = validate_table(table)
        if validation:
            return validation

        cur = conn.cursor()
        matched_field = None
        if field:
            fields = get_fields(table)
            matched_field = [f for f in fields if field in f["COLUMN_NAME"]]
            if not matched_field:
                return error_response(f"Field '{field}' not found in table '{table}'")

            query = f"""
                SELECT COUNT(*) FROM {table} WHERE {matched_field[0]['COLUMN_NAME']} like %s
            """
        else:
            query = f"""
                SELECT COUNT(*) FROM {table}
            """

        if desc:
            matched_field = matched_field or [{"COLUMN_NAME": "id"}]
            query += " ORDER BY " + matched_field[0]["COLUMN_NAME"] + " DESC"

        cur.execute(query, (f"%{value}%",) if field else None)
        result = cur.fetchone()
        conn.close()

        return success_response(
            {
                "table": table,
                "count": result[0],
            }
        )
    except Exception as e:
        print(f"Error counting records: {e}")
        return error_response(f"Error counting records: {e}")


@mcp.tool(description="List records from a table")
def list_records(
    table: str,
    field: Optional[str] = None,
    value: Optional[str] = None,
    limit: int = 1,
    desc: bool = False,
):
    try:
        print("listing_records", "table", table)
        print("field", field)
        print("value", value)
        print("limit", limit)
        print("desc", desc)
        conn = get_conn()
        validation = validate_table(table)
        if validation:
            return validation

        cur = conn.cursor(dictionary=True)
        matched_field = None
        if field:
            fields = get_fields(table)
            matched_field = [f for f in fields if field in f["COLUMN_NAME"]]
            if not matched_field:
                return error_response(f"Field '{field}' not found in table '{table}'")
            query = (
                f"SELECT * FROM {table} WHERE {matched_field[0]['COLUMN_NAME']} like %s"
            )
        else:
            query = f"SELECT * FROM {table}"

        matched_field = matched_field or [{"COLUMN_NAME": "id"}]
        query += (
            " ORDER BY "
            + matched_field[0]["COLUMN_NAME"]
            + (" DESC" if desc else " ASC")
        )

        if limit is not None:
            query += f" limit {limit}"

        cur.execute(query, (f"%{value}%",) if field else None)

        rows = cur.fetchall()

        conn.close()
        print(f"Listing records {len(rows)} from table {table} successfully")
        return success_response(rows)
    except Exception as e:
        print(f"Error listing records: {e}")
        return error_response(f"Error listing records: {e}")


@mcp.tool(description="Count all tables in the database")
def count_all_tables():
    print("Getting tables")
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = %s
    """,
        (os.getenv("MYSQL_DATABASE"),),
    )

    tables = [row[0] for row in cur.fetchall()]

    conn.close()
    return success_response(tables)


@mcp.tool(description="Get table names")
def get_table_names():
    try:
        print("Getting tables")
        conn = get_conn()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = %s
        """,
            (os.getenv("MYSQL_DATABASE"),),
        )

        tables = [row[0] for row in cur.fetchall()]

        conn.close()
        return success_response(tables)
    except Exception as e:
        print(f"Error getting tables: {e}")
        return error_response(f"Error getting tables: {e}")


@mcp.tool(description="Get fields of a table")
def get_fields(table: str):
    try:
        print(f"Gettting fields of the {table} table")
        conn = get_conn()
        validation = validate_table(table)
        if validation:
            return validation
        cur = conn.cursor(dictionary=True)

        cur.execute(
            """
            SELECT
                column_name,
                data_type,
                is_nullable,
                column_key
            FROM information_schema.columns
            WHERE table_schema = %s
            AND table_name = %s
        """,
            (os.getenv("MYSQL_DATABASE"), table),
        )

        fields = cur.fetchall()

        conn.close()

        return success_response(fields)
    except Exception as e:
        print(f"Error getting fields: {e}")
        return error_response(f"Error getting fields: {e}")


@mcp.tool(description="Count fields of a table")
def count_fields(table: str):
    try:
        print(f"Counting fields of the {table} table")
        conn = get_conn()
        validation = validate_table(table)
        if validation:
            return validation

        cur = conn.cursor(dictionary=True)

        cur.execute(
            """
            SELECT
                column_name,
                data_type,
                is_nullable,
                column_key
            FROM information_schema.columns
            WHERE table_schema = %s
            AND table_name = %s
        """,
            (os.getenv("MYSQL_DATABASE"), table),
        )

        fields = cur.fetchall()

        cur.close()
        conn.close()

        return success_response(
            {
                "table": table,
                "count": len(fields),
            }
        )

    except Exception as e:
        print(f"Error counting fields: {e}")
        return error_response(str(e))


def table_exists(table: str) -> bool:
    conn = get_conn()
    cur = conn.cursor()

    try:
        cur.execute(
            "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = %s AND LOWER(table_name) = LOWER(%s)",
            (os.getenv("MYSQL_DATABASE"), table),
        )

        return cur.fetchone()[0] > 0

    finally:
        cur.close()


def validate_table(table: str):
    if table_exists(table):
        return None

    tables = get_table_names()

    return error_response(
        f"Table '{table}' does not exist.",
        available_tables=tables,
    )


if __name__ == "__main__":
    print("Starting MCP Server...", file=sys.stderr)
    mcp.run(transport="streamable-http")
