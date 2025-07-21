import pytest
from unittest.mock import patch
from io import BytesIO
from app.services import fruit_service


# Utility: Dummy image file
def dummy_file():
    return (BytesIO(b"test image data"), "test.jpg")


# --------------------------------------
# ✅ Positive Test Cases
# --------------------------------------

def test_add_fruit_success(client, add_fruit):
    response = add_fruit(client)
    assert response.status_code == 201
    data = response.get_json()
    assert "fruit" in data
    assert data["fruit"]["name"].startswith("Test Fruit")


def test_get_all_fruits_success(client, add_fruit):
    add_fruit(client)
    response = client.get("/fruit/all")
    assert response.status_code == 200
    assert isinstance(response.get_json(), list)


def test_get_fruit_by_id_success(client, add_fruit):
    fruit_resp = add_fruit(client)
    fruit_data = fruit_resp.get_json()["fruit"]
    fruit_id = fruit_data["fruit_id"]

    response = client.get(f"/fruit/{fruit_id}")
    assert response.status_code == 200
    data = response.get_json()
    assert data["fruit_id"] == fruit_id


def test_update_fruit_info_success(client, add_fruit):
    fruit_resp = add_fruit(client)
    fruit_data = fruit_resp.get_json()["fruit"]
    fruit_id = fruit_data["fruit_id"]

    response = client.put(
        f"/fruit/update/{fruit_id}",
        json={"price": 12.5, "quantity": 20}
    )
    assert response.status_code == 200
    assert b"updated successfully" in response.data


def test_delete_fruit_success(client, add_fruit):
    fruit_resp = add_fruit(client)
    fruit_data = fruit_resp.get_json()["fruit"]
    fruit_id = fruit_data["fruit_id"]

    response = client.delete(f"/fruit/delete/{fruit_id}")
    assert response.status_code == 200
    data = response.get_json()
    assert data["message"] == "Deleted 1 fruit successfully"


# --------------------------------------
# ❌ Negative Test Cases
# --------------------------------------

def test_add_fruit_missing_fields(client):
    data = {
        "name": "",
        "description": "desc",
        "color": "Green",
        "size": "L",
        "has_seeds": "true",
        "weight": "-1",
        "price": "-10",
        "total_quantity": "-50",
        "available_quantity": "-10"
    }
    file = {"image": dummy_file()}
    response = client.post("/fruit/add", data={**data, **file}, content_type="multipart/form-data")
    assert response.status_code == 400
    assert b"Validation" in response.data or b"error" in response.data


def test_add_fruit_invalid_sell_by_date(client):
    data = {
        "name": "Banana",
        "description": "desc",
        "color": "Yellow",
        "size": "M",
        "has_seeds": "false",
        "weight": "1",
        "price": "2.0",
        "total_quantity": "10",
        "available_quantity": "10",
        "sell_by_date": "2000-01-01"
    }
    file = {"image": dummy_file()}
    response = client.post("/fruit/add", data={**data, **file}, content_type="multipart/form-data")
    assert response.status_code == 400
    assert b"sell_by_date must be a future date" in response.data


def test_add_duplicate_fruit(client, add_fruit):
    unique_name = "Test Fruit Duplicate"
    add_fruit(client, name=unique_name)
    response = add_fruit(client, name=unique_name)
    assert response.status_code == 400
    assert b"already exists" in response.data


def test_add_fruit_failure(client):
    data = {
        "name": "Mango",
        "description": "desc",
        "color": "Orange",
        "size": "L",
        "has_seeds": "true",
        "weight": "1.2",
        "price": "2.5",
        "total_quantity": "5",
        "available_quantity": "5",
        "sell_by_date": "2099-12-31"
    }
    file = {"image": dummy_file()}
    with patch.object(fruit_service, "add_fruit_with_info", return_value=None):
        response = client.post("/fruit/add", data={**data, **file}, content_type="multipart/form-data")
        assert response.status_code == 500
        assert b"Upload failed" in response.data


def test_get_fruit_by_invalid_id(client):
    response = client.get("/fruit/999999")
    assert response.status_code == 404
    assert b"not found" in response.data


def test_update_fruit_info_invalid_id(client):
    response = client.put("/fruit/update/999999", json={"price": 5})
    assert response.status_code == 404
    assert b"not found" in response.data


def test_update_fruit_invalid_id(client):
    with patch.object(fruit_service, "update_fruit_info", return_value=None):
        response = client.put("/fruit/update/9999", json={
            "name": "Papaya",
            "price": 1.0,
            "quantity": 8,
            "sell_by_date": "2099-01-01"
        })
        assert response.status_code == 404
        assert b"Fruit not found" in response.data


def test_update_fruit_invalid_data(client, add_fruit):
    fruit_resp = add_fruit(client)
    fruit_data = fruit_resp.get_json()["fruit"]
    fruit_id = fruit_data["fruit_id"]

    with patch.object(fruit_service, "update_fruit_info", return_value=None):
        response = client.put(f"/fruit/update/{fruit_id}", json={
            "name": "Papaya",
            "price": 1.0,
            "quantity": "invalid",
            "sell_by_date": "2099-01-01"
        })
        assert response.status_code == 404
        assert b"Invalid data" in response.data or b"error" in response.data


def test_delete_fruit_not_found(client):
    with patch.object(fruit_service, "delete_fruits", return_value=0):
        response = client.delete("/fruit/delete/9999")
        assert response.status_code == 404
        assert b"No fruits found to delete" in response.data


def test_add_fruit_no_image(client):
    response = client.post("/fruit/add", data={})
    assert response.status_code == 400
    assert b"No image file received" in response.data


def test_get_all_fruits_exception(client):
    with patch.object(fruit_service, "get_all_fruits", side_effect=Exception("DB failure")):
        response = client.get("/fruit/all")
        assert response.status_code == 500
        assert b"DB failure" in response.data


def test_get_fruit_by_id_exception(client):
    with patch.object(fruit_service, "get_fruit_by_id", side_effect=Exception("lookup failed")):
        response = client.get("/fruit/1")
        assert response.status_code == 500
        assert b"lookup failed" in response.data


def test_search_fruits_value_error(client):
    with patch.object(fruit_service, "search_fruits", side_effect=ValueError("invalid filter")):
        response = client.get("/fruit/search?search=papaya")
        assert response.status_code == 400
        assert b"invalid filter" in response.data


def test_search_fruits_exception(client):
    with patch.object(fruit_service, "search_fruits", side_effect=Exception("search fail")):
        response = client.get("/fruit/search?search=banana")
        assert response.status_code == 500
        assert b"search fail" in response.data


def test_delete_fruit_no_ids(client):
    response = client.delete("/fruit/delete", json={})
    assert response.status_code == 400
    assert b"No fruit ID" in response.data


def test_delete_fruit_not_found_ids(client):
    with patch.object(fruit_service, "delete_fruits", return_value=0):
        response = client.delete("/fruit/delete", json={"ids": [9999]})
        assert response.status_code == 404
        assert b"No fruits found to delete" in response.data


def test_delete_fruit_exception(client):
    with patch.object(fruit_service, "delete_fruits", side_effect=Exception("delete fail")):
        response = client.delete("/fruit/delete", json={"ids": [1]})
        assert response.status_code == 500
        assert b"delete fail" in response.data
