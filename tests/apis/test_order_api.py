from unittest.mock import patch

import pytest

from app.services import order_service
from aws_utils import s3_utils

# --------------------------------------
# Positive Test Cases
# --------------------------------------


def test_add_order_success(client, setup_order_data):
    data = setup_order_data
    response = client.post(
        f"/order/place/{data['user_id']}", json={"cart_ids": [data["cart_id"]]}
    )
    assert response.status_code == 201
    assert b"Order placed" in response.data


def test_get_order_by_user_id_success(client, setup_order_data):
    data = setup_order_data
    client.post(f"/order/place/{data['user_id']}", json={"cart_ids": [data["cart_id"]]})
    response = client.get(f"/order/history/{data['user_id']}")
    assert response.status_code == 200
    assert isinstance(response.get_json(), list)


def test_get_all_orders_success(client, setup_order_data):
    data = setup_order_data
    client.post(f"/order/place/{data['user_id']}", json={"cart_ids": [data["cart_id"]]})
    response = client.get("/order/all")
    assert response.status_code == 200
    assert isinstance(response.get_json(), list)


# --------------------------------------
# Negative Test Cases
# --------------------------------------


def test_add_order_invalid_user_id(client, setup_order_data):
    data = setup_order_data
    response = client.post("/order/place/9999", json={"cart_ids": [data["cart_id"]]})
    assert response.status_code == 400
    assert b"User not found" in response.data


def test_add_order_invalid_cart_id(client, setup_order_data):
    data = setup_order_data
    response = client.post(f"/order/place/{data['user_id']}", json={"cart_ids": [9999]})
    assert response.status_code == 400
    assert b"Cart is empty" in response.data


def test_add_order_invalid_cart_ids_type(client, setup_order_data):
    data = setup_order_data
    response = client.post(
        f"/order/place/{data['user_id']}", json={"cart_ids": "not_a_list"}
    )
    assert response.status_code == 400
    assert b"Input should be a valid list" in response.data


def test_add_order_empty_cart_ids(client, setup_order_data):
    data = setup_order_data
    response = client.post(f"/order/place/{data['user_id']}", json={"cart_ids": []})
    assert response.status_code == 400
    assert b"Cart is empty" in response.data


def test_get_order_by_invalid_user_id(client):
    response = client.get("/order/history/9999")
    assert response.status_code == 404
    assert b"No orders found for this user" in response.data


def test_place_order_unexpected_exception(client, setup_order_data):
    data = setup_order_data
    with patch.object(order_service, "place_order", side_effect=Exception("DB Error")):
        response = client.post(
            f"/order/place/{data['user_id']}", json={"cart_ids": [data["cart_id"]]}
        )
        assert response.status_code == 500
        assert b"DB Error" in response.data


def test_get_order_history_exception(client):
    with patch.object(
        order_service, "get_order_history", side_effect=Exception("Fetch failed")
    ):
        response = client.get("/order/history/1")
        assert response.status_code == 500
        assert b"Fetch failed" in response.data


def test_get_all_orders_exception(client):
    with patch.object(
        order_service, "get_all_orders", side_effect=Exception("Global fetch fail")
    ):
        response = client.get("/order/all")
        assert response.status_code == 500
        assert b"Global fetch fail" in response.data


def test_get_all_orders_not_found(client):
    with patch.object(order_service, "get_all_orders", return_value=None):
        response = client.get("/order/all")
        assert response.status_code == 404
        assert b"No orders found" in response.data
