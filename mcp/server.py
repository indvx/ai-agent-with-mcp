from mcp.server.fastmcp import FastMCP
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
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST"),
        port=os.getenv("MYSQL_PORT"),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DATABASE"),
    )


@mcp.tool()
def count_records_table(table: str) -> str:

    print(f"Counting records in table {table}")
    conn = get_conn()
    cur = conn.cursor()

    query = f"""
        SELECT COUNT(*) FROM {table}
    """

    cur.execute(query)

    conn.commit()
    conn.close()

    print(f"Record successfully counted in {table}")

    return f"Count of records in {table}: {cur.fetchone()[0]}"


@mcp.tool()
def list_records(table: str) -> list:
    print("listing_records", "table", table)
    conn = get_conn()
    cur = conn.cursor(dictionary=True)

    query = f"SELECT * FROM {table}"

    cur.execute(query)

    rows = cur.fetchall()

    conn.close()
    print(f"Listing records {len(rows)} from table {table} successfully")
    return rows

@mcp.tool()
def count_all_tables() -> str:
    print("Getting tables")
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = %s
    """,
        ("python_dummy",),
    )

    tables = [row[0] for row in cur.fetchall()]

    conn.close()
    print(f"Getting {len(tables)} tables successfully")
    return f"Count of tables in the database: {len(tables)}"

@mcp.tool()
def get_table_names() -> list:
    print("Getting tables")
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = %s
    """,
        ("python_dummy",),
    )

    tables = [row[0] for row in cur.fetchall()]

    conn.close()
    print(f"Getting {len(tables)} tables successfully")
    return tables


@mcp.tool()
def get_fields(table: str) -> list:

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
        ("python_dummy", table),
    )

    fields = cur.fetchall()

    conn.close()

    print(f"Getting fields of the {table} table successfully")
    return fields


@mcp.tool()
def count_fields(table: str, field: str, value: str) -> str:
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
        ("python_dummy", table),
    )

    fields = cur.fetchall()

    conn.close()

    print(f"Counting fields of the {table} table successfully")
    return f"{len(fields)} fields in the {table} table, {field} field has {value} value"


if __name__ == "__main__":
    print("Starting MCP Server...", file=sys.stderr)
    mcp.run(transport="streamable-http")
