import pytest
from app.models.cart import Cart

# --------------------------------------
# ✅ Positive Test Cases
# --------------------------------------

def test_add_to_cart_success(client, add_user, add_fruit):
    fruit_resp = add_fruit(client)
    fruit_id = fruit_resp.get_json()["fruit"]["fruit_id"]

    user_resp, user_id = add_user(client, email="success@example.com")
    cart_payload = {"user_id": user_id, "fruit_id": fruit_id, "quantity": 3}
    response = client.post("/cart/add", json=cart_payload)

    assert response.status_code == 201
    assert b"Item added to cart successfully" in response.data

def test_get_cart_empty(client, add_user):
    _, user_id = add_user(client, email="empty@example.com", phone="1111111111")
    response = client.get(f"/cart/{user_id}")
    assert response.status_code == 404
    assert b"No cart items found for this user" in response.data

def test_associate_cart_success(client, app, add_user, add_fruit):
    with app.app_context():
        _, old_user_id = add_user(client, name="Old", email="old@example.com")
        _, new_user_id = add_user(client, name="New", email="new@example.com")

        fruit_resp = add_fruit(client)
        fruit_id = fruit_resp.get_json()["fruit"]["fruit_id"]
        client.post("/cart/add", json={"user_id": old_user_id, "fruit_id": fruit_id, "quantity": 2})

        response = client.post("/cart/associate-cart", json={
            "old_user_id": old_user_id,
            "new_user_id": new_user_id
        })

        assert response.status_code == 200
        assert f"user {new_user_id}".encode() in response.data

        cart_items = Cart.query.filter_by(user_id=new_user_id).all()
        assert len(cart_items) > 0

# --------------------------------------
# ❌ Negative Test Cases
# --------------------------------------

def test_add_to_cart_invalid_payload(client):
    response = client.post("/cart/add", json={})
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data
    assert any(e["loc"] == ["fruit_id"] for e in data["error"])
    assert any(e["loc"] == ["quantity"] for e in data["error"])

def test_add_to_cart_fruit_not_found(client, add_user):
    _, user_id = add_user(client, email="fruitnotfound@example.com")
    payload = {"user_id": user_id, "fruit_id": 999, "quantity": 2}
    response = client.post("/cart/add", json=payload)
    assert response.status_code == 404
    assert b"FruitInfo not found" in response.data

def test_get_cart_invalid_user(client):
    response = client.get("/cart/999")
    assert response.status_code == 404
    assert b"No cart items found for this user" in response.data

def test_update_cart_item_not_found(client):
    response = client.put("/cart/update/999", json={"quantity": 5})
    assert response.status_code == 404
    assert b"Cart item not found" in response.data

def test_associate_cart_missing_fields(client):
    response = client.post("/cart/associate-cart", json={})
    assert response.status_code == 400
    assert b"old_user_id and new_user_id are required" in response.data

def test_associate_cart_target_user_not_found(client, add_user):
    _, old_user_id = add_user(client, email="assoc-old@example.com")
    response = client.post("/cart/associate-cart", json={
        "old_user_id": old_user_id,
        "new_user_id": 9999
    })
    assert response.status_code == 404
    assert b"Target user not found" in response.data
