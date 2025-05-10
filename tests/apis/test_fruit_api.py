import io
import pytest

def test_get_all_fruits_empty(client):
    response = client.get("/fruit/")
    assert response.status_code == 200
    assert isinstance(response.get_json(), list)
    assert len(response.get_json()) == 0

def test_get_fruit_by_invalid_id(client):
    response = client.get("/fruit/999")
    assert response.status_code == 404
    assert b"Fruit not found" in response.data

def test_add_fruit_success(client):
    image_data = (io.BytesIO(b"fake image data"), "apple.jpg")
    payload = {
        "name": "Apple",
        "description": "Sweet and crunchy",
        "color": "Red",
        "size": "Medium",
        "has_seeds": "true",
        "weight": "0.2",
        "price": "1.5",
        "total_quantity": "100",
        "available_quantity": "80",
        "sell_by_date": "2030-12-31",
        "image": image_data
    }
    data = {k: v for k, v in payload.items() if k != "image"}
    file_data = {"image": image_data}
    response = client.post("/fruit/add", data={**data, **file_data}, content_type='multipart/form-data')
    assert response.status_code == 201
    assert b"Fruit and FruitInfo added successfully" in response.data

@pytest.mark.parametrize("payload, expected_error", [
    (
        {
            "name": "Orange", "description": "Citrus fruit", "color": "Orange", "size": "Medium", "has_seeds": "true",
            "weight": "0.3", "price": "1.2", "total_quantity": "50", "available_quantity": "40", "sell_by_date": ""
        },
        b"Invalid date format"
    ),
    (
        {
            "name": "", "description": "", "color": "", "size": "", "has_seeds": "", "weight": "", "price": "",
            "total_quantity": "", "available_quantity": "", "sell_by_date": ""
        },
        b"Invalid number field"
    )
])
def test_add_fruit_invalid_data(client, payload, expected_error):
    image_data = (io.BytesIO(b"fake image data"), "orange.jpg")
    payload["image"] = image_data
    data = {k: v for k, v in payload.items() if k != "image"}
    file_data = {"image": image_data}

    response = client.post("/fruit/add", data={**data, **file_data}, content_type='multipart/form-data')

    assert response.status_code == 400
    assert expected_error in response.data


def test_get_fruit_by_id(client):
    image_data = (io.BytesIO(b"fake image data"), "banana.jpg")
    response = client.post("/fruit/add", data={
        "name": "Banana",
        "description": "Yellow fruit",
        "color": "Yellow",
        "size": "Large",
        "has_seeds": "false",
        "weight": "0.25",
        "price": "0.8",
        "total_quantity": "150",
        "available_quantity": "140",
        "sell_by_date": "2030-10-10",
        "image": image_data
    }, content_type='multipart/form-data')

    fruit_id = response.get_json()["fruit"]["fruit_id"]
    get_response = client.get(f"/fruit/{fruit_id}")
    assert get_response.status_code == 200
    assert b"Banana" in get_response.data
