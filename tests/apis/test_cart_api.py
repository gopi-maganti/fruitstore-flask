import io
import re
import uuid
from unittest.mock import MagicMock, patch

import pytest

from app.models.cart import Cart
from app.routes.cart_api import cart_bp
from app.services import cart_service
from app.services.cart_service import (
    add_to_cart,
    clear_cart_for_user,
    delete_cart_item,
    get_cart_items_by_user,
)


def add_user(client, name=None, email=None):
    suffix = uuid.uuid4().hex[:6]
    name = name or f"User-{suffix}"
    email = email or f"user-{suffix}@example.com"
    phone = f"90000{int(suffix, 16) % 100000:05d}"

    response = client.post(
        "/user/add", json={"name": name, "email": email, "phone_number": phone}
    )

    # Helpful debug print in case of failure
    if response.status_code != 201:
        print("User add failed:", response.status_code, response.get_data(as_text=True))

    assert response.status_code == 201
    data = response.get_json()

    return response, data.get("user", {}).get("user_id")


def add_fruit(client, name=None):
    suffix = uuid.uuid4().hex[:6]
    name = name or f"Fruit-{suffix}"
    image = (io.BytesIO(b"fake-image-bytes"), "fruit.jpg")
    fruit_data = {
        "name": name,
        "description": "desc",
        "color": "Red",
        "size": "M",
        "has_seeds": "true",
        "weight": "1.0",
        "price": "10.0",
        "total_quantity": "50",
        "available_quantity": "50",
        "sell_by_date": "2030-01-01",
    }

    response = client.post(
        "/fruit/add",
        data={**fruit_data, "image": image},
        content_type="multipart/form-data",
    )
    assert response.status_code == 201
    data = response.get_json()
    return response, data["fruit"]["fruit_id"]


# -----------------------------
# ✅ Positive Test Cases
# -----------------------------


def test_add_to_cart_success(client):
    _, user_id = add_user(client)
    _, fruit_id = add_fruit(client)

    response = client.post(
        "/cart/add", json={"user_id": user_id, "fruit_id": fruit_id, "quantity": 3}
    )
    assert response.status_code == 201
    assert response.get_json()


def test_get_cart_by_user_id_success(client):
    _, user_id = add_user(client)
    _, fruit_id = add_fruit(client)

    client.post(
        "/cart/add", json={"user_id": user_id, "fruit_id": fruit_id, "quantity": 1}
    )
    response = client.get(f"/cart/{user_id}")
    assert response.status_code == 200
    assert isinstance(response.get_json(), list)


def test_associate_cart_success(client, app):
    with app.app_context():
        _, old_user_id = add_user(client, name="Old")
        _, new_user_id = add_user(client, name="New")
        _, fruit_id = add_fruit(client)

        client.post(
            "/cart/add",
            json={"user_id": old_user_id, "fruit_id": fruit_id, "quantity": 2},
        )

        response = client.post(
            "/cart/associate-cart",
            json={"old_user_id": old_user_id, "new_user_id": new_user_id},
        )

        assert response.status_code == 200
        assert f"user {new_user_id}".encode() in response.data

        cart_items = Cart.query.filter_by(user_id=new_user_id).all()
        assert len(cart_items) > 0


# -----------------------------
# ❌ Negative Test Cases
# -----------------------------


def test_add_to_cart_missing_fields(client):
    response = client.post("/cart/add", json={})
    assert response.status_code == 400
    assert b"error" in response.data


def test_add_to_cart_invalid_fruit(client):
    _, user_id = add_user(client)
    response = client.post(
        "/cart/add", json={"user_id": user_id, "fruit_id": 9999, "quantity": 1}
    )
    assert response.status_code == 404
    assert b"Fruit not found" in response.data


def test_associate_cart_missing_fields(client):
    response = client.post("/cart/associate-cart", json={})
    assert response.status_code == 400
    assert b"Both old_user_id and new_user_id are required" in response.data


def test_delete_cart_invalid_id(client):
    response = client.delete("/cart/delete/9999")
    assert response.status_code == 404
    assert b"Cart item not found" in response.data


def test_clear_cart_user_not_found(client):
    response = client.delete("/cart/clear/9999")
    assert response.status_code == 404
    assert b"No cart items to delete" in response.data


# --- FIXED MOCK TARGETS (patches where they're used, not where defined) ---


def test_get_cart_by_user_id_not_found(client):
    with patch.object(cart_service, "get_cart_items_by_user", return_value=None):
        response = client.get("/cart/999")
        assert response.status_code == 404
        assert b"No cart items found for this user" in response.data


def test_add_to_cart_service_returns_none(client):
    with patch.object(cart_service, "add_to_cart", return_value=None):
        payload = {"user_id": 1, "fruit_id": 1, "quantity": 2}
        response = client.post("/cart/add", json=payload)
        assert response.status_code == 500
        assert b"Internal Server Error" in response.data


def test_clear_cart_failure(client):
    with patch.object(cart_service, "clear_cart_for_user", return_value=False):
        response = client.delete("/cart/clear/999")
        assert response.status_code == 404
        assert b"No cart items to delete" in response.data


def test_update_cart_item_missing_quantity(client):
    response = client.put("/cart/update/1", json={})
    assert response.status_code == 400
    assert b"Field required" in response.data or b"Validation Error" in response.data


def test_update_cart_item_not_found(client):
    with patch.object(cart_service, "update_cart_item", return_value=None):
        response = client.put("/cart/update/999", json={"quantity": 2})
        assert response.status_code == 404
        assert b"Cart item not found" in response.data


@patch("app.routes.cart_api.db.session.commit", side_effect=Exception("DB fail"))
def test_clear_cart_exception(mock_commit, client):
    # You can optionally insert a real cart entry here if needed.
    response = client.delete("/cart/clear/1")
    assert response.status_code == 500
    assert b"Internal Server Error" in response.data


@patch("app.routes.cart_api.db.session.commit", side_effect=Exception("DB error"))
def test_delete_cart_item_exception(mock_commit, client):
    # You can optionally insert a cart item here if needed
    response = client.delete("/cart/delete/1")
    assert response.status_code == 500
    assert b"Internal Server Error" in response.data
