import pytest

# --------------------------------------
# ✅ Positive Test Cases
# --------------------------------------

def test_add_fruit_success(client, add_fruit):
    response = add_fruit(client)
    assert response.status_code == 201
    data = response.get_json()
    assert "fruit" in data
    assert data["fruit"]["name"] == "Test Fruit"

def test_get_all_fruits_success(client, add_fruit):
    add_fruit(client)
    response = client.get("/fruit/all")
    assert response.status_code == 200
    assert isinstance(response.get_json(), list)

def test_get_fruit_by_id_success(client, add_fruit):
    fruit_resp = add_fruit(client)
    fruit_id = fruit_resp.get_json()["fruit"]["fruit_id"]
    response = client.get(f"/fruit/{fruit_id}")
    assert response.status_code == 200
    data = response.get_json()
    assert data["fruit_id"] == fruit_id

def test_update_fruit_info_success(client, add_fruit):
    fruit_resp = add_fruit(client)
    fruit_id = fruit_resp.get_json()["fruit"]["fruit_id"]
    response = client.put(
        f"/fruit/update/{fruit_id}",
        json={"price": 12.5, "quantity": 20}
    )
    assert response.status_code == 200
    assert b"updated successfully" in response.data

def test_delete_fruit_success(client, add_fruit):
    fruit_resp = add_fruit(client)
    fruit_id = fruit_resp.get_json()["fruit"]["fruit_id"]
    response = client.delete(f"/fruit/delete/{fruit_id}")
    assert response.status_code == 200
    assert b"deleted successfully" in response.data

# --------------------------------------
# ❌ Negative Test Cases
# --------------------------------------

def test_add_fruit_invalid_data(client):
    response = client.post("/fruit/add", data={
        "name": "",
        "description": "desc",
        "color": "Green",
        "size": "L",
        "has_seeds": "true",
        "weight": "-1",
        "price": "-10",
        "total_quantity": "-50",
        "available_quantity": "-10",
        "sell_by_date": "2030-01-01"
    })
    assert response.status_code == 400
    assert b"Validation" in response.data or b"error" in response.data

def test_add_duplicate_fruit(client, add_fruit):
    add_fruit(client)
    response = add_fruit(client)
    assert response.status_code == 400
    assert b"already exists" in response.data

def test_get_fruit_by_invalid_id(client):
    response = client.get("/fruit/999999")
    assert response.status_code == 404
    assert b"not found" in response.data

def test_update_fruit_info_invalid_id(client):
    response = client.put("/fruit/update/999999", json={"price": 5})
    assert response.status_code == 404
    assert b"not found" in response.data

def test_delete_fruit_not_found(client):
    response = client.delete("/fruit/delete/999999")
    assert response.status_code == 404
    assert b"not found" in response.data
