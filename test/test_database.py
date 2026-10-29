import io
import sqlite3
from pathlib import Path
from unittest.mock import patch
import pytest

import database
import routers.database


@pytest.fixture(autouse=True)
def isolated_db_environment(tmp_path, monkeypatch):
    """Isolate database registry and databases directory in tmp_path for each test."""
    test_app_db = tmp_path / "test_app.db"
    test_databases_dir = tmp_path / "test_databases"
    test_databases_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(database, "SYSTEM_DB_PATH", test_app_db)
    monkeypatch.setattr(database, "DATABASES_DIR", test_databases_dir)
    monkeypatch.setattr(routers.database, "DATABASES_DIR", test_databases_dir)

    database.init_system_db()
    yield tmp_path


def test_get_database_info_nonexistent(client):
    """Verify get_database_info returns exists=False when requested database does not exist."""
    response = client.get("/database/info?db=nonexistent")
    assert response.status_code == 200
    data = response.json()
    assert data["exists"] is False
    assert data["total_tables"] == 0
    assert data["tables"] == []


def test_import_database_sql_file(client, tmp_path):
    """Verify importing a .sql script populates tables and registers the database."""
    sql_content = (
        b"CREATE TABLE departments (id INTEGER PRIMARY KEY, name TEXT);\n"
        b"INSERT INTO departments (name) VALUES ('Engineering');"
    )

    response = client.post(
        "/database/import",
        files={"file": ("company.sql", io.BytesIO(sql_content), "application/sql")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["database"]["name"] == "company"
    assert data["total_tables"] == 1
    assert "departments" in data["tables"]

    # Verify database appears in /database/list
    list_res = client.get("/database/list")
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert list_data["total_databases"] == 1
    assert list_data["databases"][0]["name"] == "company"


def test_import_database_db_binary(client, tmp_path):
    """Verify importing an existing .db SQLite file registers and discovers tables."""
    source_db = tmp_path / "source.db"
    conn = sqlite3.connect(source_db)
    conn.execute("CREATE TABLE products (id INTEGER PRIMARY KEY, title TEXT)")
    conn.execute("INSERT INTO products (title) VALUES ('Keyboard')")
    conn.commit()
    conn.close()

    db_bytes = source_db.read_bytes()
    response = client.post(
        "/database/import",
        files={"file": ("inventory.db", io.BytesIO(db_bytes), "application/octet-stream")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["database"]["name"] == "inventory"
    assert "products" in data["tables"]


def test_import_database_unsupported_extension(client):
    """Verify rejection of invalid file extensions."""
    response = client.post(
        "/database/import",
        files={"file": ("data.csv", io.BytesIO(b"a,b,c\n1,2,3"), "text/csv")},
    )
    assert response.status_code == 400
    assert "Unsupported file format" in response.json()["detail"]


def test_import_database_oversized(client):
    """Verify rejection of files exceeding the 5MB size limit."""
    huge_data = b"x" * (5 * 1024 * 1024 + 10)
    response = client.post(
        "/database/import",
        files={"file": ("big.db", io.BytesIO(huge_data), "application/octet-stream")},
    )
    assert response.status_code == 413
    assert "Maximum allowed file size" in response.json()["detail"]


def test_select_active_database_via_put(client, tmp_path):
    """Verify updating database status to 1 sets it as active."""
    # Register two databases
    db1 = database.register_database("sales", status=0)
    db2 = database.register_database("marketing", status=0)

    # Activate marketing via PUT
    response = client.put("/database/marketing", json={"status": 1})
    assert response.status_code == 200
    data = response.json()
    assert data["database"]["name"] == "marketing"
    assert data["database"]["status"] == 1

    active_info = database.get_active_database_info()
    assert active_info is not None
    assert active_info["name"] == "marketing"


def test_select_active_database_not_found(client):
    """Verify 404 response when updating non-existent database."""
    response = client.put("/database/ghost", json={"status": 1})
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_delete_database_endpoint(client, tmp_path):
    """Verify deleting a database removes record and file."""
    db_file = routers.database.DATABASES_DIR / "analytics.db"
    conn = sqlite3.connect(db_file)
    conn.execute("CREATE TABLE metrics (id INTEGER PRIMARY KEY, count INTEGER)")
    conn.commit()
    conn.close()

    database.register_database("analytics", status=1)

    response = client.delete("/database/analytics")
    assert response.status_code == 200
    assert "Successfully deleted" in response.json()["message"]
    assert not db_file.exists()


def test_delete_predefined_default_database_protected(client):
    """Verify predefined default database cannot be deleted."""
    # Register predefined default database
    database.register_database("default_system", status=1)
    database.update_database("default_system", is_default=True)

    response = client.delete("/database/default_system")
    assert response.status_code == 400
    assert "Predefined default database cannot be deleted" in response.json()["detail"]


def test_delete_active_database_falls_back_to_default(client):
    """Verify fallback to default predefined database when active database is deleted."""
    # Register predefined default database
    database.register_database("predefined_db", status=0)
    database.update_database("predefined_db", is_default=True)

    # Register and activate a user database
    database.register_database("user_db", status=1)

    active_before = database.get_active_database_info()
    assert active_before["name"] == "user_db"

    # Delete active user database
    res = client.delete("/database/user_db")
    assert res.status_code == 200

    # System should now fall back to predefined default database
    active_after = database.get_active_database_info()
    assert active_after is not None
    assert active_after["name"] == "predefined_db"
    assert active_after["is_default"] == 1


def test_list_tables_and_details_endpoints(client, tmp_path):
    """Verify table listing and detailed schema inspection endpoints."""
    db_file = routers.database.DATABASES_DIR / "org.db"
    conn = sqlite3.connect(db_file)
    conn.execute("CREATE TABLE staff (id INTEGER PRIMARY KEY, name TEXT NOT NULL, role TEXT DEFAULT 'Engineer')")
    conn.execute("INSERT INTO staff (name, role) VALUES ('Dilip', 'Dev')")
    conn.commit()
    conn.close()

    database.register_database("org", status=1)

    # Tables overview
    tables_res = client.get("/database/tables?db=org")
    assert tables_res.status_code == 200
    tables_data = tables_res.json()
    assert tables_data["total_tables"] == 1
    assert tables_data["tables"][0]["name"] == "staff"
    assert tables_data["tables"][0]["total_rows"] == 1
    assert tables_data["tables"][0]["total_columns"] == 3

    # Table details
    detail_res = client.get("/database/tables/staff?db=org")
    assert detail_res.status_code == 200
    detail_data = detail_res.json()
    assert detail_data["table"] == "staff"
    assert detail_data["total_rows"] == 1
    assert len(detail_data["columns"]) == 3

    col_names = [c["name"] for c in detail_data["columns"]]
    assert "id" in col_names
    assert "name" in col_names
    assert "role" in col_names


def test_table_details_not_found(client, tmp_path):
    """Verify 404 when querying a non-existent table."""
    db_file = routers.database.DATABASES_DIR / "testdb.db"
    conn = sqlite3.connect(db_file)
    conn.close()
    database.register_database("testdb", status=1)

    response = client.get("/database/tables/nonexistent?db=testdb")
    assert response.status_code == 404
    assert "does not exist" in response.json()["detail"]


def test_import_database_mysql_dump_with_comments_and_missing_tables(client):
    """Verify importing MySQL dumps with column comments, ON UPDATE, and auto-created tables."""
    mysql_dump = (
        b"/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;\n"
        b"SET foreign_key_checks = 0;\n"
        b"DROP TABLE IF EXISTS `activities`;\n"
        b"CREATE TABLE `activities` (\n"
        b"  `id` int NOT NULL AUTO_INCREMENT,\n"
        b"  `employee_id` int NOT NULL,\n"
        b"  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'ON UPDATE CURRENT_TIMESTAMP()',\n"
        b"  PRIMARY KEY (`id`),\n"
        b"  CONSTRAINT `fk_emp` FOREIGN KEY (`employee_id`) REFERENCES `employees` (`id`)\n"
        b") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;\n"
        b"INSERT INTO `activities` (`id`, `employee_id`) VALUES (1, 10);\n"
        b"INSERT INTO `employees` (`id`, `name`) VALUES (10, 'John Doe');\n"
    )

    response = client.post(
        "/database/import",
        files={"file": ("dump_test.sql", io.BytesIO(mysql_dump), "application/sql")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "activities" in data["tables"]
    assert "employees" in data["tables"]

    # Check imported table contents
    imported_db = routers.database.DATABASES_DIR / "dump_test.db"
    conn = sqlite3.connect(imported_db)
    act_rows = conn.execute("SELECT id, employee_id FROM activities").fetchall()
    emp_rows = conn.execute("SELECT id, name FROM employees").fetchall()
    conn.close()

    assert act_rows == [(1, 10)]
    assert emp_rows == [(10, "John Doe")]

