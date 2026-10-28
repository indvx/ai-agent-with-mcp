"""Unit tests for MCP server database tools, connection pooling, and row serialization."""

import importlib.util
from datetime import datetime, date
from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

# Load the local mcp/server.py module directly to avoid shadowing by the installed 'mcp' SDK package
_server_path = Path(__file__).parent.parent / "mcp" / "server.py"
_spec = importlib.util.spec_from_file_location("local_mcp_server", _server_path)
mcp_server = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mcp_server)

serialize_row = mcp_server.serialize_row
get_conn = mcp_server.get_conn
list_records = mcp_server.list_records
count_records_table = mcp_server.count_records_table
build_filter_condition = mcp_server.build_filter_condition


def test_serialize_row_primitives():
    """Verify serialize_row preserves primitives and serializes complex types."""
    now = datetime(2026, 10, 19, 12, 0, 0)
    today = date(2026, 10, 19)
    raw = {
        "id": 1,
        "name": "Test User",
        "balance": Decimal("150.75"),
        "created_at": now,
        "birth_date": today,
        "raw_bytes": b"hello_world",
        "is_active": True,
    }

    result = serialize_row(raw)

    assert result["id"] == 1
    assert result["name"] == "Test User"
    assert result["balance"] == 150.75
    assert result["created_at"] == "2026-10-19T12:00:00"
    assert result["birth_date"] == "2026-10-19"
    assert result["raw_bytes"] == "hello_world"
    assert result["is_active"] is True


def test_get_conn_uses_pool():
    """Verify get_conn delegates to the underlying connection pool."""
    mock_pool = MagicMock()
    mock_connection = MagicMock()
    mock_pool.get_connection.return_value = mock_connection

    with patch.object(mcp_server, "_db_pool", mock_pool):
        conn = get_conn()
        assert conn == mock_connection
        mock_pool.get_connection.assert_called_once()


def test_list_records_returns_key_value_dicts():
    """Verify list_records uses a dictionary cursor and returns key-value mappings."""
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value = mock_cur

    mock_cur.fetchall.return_value = [
        {"id": 1, "email": "admin@test.com", "name": "Admin"},
        {"id": 2, "email": "user@test.com", "name": "User"},
    ]

    mock_fields = [
        {"column_name": "id", "data_type": "int", "is_nullable": "NO", "column_key": "PRI"},
        {"column_name": "email", "data_type": "varchar", "is_nullable": "NO", "column_key": ""},
        {"column_name": "name", "data_type": "varchar", "is_nullable": "YES", "column_key": ""},
    ]

    with patch.object(mcp_server, "get_actual_table_name", return_value="users"), \
         patch.object(mcp_server, "get_table_fields_raw", return_value=mock_fields), \
         patch.object(mcp_server, "get_conn", return_value=mock_conn):

        response = list_records(table="users", limit=10)

        # Ensure dictionary=True cursor was requested
        mock_conn.cursor.assert_called_with(dictionary=True)
        # Ensure connections are closed
        mock_cur.close.assert_called_once()
        mock_conn.close.assert_called_once()

        assert response["success"] is True
        assert response["data"]["table"] == "users"
        assert response["data"]["count"] == 2
        assert isinstance(response["data"]["data"], list)
        assert isinstance(response["data"]["data"][0], dict)
        assert response["data"]["data"][0]["email"] == "admin@test.com"


def test_list_records_closes_connection_on_error():
    """Verify list_records releases the pooled connection even if execution errors."""
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value = mock_cur
    mock_cur.execute.side_effect = RuntimeError("Database query failed")

    mock_fields = [
        {"column_name": "id", "data_type": "int", "is_nullable": "NO", "column_key": "PRI"},
    ]

    with patch.object(mcp_server, "get_actual_table_name", return_value="users"), \
         patch.object(mcp_server, "get_table_fields_raw", return_value=mock_fields), \
         patch.object(mcp_server, "get_conn", return_value=mock_conn):

        response = list_records(table="users")

        assert response["success"] is False
        assert "Database query failed" in response["error"]
        mock_cur.close.assert_called_once()
        mock_conn.close.assert_called_once()


def test_build_filter_condition_tinyint():
    """Verify boolean and status strings map to integer flags for tinyint/boolean columns."""
    tinyint_col = {"column_name": "status", "data_type": "tinyint"}
    sql, params = build_filter_condition(tinyint_col, "active")
    assert sql == "`status` = %s"
    assert params == [1]

    sql, params = build_filter_condition(tinyint_col, "inactive")
    assert sql == "`status` = %s"
    assert params == [0]

    sql, params = build_filter_condition(tinyint_col, 1)
    assert sql == "`status` = %s"
    assert params == [1]

    sql, params = build_filter_condition(tinyint_col, "0")
    assert sql == "`status` = %s"
    assert params == [0]

    # Varchar columns should retain LIKE text matching
    varchar_col = {"column_name": "status", "data_type": "varchar"}
    sql, params = build_filter_condition(varchar_col, "active")
    assert sql == "`status` LIKE %s"
    assert params == ["%active%"]


def test_count_records_table_tinyint_mapping():
    """Verify count_records_table converts 'active' to numeric 1 when filtering tinyint columns."""
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value = mock_cur
    mock_cur.fetchone.return_value = [32]

    mock_fields = [
        {"column_name": "id", "data_type": "int", "is_nullable": "NO", "column_key": "PRI"},
        {"column_name": "status", "data_type": "tinyint", "is_nullable": "YES", "column_key": ""},
    ]

    with patch.object(mcp_server, "get_actual_table_name", return_value="employees"), \
         patch.object(mcp_server, "get_table_fields_raw", return_value=mock_fields), \
         patch.object(mcp_server, "get_conn", return_value=mock_conn):

        response = count_records_table(table="employees", field="status", value="active")

        assert response["success"] is True
        assert response["data"]["table"] == "employees"
        assert response["data"]["count"] == 32

        mock_cur.execute.assert_called_once_with(
            "SELECT COUNT(*) FROM `employees` WHERE `status` = %s",
            [1],
        )
        mock_cur.close.assert_called_once()
        mock_conn.close.assert_called_once()


def test_list_records_tinyint_mapping():
    """Verify list_records converts 'active' to numeric 1 for tinyint column filter."""
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value = mock_cur
    mock_cur.fetchall.return_value = [
        {"id": 1, "status": 1},
    ]

    mock_fields = [
        {"column_name": "id", "data_type": "int", "is_nullable": "NO", "column_key": "PRI"},
        {"column_name": "status", "data_type": "tinyint", "is_nullable": "YES", "column_key": ""},
    ]

    with patch.object(mcp_server, "get_actual_table_name", return_value="employees"), \
         patch.object(mcp_server, "get_table_fields_raw", return_value=mock_fields), \
         patch.object(mcp_server, "get_conn", return_value=mock_conn):

        response = list_records(table="employees", field="status", value="active")

        assert response["success"] is True
        assert response["data"]["count"] == 1
        query, params = mock_cur.execute.call_args[0]
        assert "WHERE `status` = %s" in query
        assert params[0] == 1

