from mcp.server.fastmcp import FastMCP
from typing import Optional
import mysql.connector
import sys
from dotenv import load_dotenv
import os

load_dotenv()


mcp = FastMCP(
    "mysql-test",
    host=os.getenv("MCP_HOST"),
    port=os.getenv("MCP_PORT"),
)


def get_conn():
    try:
        return mysql.connector.connect(
            host=os.getenv("MYSQL_HOST"),
            port=os.getenv("MYSQL_PORT"),
            user=os.getenv("MYSQL_USER"),
            password=os.getenv("MYSQL_PASSWORD"),
            database=os.getenv("MYSQL_DATABASE"),
        )
    except Exception as e:
        print(f"Error getting connection: {e}")
        return None


@mcp.tool(description="Count records in a table")
def count_records_table(
    table: str,
    field: Optional[str] = None,
    value: Optional[str] = None,
    desc: bool = False,
) -> str:
    try:
        print(f"Counting records in table {table}")
        print("field", field)
        conn = get_conn()
        cur = conn.cursor()
        matched_field = None
        if field:
            fields = get_fields(table)
            matched_field = [f for f in fields if field in f["COLUMN_NAME"]]
            if not matched_field:
                print(f"Field {field} not found in table {table}")
                return f"Field {field} not found in table {table}"

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

        if field:
            print(
                f"Record successfully counted in {table} with field {field}: {result[0]}"
            )
            return f"Count of records in {table} with field {field}: {result[0]}"
        else:
            print(f"Record successfully counted in {table}: {result[0]}")
            return f"Count of records in {table}: {result[0]}"
    except Exception as e:
        print(f"Error counting records in table {table}: {e}")
        return f"Error counting records in table {table}: {e}"


@mcp.tool(description="List records from a table")
def list_records(
    table: str,
    field: Optional[str] = None,
    value: Optional[str] = None,
    limit: int = 1,
    desc: bool = False,
) -> list:
    try:
        print("listing_records", "table", table)
        print("field", field)
        print("value", value)
        print("limit", limit)
        print("desc", desc)

        conn = get_conn()
        cur = conn.cursor(dictionary=True)
        matched_field = None

        if field:
            fields = get_fields(table)
            matched_field = [f for f in fields if field in f["COLUMN_NAME"]]
            if not matched_field:
                print(f"Field {field} not found in table {table}")
                conn.close()
                return []
            print(f"Matched field: {matched_field[0]['COLUMN_NAME']}")
            query = (
                f"SELECT * FROM {table} WHERE {matched_field[0]['COLUMN_NAME']} LIKE %s"
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
            query += f" LIMIT {limit}"

        cur.execute(query, (f"%{value}%",) if field else None)

        rows = cur.fetchall()

        conn.close()
        print(f"Listing records {len(rows)} from table {table} successfully")
        return rows
    except Exception as e:
        print(f"Error listing records from table {table}: {e}")
        return []


@mcp.tool(description="Count all tables in the database")
def count_all_tables() -> str:
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
        print(f"Getting {len(tables)} tables successfully")
        return f"Count of tables in the database: {len(tables)}"
    except Exception as e:
        print(f"Error counting all tables: {e}")
        return f"Error counting all tables: {e}"


@mcp.tool(description="Get table names")
def get_table_names() -> list:
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
        print(tables)
        print(f"Getting {len(tables)} tables successfully")
        return tables
    except Exception as e:
        print(f"Error getting table names: {e}")
        return []


@mcp.tool(description="Get fields of a table")
def get_fields(table: str) -> list:
    try:
        print(f"Gettting fields of the {table} table")
        conn = get_conn()
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

        print(f"Getting fields of the {table} table successfully")
        return fields
    except Exception as e:
        print(f"Error getting fields of the {table} table: {e}")
        return []


@mcp.tool(description="Count fields of a table")
def count_fields(table: str, field: str, value: str) -> str:
    try:
        print(f"Counting fields of the {table} table")
        conn = get_conn()
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

        print(f"Counting fields of the {table} table successfully")
        return f"{len(fields)} fields in the {table} table, {field} field has {value} value"
    except Exception as e:
        print(f"Error counting fields of the {table} table: {e}")
        return f"Error counting fields of the {table} table: {e}"


if __name__ == "__main__":
    print("Starting MCP Server...", file=sys.stderr)
    mcp.run(transport="streamable-http")
