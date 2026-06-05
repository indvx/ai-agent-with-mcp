def test_create_new_user(client):
    response = client.post(
        "/users/register",
        json={
            "full_name": "John",
            "email": "user@example.com",
            "password": "stringstQ1!",
            "password_confirmation": "stringstQ1!",
        },
    )

    assert response.status_code == 200
    assert response.json() == {"message": "User Registered"}


def test_get_users(client):
    response = client.get("/users/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_user(client):
    response = client.get("/users/1")
    assert response.status_code == 200
    assert response.json()["email"] == "user@example.com"


def test_delete_user(client):
    response = client.delete("/users/1")
    assert response.status_code == 200
    assert response.json() == {"message": "User deleted"}
