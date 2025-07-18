import pytest

# --------------------------------------
# Positive Test Cases
# --------------------------------------

def test_add_order_success(client, setup_order_data):
    data = setup_order_data
    response = client.post("/order/add", json={
        "user_id": data["user_id"],
        "cart_ids": [data["cart_id"]]
    })
    assert response.status_code == 201
    assert b"Order created" in response.data

def test_get_order_by_user_id_success(client, setup_order_data):
    data = setup_order_data
    client.post("/order/add", json={"user_id": data["user_id"], "cart_ids": [data["cart_id"]]})
    response = client.get(f"/order/user/{data['user_id']}")
    assert response.status_code == 200
    assert isinstance(response.get_json(), list)

def test_get_all_orders_success(client, setup_order_data):
    data = setup_order_data
    client.post("/order/add", json={"user_id": data["user_id"], "cart_ids": [data["cart_id"]]})
    response = client.get("/order/all")
    assert response.status_code == 200
    assert isinstance(response.get_json(), list)


# --------------------------------------
# Negative Test Cases
# --------------------------------------

def test_add_order_invalid_user_id(client, setup_order_data):
    data = setup_order_data
    response = client.post("/order/add", json={
        "user_id": 9999,
        "cart_ids": [data["cart_id"]]
    })
    assert response.status_code == 404
    assert b"User not found" in response.data

def test_add_order_invalid_cart_id(client, setup_order_data):
    data = setup_order_data
    response = client.post("/order/add", json={
        "user_id": data["user_id"],
        "cart_ids": [9999]
    })
    assert response.status_code == 404
    assert b"One or more cart items not found" in response.data

def test_add_order_invalid_cart_ids_type(client, setup_order_data):
    data = setup_order_data
    response = client.post("/order/add", json={
        "user_id": data["user_id"],
        "cart_ids": "notalist"
    })
    assert response.status_code == 400
    assert b"Invalid cart_ids format" in response.data

def test_add_order_empty_cart_ids(client, setup_order_data):
    data = setup_order_data
    response = client.post("/order/add", json={
        "user_id": data["user_id"],
        "cart_ids": []
    })
    assert response.status_code == 400
    assert b"cart_ids must not be empty" in response.data

def test_get_order_by_invalid_user_id(client):
    response = client.get("/order/user/9999")
    assert response.status_code == 404
    assert b"No orders found for user" in response.data

def test_get_order_by_user_id_no_orders(client, add_user):
    user_resp = add_user(client, email="noorder@example.com", phone="9998887777")
    user_id = int(user_resp.get_json()["message"].split(":")[-1])
    response = client.get(f"/order/user/{user_id}")
    assert response.status_code == 404
    assert b"No orders found for user" in response.data
