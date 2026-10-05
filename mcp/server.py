import sys
import os
from mcp.server.fastmcp import FastMCP
from typing import Optional

from dotenv import load_dotenv
import mysql.connector


load_dotenv()

MCP_HOST = os.getenv("MCP_HOST", "0.0.0.0")
MCP_PORT = int(os.getenv("MCP_PORT", "8001"))
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE")


mcp = FastMCP(
    "mysql-test",
    host=MCP_HOST,
    port=MCP_PORT,
)


MAX_RECORD_LIMIT = 20
MAX_TABLE_LIMIT = 20

SENSITIVE_FIELDS = {
    "password",
    "password_hash",
    "token",
    "access_token",
    "refresh_token",
    "secret",
    "api_key",
    "private_key",
}


def get_conn():
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=MYSQL_DATABASE,
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


def table_exists(table: str) -> bool:
    """
    Check whether a table exists in the configured database.
    """

    conn = get_conn()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_schema = %s
              AND LOWER(table_name) = LOWER(%s)
            """,
            (
                MYSQL_DATABASE,
                table,
            ),
        )

        return cur.fetchone()[0] > 0

    finally:
        cur.close()
        conn.close()


def validate_table(table: str):
    """
    Validate table without returning the entire table list.
    This prevents large MCP responses.
    """

    if table_exists(table):
        return None

    return error_response(f"Table '{table}' does not exist.")


def get_actual_table_name(table: str) -> Optional[str]:
    """
    Return the actual table name from MySQL.
    Useful for case-insensitive table matching.
    """

    conn = get_conn()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = %s
              AND LOWER(table_name) = LOWER(%s)
            LIMIT 1
            """,
            (
                MYSQL_DATABASE,
                table,
            ),
        )

        result = cur.fetchone()

        return result[0] if result else None

    finally:
        cur.close()
        conn.close()


def get_table_fields_raw(table: str):
    """
    Internal helper.
    Returns normalized field information from MySQL.
    """

    conn = get_conn()
    cur = conn.cursor(dictionary=True)

    try:
        cur.execute(
            """
            SELECT
                COLUMN_NAME,
                DATA_TYPE,
                IS_NULLABLE,
                COLUMN_KEY
            FROM information_schema.columns
            WHERE table_schema = %s
              AND table_name = %s
            ORDER BY ORDINAL_POSITION
            """,
            (
                MYSQL_DATABASE,
                table,
            ),
        )

        rows = cur.fetchall()

        # Normalize MySQL column names
        fields = []

        for row in rows:
            fields.append(
                {
                    "column_name": row["COLUMN_NAME"],
                    "data_type": row["DATA_TYPE"],
                    "is_nullable": row["IS_NULLABLE"],
                    "column_key": row["COLUMN_KEY"],
                }
            )

        return fields

    finally:
        cur.close()
        conn.close()


def find_field(
    available_fields: list[dict],
    requested_field: str,
) -> Optional[str]:
    """
    Find a field case-insensitively.
    """

    requested_field = requested_field.lower()

    for field in available_fields:
        actual_name = field["column_name"]

        if actual_name.lower() == requested_field:
            return actual_name

    return None


@mcp.tool(
    description=(
        "Find database tables by name. "
        "Use this when the correct table is unknown. "
        "The search parameter is optional."
    )
)
def get_table_names(
    search: Optional[str] = None,
    limit: int = MAX_TABLE_LIMIT,
):
    """
    Find tables in the database.

    Examples:

        get_table_names()

        get_table_names(search="employee")

        get_table_names(search="user")
    """

    try:
        conn = get_conn()
        cur = conn.cursor()

        limit = min(
            max(limit or 1, 1),
            MAX_TABLE_LIMIT,
        )

        query = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = %s
        """

        params = [MYSQL_DATABASE]

        if search:
            query += """
                AND LOWER(table_name) LIKE LOWER(%s)
            """

            params.append(f"%{search}%")

        query += """
            ORDER BY table_name
            LIMIT %s
        """

        params.append(limit)

        cur.execute(query, params)

        tables = [row[0] for row in cur.fetchall()]

        cur.close()
        conn.close()

        return success_response(
            {
                "count": len(tables),
                "tables": tables,
            }
        )

    except Exception as e:
        print(
            f"Error getting tables: {e}",
            file=sys.stderr,
        )

        return error_response(f"Error getting tables: {e}")


@mcp.tool(
    description=(
        "Get the fields/columns of a specific database table. "
        "Use this after identifying the correct table."
    )
)
def get_fields(table: str):
    """
    Get columns of a table.
    """

    try:
        actual_table = get_actual_table_name(table)

        if not actual_table:
            return error_response(f"Table '{table}' does not exist.")

        fields = get_table_fields_raw(actual_table)

        # Don't expose unnecessary information.
        result = []

        for field in fields:
            result.append(
                {
                    "column_name": field["column_name"],
                    "data_type": field["data_type"],
                    "is_nullable": field["is_nullable"],
                    "column_key": field["column_key"],
                }
            )

        return success_response(
            {
                "table": actual_table,
                "count": len(result),
                "fields": result,
            }
        )

    except Exception as e:
        print(
            f"Error getting fields: {e}",
            file=sys.stderr,
        )

        return error_response(f"Error getting fields: {e}")


@mcp.tool(
    description=(
        "List records from a database table. "
        "Never return more than 20 records in one call. "
        "If the user asks for one, single, or only one record, "
        "use limit=1. "
        "If the user asks for a specific number, use that number "
        "up to the maximum allowed limit. "
        "For normal list requests, use limit=20. "
        "For all/every records, use limit=20 and start with offset=0. "
        "Continue requesting the next page using next_offset until "
        "has_more=false. "
        "Never use limit=1 unless the user explicitly asks for one record. "
        "Never remove the LIMIT/OFFSET restriction."
    )
)
def list_records(
    table: str,
    field: Optional[str] = None,
    value: Optional[str] = None,
    fields: Optional[list[str]] = None,
    limit: int = 20,
    offset: int = 0,
    get_all: bool = False,
    desc: bool = False,
):
    try:

        actual_table = get_actual_table_name(table)

        if not actual_table:
            return error_response(f"Table '{table}' does not exist.")

        available_fields = get_table_fields_raw(actual_table)

        if not available_fields:
            return error_response(f"No fields found for table '{actual_table}'.")

        available_field_names = [
            field_data["column_name"] for field_data in available_fields
        ]

        if fields:

            selected_fields = []
            invalid_fields = []

            for requested_field in fields:

                actual_field = find_field(
                    available_fields,
                    requested_field,
                )

                if not actual_field:
                    invalid_fields.append(requested_field)
                    continue

                if actual_field.lower() in SENSITIVE_FIELDS:
                    continue

                selected_fields.append(actual_field)

            if invalid_fields:
                return error_response(
                    f"Fields not found in table "
                    f"'{actual_table}': "
                    f"{', '.join(invalid_fields)}",
                    available_fields=[
                        field_name
                        for field_name in available_field_names
                        if field_name.lower() not in SENSITIVE_FIELDS
                    ],
                )

            if not selected_fields:
                return error_response("No valid fields were selected.")

        else:

            selected_fields = [
                field_name
                for field_name in available_field_names
                if field_name.lower() not in SENSITIVE_FIELDS
            ]

        matched_field = None

        if field:

            matched_field = find_field(
                available_fields,
                field,
            )

            if not matched_field:
                return error_response(
                    f"Field '{field}' not found " f"in table '{actual_table}'.",
                    available_fields=[
                        field_name
                        for field_name in available_field_names
                        if field_name.lower() not in SENSITIVE_FIELDS
                    ],
                )

            if matched_field.lower() in SENSITIVE_FIELDS:
                return error_response(
                    f"Searching by field " f"'{matched_field}' is not allowed."
                )

        order_field = find_field(
            available_fields,
            "id",
        )

        if not order_field:

            if matched_field:
                order_field = matched_field

            elif selected_fields:
                order_field = selected_fields[0]

        direction = "DESC" if desc else "ASC"

        columns = ", ".join(f"`{column}`" for column in selected_fields)

        query = f"SELECT {columns} " f"FROM `{actual_table}`"

        params = []

        if matched_field and value is not None:

            query += f" WHERE `{matched_field}` LIKE %s"

            params.append(f"%{value}%")

        if order_field:

            query += f" ORDER BY `{order_field}` " f"{direction}"

        limit = min(max(limit or 1, 1), MAX_RECORD_LIMIT)
        offset = max(offset or 0, 0)

        query += " LIMIT %s OFFSET %s"
        params.append(limit + 1)
        params.append(offset)

        conn = get_conn()
        cur = conn.cursor()

        cur.execute(query, tuple(params))

        rows = cur.fetchall()

        has_more = len(rows) > limit

        rows = rows[:limit]

        next_offset = offset + limit if has_more else None

        cur.close()
        conn.close()

        return success_response(
            {
                "table": actual_table,
                "count": len(rows),
                "offset": offset,
                "limit": limit,
                "has_more": has_more,
                "next_offset": next_offset,
                "data": rows,
            }
        )

    except Exception as e:

        print(
            f"Error listing records: {e}",
            file=sys.stderr,
        )

        return error_response(f"Error listing records: {e}")


@mcp.tool(
    description=(
        "Count records in a database table. "
        "Use field and value when counting matching records."
    )
)
def count_records_table(
    table: str,
    field: Optional[str] = None,
    value: Optional[str] = None,
):
    """
    Count records in a table.
    """

    try:
        actual_table = get_actual_table_name(table)

        if not actual_table:
            return error_response(f"Table '{table}' does not exist.")

        available_fields = get_table_fields_raw(actual_table)

        matched_field = None

        if field:

            matched_field = find_field(
                available_fields,
                field,
            )

            if not matched_field:
                return error_response(
                    f"Field '{field}' not found " f"in table '{actual_table}'.",
                    available_fields=[
                        item["column_name"]
                        for item in available_fields
                        if item["column_name"].lower() not in SENSITIVE_FIELDS
                    ],
                )

            if matched_field.lower() in SENSITIVE_FIELDS:
                return error_response(
                    f"Searching by field " f"'{matched_field}' is not allowed."
                )

        if matched_field and value is not None:

            query = (
                f"SELECT COUNT(*) "
                f"FROM `{actual_table}` "
                f"WHERE `{matched_field}` LIKE %s"
            )

            params = [f"%{value}%"]

        else:

            query = f"SELECT COUNT(*) " f"FROM `{actual_table}`"

            params = []

        conn = get_conn()
        cur = conn.cursor()

        cur.execute(
            query,
            params,
        )

        count = cur.fetchone()[0]

        cur.close()
        conn.close()

        return success_response(
            {
                "table": actual_table,
                "count": count,
            }
        )

    except Exception as e:

        print(
            f"Error counting records: {e}",
            file=sys.stderr,
        )

        return error_response(f"Error counting records: {e}")


if __name__ == "__main__":
    print(
        f"MCP: http://{MCP_HOST}:{MCP_PORT}/mcp",
        file=sys.stderr,
    )

    mcp.run(transport="streamable-http")
