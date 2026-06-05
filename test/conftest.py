import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from routers.user import user_read_permissions, user_delete_permissions

from database import Base, get_db
from main import app

TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})

TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def override_get_db():
    connection = engine.connect()
    transaction = connection.begin()

    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()

def override_permissions():
    return True

@pytest.fixture()
def client():
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[user_read_permissions] = override_permissions
    app.dependency_overrides[user_delete_permissions] = override_permissions

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()