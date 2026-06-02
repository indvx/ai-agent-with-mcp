import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.server.fastmcp import FastMCP
from database import engine 
from sqlalchemy import text
from dotenv import load_dotenv

load_dotenv()


mcp = FastMCP(
    "mysql-test",
    host=os.getenv("MCP_HOST"),
    port=os.getenv("MCP_PORT"),
)

def get_conn():
    return engine.connect()


# @mcp.tool()
# def add_record(table: str, data: dict) -> str:

#     print(f"Adding data {data} in the table {table}")
#     conn = get_conn()
   
#     columns = ", ".join(data.keys())
#     placeholders = ", ".join([f":{k}" for k in data.keys()])

#     query = text(f"""
#         INSERT INTO {table} ({columns})
#         VALUES ({placeholders})
#     """)

#     print(query, data)
#     conn.execute(query, data)

#     conn.commit()
#     conn.close()
    
#     print(f"Record successfully added in {table}")

#     return f"Record added to {table}"


@mcp.tool()
def list_records(table: str) -> list:
    print('listing_records', "table", table)
    conn = get_conn()
    query = text(f"SELECT * FROM {table}")
    result = conn.execute(query)
    rows = [dict(row) for row in result.mappings()]

    conn.close()
    print(f"Listing records {len(rows)} from table {table} successfully")
    return rows


# @mcp.tool()
# def update_record(table: str, record_id: int, data: dict) -> str:

#     print('Updating record', record_id, "data", data)
#     conn = get_conn()

#     set_clause = ", ".join([f"{k}=:{k}" for k in data.keys()])
    
#     query = text(f"""
#         UPDATE {table}
#         SET {set_clause}
#         WHERE id = :record_id
#     """)

#     params = {**data, "record_id": record_id}

#     conn.execute(query, params)

#     conn.commit()
#     conn.close()
#     print("Updated record successfully")
#     return f"Record {record_id} updated in {table}"


# @mcp.tool()
# def delete_record(table: str, record_id: int) -> str:

#     print(f"Deleting record {record_id} from table {table}")
#     conn = get_conn()

#     query = text(f"DELETE FROM {table} WHERE id = :record_id")

#     conn.execute(query, {"record_id": record_id})

#     conn.commit()
#     conn.close()
#     print('delete_record', record_id)
#     return f"Record {record_id} deleted from {table}"


@mcp.tool()
def get_tables() -> list:
    print("Getting tables")
    conn = get_conn()

    query = text("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = :schema
    """)

    result = conn.execute(query, {"schema": "python_dummy"})

    tables = [row[0] for row in result.fetchall()]

    conn.close()
    print(f"Getting {len(tables)} tables successfully")
    return tables


@mcp.tool()
def get_fields(table: str) -> list:

    print(f"Gettting fields of the {table} table")
    conn = get_conn()

    query = text("""
        SELECT
            column_name,
            data_type,
            is_nullable,
            column_key
        FROM information_schema.columns
        WHERE table_schema = :schema
        AND table_name = :table
    """)

    result = conn.execute(query, {"schema": "python_dummy", "table": table})

    fields = [dict(row) for row in result.mappings()]

    conn.close()

    print(f"Getting fields of the {table} table successfully")
    return fields

if __name__ == "__main__":
    print("Starting MCP Server...", file=sys.stderr)
    mcp.run(transport="streamable-http")