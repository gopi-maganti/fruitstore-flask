import pytest

"""
Positive Test Cases for Order API
"""
def test_add_order_success(client, setup_order_data):
    user_id = setup_order_data["user_id"]
    cart_id = setup_order_data["cart_id"]

    response = client.post(f"/order/add/{user_id}", json={"cart_ids": [cart_id]})
    assert response.status_code == 201
    data = response.get_json()
    
    assert data["total_order_price"] == 12.0
    assert data["items"][0]["fruit_name"] == "FixtureFruit"

def test_get_order_by_user_id_success(client, setup_order_data):
    user_id = setup_order_data["user_id"]
    cart_id = setup_order_data["cart_id"]

    # First add an order
    client.post(f"/order/add/{user_id}", json={"cart_ids": [cart_id]})

    response = client.get(f"/order/history/{user_id}")
    assert response.status_code == 200
    data = response.get_json()
    print(data)
    
    assert isinstance(data, list)
    assert len(data) > 0
    assert "order_id" in data[0]
    assert "items" in data[0]
    assert data[0]["items"][0]["fruit_name"] == "FixtureFruit"

def test_get_all_orders_success(client, setup_order_data):
    user_id = setup_order_data["user_id"]
    cart_id = setup_order_data["cart_id"]

    # First add an order
    client.post(f"/order/add/{user_id}", json={"cart_ids": [cart_id]})

    response = client.get("/order/getall")
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) > 0

    for order in data:
        assert "order_id" in order
        assert "user_id" in order
        assert "fruit" in order
        assert "quantity" in order
        assert "price" in order

"""
Negative Test Cases for Order API
"""

def test_add_order_invalid_user_id(client):
    response = client.post("/order/add/999", json={"cart_ids": [1, 2]})
    assert response.status_code == 404
    assert b"User not found" in response.data

def test_add_order_invalid_cart_id(client, setup_order_data):
    user_id = setup_order_data["user_id"]

    response = client.post(f"/order/add/{user_id}", json={"cart_ids": [999]})
    assert response.status_code == 400
    assert b"No items found in cart to checkout" in response.data


def test_add_order_invalid_cart_ids(client, setup_order_data):
    user_id = setup_order_data["user_id"]
    cart_id = setup_order_data["cart_id"]

    # First add an order
    client.post(f"/order/add/{user_id}", json={"cart_ids": [cart_id]})

    # Now try to add an order with invalid cart IDs
    response = client.post(f"/order/add/{user_id}", json={"cart_ids": [998, 999]})
    assert response.status_code == 400
    assert b"No items found in cart to checkout" in response.data

def test_add_order_empty_cart_ids(client, setup_order_data):
    user_id = setup_order_data["user_id"]

    # First add an order
    client.post(f"/order/add/{user_id}", json={"cart_ids": []})

    # Now try to add an order with empty cart IDs
    response = client.post(f"/order/add/{user_id}", json={"cart_ids": []})
    assert response.status_code == 400
    assert b"No items found in cart to checkout" in response.data

def test_get_order_by_invalid_user_id(client):
    response = client.get("/order/history/999")
    assert response.status_code == 404
    assert b"User not found" in response.data

def test_get_order_by_user_id_no_orders(client, setup_order_data):
    user_id = setup_order_data["user_id"]

    # Ensure no orders exist for this user
    response = client.get(f"/order/history/{user_id}")
    assert response.status_code == 404
    data = response.get_json()
    assert isinstance(data, dict)
    assert data.get("message") == "No order history found"


def test_get_all_orders_no_orders(client):
    response = client.get("/order/getall")
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) == 0