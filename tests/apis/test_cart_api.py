import pytest

def test_add_to_cart_invalid_payload(client):
    # Missing required fields
    response = client.post("/cart/add", json={})
    assert response.status_code == 400
    assert b"Validation Error" in response.data

def test_add_to_cart_fruit_not_found(client):
    payload = {
        "user_id": -1,
        "fruit_id": 999,   # invalid fruit_id
        "quantity": 2
    }
    response = client.post("/cart/add", json=payload)
    assert response.status_code == 404
    assert b"FruitInfo not found" in response.data

import io

def add_fruit(client):
    image = (io.BytesIO(b"fake"), "fruit.jpg")
    fruit_data = {
        "name": "Test Fruit",
        "description": "desc",
        "color": "Red",
        "size": "M",
        "has_seeds": "true",
        "weight": "1.0",
        "price": "10.0",
        "total_quantity": "50",
        "available_quantity": "50",
        "sell_by_date": "2030-01-01",
        "image": image
    }
    data = {k: v for k, v in fruit_data.items() if k != "image"}
    return client.post("/fruit/add", data={**data, "image": image}, content_type="multipart/form-data")

def add_user(client):
    return client.post("/user/add", json={
        "name": "CartUser",
        "email": "cart@example.com",
        "phone_number": "1234567890"
    })

def test_add_to_cart_success(client):
    fruit_resp = add_fruit(client)
    fruit_id = fruit_resp.get_json()["fruit"]["fruit_id"]

    user_resp = add_user(client)
    user_id = int(user_resp.get_json()["message"].split(":")[-1])

    cart_payload = {
        "user_id": user_id,
        "fruit_id": fruit_id,
        "quantity": 3
    }

    response = client.post("/cart/add", json=cart_payload)
    assert response.status_code == 201
    assert b"Item added to cart successfully" in response.data

def test_get_cart_invalid_user(client):
    response = client.get("/cart/999")  # Invalid user_id
    assert response.status_code == 404
    assert b"No cart items found for this user" in response.data

def test_get_cart_empty(client):
    user_resp = add_user(client)
    print("---------", user_resp.get_json())
    user_id = int(user_resp.get_json()["message"].split(":")[-1])

    response = client.get(f"/cart/{user_id}")
    assert response.status_code == 404
    assert b"No cart items found for this user" in response.data

def test_update_cart_item_not_found(client):
    response = client.put("/cart/update/999", json={"quantity": 5})
    assert response.status_code == 404
    assert b"Cart item not found" in response.data





