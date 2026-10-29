import io
import sqlite3
from unittest.mock import patch
from starlette.testclient import TestClient

from main import app

client = TestClient(app)


def test_get_database_info_nonexistent(tmp_path):
    test_db = tmp_path / "missing.db"
    with patch("os.getenv", return_value=str(test_db)):
        response = client.get("/database/info")
        assert response.status_code == 200
        data = response.json()
        assert data["exists"] is False
        assert data["total_tables"] == 0
        assert data["tables"] == []


def test_get_database_info_existing(tmp_path):
    test_db = tmp_path / "existing.db"
    conn = sqlite3.connect(test_db)
    conn.execute("CREATE TABLE employees (id INTEGER PRIMARY KEY, name TEXT)")
    conn.commit()
    conn.close()

    with patch("os.getenv", return_value=str(test_db)):
        response = client.get("/database/info")
        assert response.status_code == 200
        data = response.json()
        assert data["exists"] is True
        assert data["total_tables"] == 1
        assert "employees" in data["tables"]


def test_import_database_sql_file(tmp_path):
    test_db = tmp_path / "active.db"
    sql_content = b"CREATE TABLE departments (id INTEGER PRIMARY KEY, name TEXT);\nINSERT INTO departments (name) VALUES ('Engineering');"

    with patch("os.getenv", return_value=str(test_db)):
        response = client.post(
            "/database/import",
            files={"file": ("dump.sql", io.BytesIO(sql_content), "application/sql")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["total_tables"] == 1
        assert "departments" in data["tables"]


def test_import_database_db_file(tmp_path):
    source_db = tmp_path / "source.db"
    target_db = tmp_path / "target.db"

    conn = sqlite3.connect(source_db)
    conn.execute("CREATE TABLE products (id INTEGER PRIMARY KEY, title TEXT)")
    conn.commit()
    conn.close()

    db_bytes = source_db.read_bytes()

    with patch("os.getenv", return_value=str(target_db)):
        response = client.post(
            "/database/import",
            files={"file": ("backup.db", io.BytesIO(db_bytes), "application/octet-stream")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "products" in data["tables"]


def test_import_database_unsupported_extension():
    response = client.post(
        "/database/import",
        files={"file": ("report.csv", io.BytesIO(b"id,name\n1,Alice"), "text/csv")},
    )
    assert response.status_code == 400
    assert "Unsupported file format" in response.json()["detail"]


def test_list_tables_overview(tmp_path):
    test_db = tmp_path / "overview.db"
    conn = sqlite3.connect(test_db)
    conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, email TEXT, active INTEGER)")
    conn.execute("INSERT INTO users (email, active) VALUES ('admin@test.com', 1)")
    conn.execute("CREATE TABLE roles (id INTEGER PRIMARY KEY, title TEXT)")
    conn.commit()
    conn.close()

    with patch("os.getenv", return_value=str(test_db)):
        response = client.get("/database/tables")
        assert response.status_code == 200
        data = response.json()
        assert data["total_tables"] == 2
        user_table = next(t for t in data["tables"] if t["name"] == "users")
        assert user_table["total_rows"] == 1
        assert user_table["total_columns"] == 3


def test_get_table_details_endpoint(tmp_path):
    test_db = tmp_path / "details.db"
    conn = sqlite3.connect(test_db)
    conn.execute("CREATE TABLE employees (id INTEGER PRIMARY KEY, name TEXT NOT NULL, salary REAL DEFAULT 0.0)")
    conn.execute("INSERT INTO employees (name, salary) VALUES ('Alice', 75000.0)")
    conn.commit()
    conn.close()

    with patch("os.getenv", return_value=str(test_db)):
        response = client.get("/database/tables/employees")
        assert response.status_code == 200
        data = response.json()
        assert data["table"] == "employees"
        assert data["total_rows"] == 1
        assert data["total_columns"] == 3
        col_names = [c["name"] for c in data["columns"]]
        assert "id" in col_names
        assert "name" in col_names
        assert "salary" in col_names

        id_col = next(c for c in data["columns"] if c["name"] == "id")
        assert id_col["primary_key"] is True

        name_col = next(c for c in data["columns"] if c["name"] == "name")
        assert name_col["nullable"] is False


def test_get_table_details_not_found(tmp_path):
    test_db = tmp_path / "details.db"
    conn = sqlite3.connect(test_db)
    conn.close()

    with patch("os.getenv", return_value=str(test_db)):
        response = client.get("/database/tables/nonexistent")
        assert response.status_code == 404
        assert "does not exist" in response.json()["detail"]
