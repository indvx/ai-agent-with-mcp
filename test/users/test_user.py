from sql.models.users import User
from sql.crud.users import get_password_hash


def test_create_new_user(client):
    response = client.post(
        "/auth/register",
        json={
            "full_name": "John",
            "email": "user@example.com",
            "password": "stringstQ1!",
            "password_confirmation": "stringstQ1!",
        },
    )

    assert response.status_code == 201
    assert response.json() == {"message": "User registered successfully"}


def test_get_users(client):
    response = client.get("/users/")
    assert response.status_code == 200
    assert "users" in response.json()
    assert isinstance(response.json()["users"], list)


def test_get_user(client, db_session):
    user = User(
        full_name="John",
        email="user@example.com",
        password_hash=get_password_hash("stringstQ1!"),
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()

    response = client.get(f"/users/{user.id}")
    assert response.status_code == 200
    assert response.json()["email"] == "user@example.com"


def test_delete_user(client, db_session):
    user = User(
        full_name="John",
        email="user@example.com",
        password_hash=get_password_hash("stringstQ1!"),
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()

    response = client.delete(f"/users/{user.id}")
    assert response.status_code == 200
    assert response.json() == {"message": "User deleted"}
