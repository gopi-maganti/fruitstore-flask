import io

import pytest

from app.models.cart import Cart


# Helper to add a fruit
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
        "image": image,
    }
    data = {k: v for k, v in fruit_data.items() if k != "image"}
    return client.post(
        "/fruit/add", data={**data, "image": image}, content_type="multipart/form-data"
    )

# Helper to add a user
def add_user(client, name="CartUser", email="cart@example.com", phone="1234567890"):
    return client.post(
        "/user/add",
        json={
            "name": name,
            "email": email,
            "phone_number": phone,
        },
    )


def test_add_to_cart_invalid_payload(client):
    response = client.post("/cart/add", json={})
    assert response.status_code == 400
    assert b"Validation Error" in response.data

def test_add_to_cart_fruit_not_found(client):
    payload = {"user_id": -1, "fruit_id": 999, "quantity": 2}
    response = client.post("/cart/add", json=payload)
    assert response.status_code == 404
    assert b"FruitInfo not found" in response.data

def test_add_to_cart_success(client):
    fruit_resp = add_fruit(client)
    fruit_id = fruit_resp.get_json()["fruit"]["fruit_id"]

    user_resp = add_user(client)
    user_id = int(user_resp.get_json()["message"].split(":")[-1])

    cart_payload = {"user_id": user_id, "fruit_id": fruit_id, "quantity": 3}
    response = client.post("/cart/add", json=cart_payload)

    assert response.status_code == 201
    assert b"Item added to cart successfully" in response.data


def test_get_cart_invalid_user(client):
    response = client.get("/cart/999")
    assert response.status_code == 404
    assert b"No cart items found for this user" in response.data

def test_get_cart_empty(client):
    user_resp = add_user(client, email="empty@example.com", phone="1111111111")
    user_id = int(user_resp.get_json()["message"].split(":")[-1])

    response = client.get(f"/cart/{user_id}")
    assert response.status_code == 404
    assert b"No cart items found for this user" in response.data

def test_update_cart_item_not_found(client):
    response = client.put("/cart/update/999", json={"quantity": 5})
    assert response.status_code == 404
    assert b"Cart item not found" in response.data

def test_associate_cart_success(client, app):
    with app.app_context():
        # Create users
        old_user_resp = add_user(client, name="Old", email="old@example.com", phone="1111111111")
        new_user_resp = add_user(client, name="New", email="new@example.com", phone="2222222222")

        old_user_id = int(old_user_resp.get_json()["message"].split(":")[-1])
        new_user_id = int(new_user_resp.get_json()["message"].split(":")[-1])

        # Add fruit and cart for old user
        fruit_resp = add_fruit(client)
        fruit_id = fruit_resp.get_json()["fruit"]["fruit_id"]
        client.post("/cart/add", json={"user_id": old_user_id, "fruit_id": fruit_id, "quantity": 2})

        # Associate cart
        response = client.post("/cart/associate-cart", json={
            "old_user_id": old_user_id,
            "new_user_id": new_user_id
        })

        assert response.status_code == 200
        assert f"user {new_user_id}".encode() in response.data

        # Confirm reassignment
        cart_items = Cart.query.filter_by(user_id=new_user_id).all()
        assert len(cart_items) > 0

def test_associate_cart_missing_fields(client):
    response = client.post("/cart/associate-cart", json={})
    assert response.status_code == 400
    assert b"old_user_id and new_user_id are required" in response.data

def test_associate_cart_target_user_not_found(client):
    response = client.post("/cart/associate-cart", json={
        "old_user_id": 1,
        "new_user_id": 9999
    })
    assert response.status_code == 404
    assert b"Target user not found" in response.data
