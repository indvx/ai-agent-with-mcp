from mcp.server.fastmcp import FastMCP
import mysql.connector
import sys

mcp = FastMCP(
    "mysql-test",
    host="localhost",
    port=8001
)

def get_conn():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="python_dummy"
    )


@mcp.tool()
def add_record(table: str, data: dict) -> str:

    print(f"Adding data {data} in the table {table}")
    conn = get_conn()
    cur = conn.cursor()

    columns = ", ".join(data.keys())
    placeholders = ", ".join(["%s"] * len(data))
    values = list(data.values())

    query = f"""
        INSERT INTO {table} ({columns})
        VALUES ({placeholders})
    """

    cur.execute(query, values)

    conn.commit()
    conn.close()
    
    print(f"Record successfully added in {table}")

    return f"Record added to {table}"


@mcp.tool()
def list_records(table: str) -> list:
    print('listing_records', "table", table)
    conn = get_conn()
    cur = conn.cursor(dictionary=True)

    query = f"SELECT * FROM {table}"

    cur.execute(query)

    rows = cur.fetchall()

    conn.close()
    print(f"Listing records {len(rows)} from table {table} successfully")
    return rows


@mcp.tool()
def update_record(table: str, record_id: int, data: dict) -> str:

    print('Updating record', record_id, "data", data)
    conn = get_conn()
    cur = conn.cursor()

    set_clause = ", ".join([f"{k}=%s" for k in data.keys()])
    values = list(data.values())

    query = f"""
        UPDATE {table}
        SET {set_clause}
        WHERE id = %s
    """

    values.append(record_id)

    cur.execute(query, values)

    conn.commit()
    conn.close()
    print("Updated record successfully")
    return f"Record {record_id} updated in {table}"


@mcp.tool()
def delete_record(table: str, record_id: int) -> str:

    print(f"Deleting record {record_id} from table {table}")
    conn = get_conn()
    cur = conn.cursor()

    query = f"DELETE FROM {table} WHERE id = %s"

    cur.execute(query, (record_id,))

    conn.commit()
    conn.close()
    print('delete_record', record_id)
    return f"Record {record_id} deleted from {table}"


@mcp.tool()
def get_tables() -> list:
    print("Getting tables")
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = %s
    """, ("python_dummy",))

    tables = [row[0] for row in cur.fetchall()]

    conn.close()
    print(f"Getting {len(tables)} tables successfully")
    return tables


@mcp.tool()
def get_fields(table: str) -> list:

    print(f"Gettting fields of the {table} table")
    conn = get_conn()
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT
            column_name,
            data_type,
            is_nullable,
            column_key
        FROM information_schema.columns
        WHERE table_schema = %s
        AND table_name = %s
    """, ("python_dummy", table))

    fields = cur.fetchall()

    conn.close()

    print(f"Getting fields of the {table} table successfully")
    return fields

if __name__ == "__main__":
    print("Starting MCP Server...", file=sys.stderr)
    mcp.run(transport="streamable-http")