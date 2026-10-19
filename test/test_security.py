import pytest
from fastapi import HTTPException
import jwt
import os
from core.security import get_current_user, decode_token
from sql.models.users import User
from sql.crud.users import get_password_hash


def test_get_current_user_success(db_session):
    secret_key = os.getenv("SECRET_KEY")
    algorithm = os.getenv("ALGORITHM", "HS256")

    user = User(
        full_name="Active Test User",
        email="activetest@example.com",
        password_hash=get_password_hash("ValidPass1!"),
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()

    token = jwt.encode({"sub": str(user.id)}, secret_key, algorithm=algorithm)
    resolved_user = get_current_user(token=token, db=db_session)

    assert resolved_user.id == user.id
    assert resolved_user.email == "activetest@example.com"


def test_get_current_user_inactive_user(db_session):
    secret_key = os.getenv("SECRET_KEY")
    algorithm = os.getenv("ALGORITHM", "HS256")

    user = User(
        full_name="Inactive User",
        email="inactive@example.com",
        password_hash=get_password_hash("ValidPass1!"),
        is_active=False,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()

    token = jwt.encode({"sub": str(user.id)}, secret_key, algorithm=algorithm)
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(token=token, db=db_session)

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Inactive user"


def test_get_current_user_not_found(db_session):
    secret_key = os.getenv("SECRET_KEY")
    algorithm = os.getenv("ALGORITHM", "HS256")

    token = jwt.encode({"sub": "999999"}, secret_key, algorithm=algorithm)
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(token=token, db=db_session)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "User not found"
