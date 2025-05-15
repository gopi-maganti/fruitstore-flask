import pytest

""" 
Positive Test Cases for User API
"""


def test_add_user_success(client):
    payload = {
        "name": "John Doe",
        "email": "john@example.com",
        "phone_number": "1234567890",
    }
    response = client.post("/user/add", json=payload)
    assert response.status_code == 201
    assert b"User added successfully" in response.data


def test_get_all_users(client):
    # First add a user
    client.post(
        "/user/add",
        json={
            "name": "Tester",
            "email": "tester@example.com",
            "phone_number": "1112223333",
        },
    )

    response = client.get("/user/")
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert any(user["name"] == "Tester" for user in data)


def test_get_single_user_success(client):
    # First add a user
    add_response = client.post(
        "/user/add",
        json={
            "name": "Single User",
            "email": "single@example.com",
            "phone_number": "1231231234",
        },
    )
    user_id = add_response.get_json()["message"].split(":")[-1].strip()

    response = client.get(f"/user/{user_id}")
    assert response.status_code == 200
    assert b"Single User" in response.data


def test_delete_user_success(client):
    # First add a user
    add_response = client.post(
        "/user/add",
        json={
            "name": "Delete User",
            "email": "delete@example.com",
            "phone_number": "3213214321",
        },
    )
    user_id = add_response.get_json()["message"].split(":")[-1].strip()

    delete_response = client.delete(f"/user/{user_id}")
    assert delete_response.status_code == 200
    assert b"User deleted successfully" in delete_response.data


"""
Negative Test Cases for User API
"""


# Testing Email
@pytest.mark.parametrize(
    "payload",
    [
        {"name": "User1", "email": "notanemail", "phone_number": "1234567890"},
        {"name": "User2", "email": "also@wrong", "phone_number": "9876543210"},
        {"name": "User3", "email": "missingdomain@", "phone_number": "1122334455"},
    ],
)
def test_add_user_invalid_emails(client, payload):
    response = client.post("/user/add", json=payload)
    assert response.status_code == 400
    assert b"Validation Error" in response.data


# Testing Phone Number
@pytest.mark.parametrize(
    "payload",
    [
        {
            "name": "UserA",
            "email": "usera@example.com",
            "phone_number": "abc1234567",
        },  # letters in phone
        {
            "name": "UserB",
            "email": "userb@example.com",
            "phone_number": "123",
        },  # too short
        {"name": "UserC", "email": "userc@example.com", "phone_number": ""},  # empty
        {
            "name": "UserD",
            "email": "userd@example.com",
            "phone_number": "12345678901",
        },  # too long
        {
            "name": "UserE",
            "email": "usere@example.com",
            "phone_number": "123-456-7890",
        },  # special chars
    ],
)
def test_add_user_invalid_phone_number(client, payload):
    response = client.post("/user/add", json=payload)
    assert response.status_code == 400
    assert (
        b"Improper phone number length" in response.data
        or b"Validation Error" in response.data
    )


def test_get_single_user_not_found(client):
    response = client.get("/user/999")
    assert response.status_code == 404
    assert b"User not found" in response.data


def test_delete_user_not_found(client):
    response = client.delete("/user/999")
    assert response.status_code == 404
    assert b"User not found" in response.data
