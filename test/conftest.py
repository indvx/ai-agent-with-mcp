import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from fastapi import Request

from database import Base, get_db
from main import app
from core.security import get_current_user, JWTBearer
from sql.models.role import Role
from sql.models.permission import Permission

TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class MockPermission:
    def __init__(self, name):
        self.name = name


class MockRole:
    def __init__(self, name, permissions):
        self.name = name
        self.permissions = [MockPermission(p) for p in permissions]


class MockUser:
    def __init__(self):
        self.id = 1
        self.full_name = "Mock Admin"
        self.email = "admin@test.com"
        self.is_active = True
        self.is_verified = True
        self.roles = [
            MockRole(
                "admin",
                [
                    "user:create",
                    "user:read",
                    "user:update",
                    "user:delete",
                    "role:manage",
                    "permission:manage",
                    "chat:use",
                ],
            )
        ]


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    # Seed default roles and permissions in test db so registration can find the default role
    db = TestingSessionLocal()
    permissions = [
        "user:create",
        "user:read",
        "user:update",
        "user:delete",
        "role:manage",
        "permission:manage",
        "chat:use",
    ]
    for p_name in permissions:
        if not db.query(Permission).filter(Permission.name == p_name).first():
            db.add(Permission(name=p_name))
    
    for r_name in ["admin", "manager", "user"]:
        if not db.query(Role).filter(Role.name == r_name).first():
            db.add(Role(name=r_name, is_default=(r_name == "user")))
            
    db.commit()
    db.close()
    
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


def override_get_current_user():
    return MockUser()


async def mock_jwt_bearer_call(self, request: Request):
    return "mock_token"


@pytest.fixture(autouse=True)
def mock_jwt(monkeypatch):
    monkeypatch.setattr(JWTBearer, "__call__", mock_jwt_bearer_call)


@pytest.fixture
def client(db_session):
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()