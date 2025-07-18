import pytest

# --------------------------------------
# ✅ Positive Test Cases
# --------------------------------------

def test_add_user_success(client, add_user):
    response, user_id = add_user(client, name="Alice", email="alice@example.com", phone="1112223333")
    assert response.status_code == 201
    assert b"User created" in response.data

def test_get_all_users(client, add_user):
    add_user(client, name="Bob", email="bob@example.com", phone="2223334444")
    response = client.get("/user/all")
    assert response.status_code == 200
    assert isinstance(response.get_json(), list)

def test_get_single_user_success(client, add_user):
    _, user_id = add_user(client, name="Charlie", email="charlie@example.com", phone="3334445555")
    response = client.get(f"/user/{user_id}")
    assert response.status_code == 200
    assert response.get_json()["user_id"] == user_id

def test_delete_user_success(client, add_user):
    _, user_id = add_user(client, name="Dave", email="dave@example.com", phone="4445556666")
    response = client.delete(f"/user/delete/{user_id}")
    assert response.status_code == 200
    assert b"deleted successfully" in response.data

# --------------------------------------
# ❌ Negative Test Cases
# --------------------------------------

def test_add_user_invalid_email(client):
    response = client.post("/user/add", json={
        "name": "Eve", "email": "invalid-email", "phone_number": "5556667777"
    })
    assert response.status_code == 400
    assert b"Invalid email format" in response.data

def test_add_user_invalid_phone_number(client):
    response = client.post("/user/add", json={
        "name": "Frank", "email": "frank@example.com", "phone_number": "notaphone"
    })
    assert response.status_code == 400
    assert b"Invalid phone number" in response.data

def test_get_single_user_not_found(client):
    response = client.get("/user/99999")
    assert response.status_code == 404
    assert b"User not found" in response.data

def test_delete_user_not_found(client):
    response = client.delete("/user/delete/99999")
    assert response.status_code == 404
    assert b"User not found" in response.data
