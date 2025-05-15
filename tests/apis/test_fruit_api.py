import io

import pytest

"""
Positive Test Cases for Fruit API
"""


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
        "image": image_data,
    }
    data = {k: v for k, v in payload.items() if k != "image"}
    file_data = {"image": image_data}
    response = client.post(
        "/fruit/add", data={**data, **file_data}, content_type="multipart/form-data"
    )
    assert response.status_code == 201
    assert b"Fruit and FruitInfo added successfully" in response.data


def test_get_all_fruits_success(client):
    image_data = (io.BytesIO(b"fake image data"), "banana.jpg")
    payload = {
        "name": "Banana",
        "description": "Tasty and healthy",
        "color": "Yellow",
        "size": "Medium",
        "has_seeds": "false",
        "weight": "0.15",
        "price": "0.5",
        "total_quantity": "200",
        "available_quantity": "150",
        "sell_by_date": "2030-12-31",
        "image": image_data,
    }
    data = {k: v for k, v in payload.items() if k != "image"}
    file_data = {"image": image_data}
    client.post(
        "/fruit/add", data={**data, **file_data}, content_type="multipart/form-data"
    )

    response = client.get("/fruit/")
    assert response.status_code == 200
    assert isinstance(response.get_json(), list)
    assert len(response.get_json()) > 0


def test_get_fruit_by_id_success(client):
    image_data = (io.BytesIO(b"fake image data"), "banana.jpg")
    response = client.post(
        "/fruit/add",
        data={
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
            "image": image_data,
        },
        content_type="multipart/form-data",
    )

    fruit_id = response.get_json()["fruit"]["fruit_id"]
    get_response = client.get(f"/fruit/{fruit_id}")
    assert get_response.status_code == 200
    assert b"Banana" in get_response.data


def test_update_fruit_info_success(client):
    image_data = (io.BytesIO(b"fake image data"), "kiwi.jpg")
    response = client.post(
        "/fruit/add",
        data={
            "name": "Kiwi",
            "description": "Green fruit",
            "color": "Green",
            "size": "Small",
            "has_seeds": "true",
            "weight": "0.1",
            "price": "2.0",
            "total_quantity": "50",
            "available_quantity": "45",
            "sell_by_date": "2030-01-10",
            "image": image_data,
        },
        content_type="multipart/form-data",
    )

    fruit_id = response.get_json()["fruit"]["fruit_id"]

    update_payload = {
        "price": 2.5,
        "total_quantity": 60,
        "available_quantity": 55,
        "sell_by_date": "2030-01-10T00:00:00",
    }

    update_response = client.put(f"/fruit/{fruit_id}", json=update_payload)
    assert update_response.status_code == 200
    assert b"updated successfully" in update_response.data


def test_delete_fruit_success(client):
    image_data = (io.BytesIO(b"fake image data"), "grape.jpg")
    response = client.post(
        "/fruit/add",
        data={
            "name": "Grape",
            "description": "Purple fruit",
            "color": "Purple",
            "size": "Small",
            "has_seeds": "false",
            "weight": "0.05",
            "price": "0.3",
            "total_quantity": "300",
            "available_quantity": "280",
            "sell_by_date": "2030-06-01",
            "image": image_data,
        },
        content_type="multipart/form-data",
    )

    fruit_id = response.get_json()["fruit"]["fruit_id"]

    delete_response = client.delete("/fruit/delete", json={"ids": [fruit_id]})
    assert delete_response.status_code == 200
    assert b"Deleted 1 fruit(s) successfully" in delete_response.data


"""
Negative Test Cases for Fruit API
"""


def test_get_all_fruits_empty(client):
    response = client.get("/fruit/")
    assert response.status_code == 200
    assert isinstance(response.get_json(), list)
    assert len(response.get_json()) == 0


def test_get_fruit_by_invalid_id(client):
    response = client.get("/fruit/999")
    assert response.status_code == 404
    assert b"Fruit not found" in response.data


@pytest.mark.parametrize(
    "payload, expected_error",
    [
        (
            {
                "name": "Orange",
                "description": "Citrus fruit",
                "color": "Orange",
                "size": "Medium",
                "has_seeds": "true",
                "weight": "0.3",
                "price": "1.2",
                "total_quantity": "50",
                "available_quantity": "40",
                "sell_by_date": "",
            },
            b"Invalid date format",
        ),
        (
            {
                "name": "",
                "description": "",
                "color": "",
                "size": "",
                "has_seeds": "",
                "weight": "",
                "price": "",
                "total_quantity": "",
                "available_quantity": "",
                "sell_by_date": "",
            },
            b"Invalid number field",
        ),
        (
            {
                "name": "Tomato",
                "description": "Red fruit",
                "color": "Red",
                "size": "Small",
                "has_seeds": "true",
                "weight": "heavy",
                "price": "1.0",
                "total_quantity": "30",
                "available_quantity": "20",
                "sell_by_date": "2030-10-10",
            },
            b"Invalid number field",
        ),
        (
            {
                "name": "Lemon",
                "description": "Sour",
                "color": "Yellow",
                "size": "Small",
                "has_seeds": "true",
                "weight": "0.2",
                "price": "cheap",
                "total_quantity": "50",
                "available_quantity": "30",
                "sell_by_date": "2030-09-01",
            },
            b"Invalid number field",
        ),
        (
            {
                "name": "Guava",
                "description": "Sweet and green",
                "color": "Green",
                "size": "Medium",
                "has_seeds": "true",
                "weight": "0.3",
                "price": "1.2",
                "total_quantity": "50",
                "available_quantity": "50",
                "sell_by_date": "2020-01-01",
            },
            b"sell_by_date must be a future date",
        ),
    ],
)
def test_add_fruit_invalid_data(client, payload, expected_error):
    image_data = (io.BytesIO(b"fake image data"), "test.jpg")
    payload["image"] = image_data
    data = {k: v for k, v in payload.items() if k != "image"}
    file_data = {"image": image_data}

    response = client.post(
        "/fruit/add", data={**data, **file_data}, content_type="multipart/form-data"
    )
    assert response.status_code == 400
    assert expected_error in response.data


def test_add_fruit_duplicate(client):
    def image():
        return (io.BytesIO(b"fake image data"), "pear.jpg")

    payload = {
        "name": "Pear",
        "description": "Juicy green fruit",
        "color": "Green",
        "size": "Medium",
        "has_seeds": "true",
        "weight": "0.2",
        "price": "1.0",
        "total_quantity": "100",
        "available_quantity": "90",
        "sell_by_date": "2031-01-01",
    }

    client.post(
        "/fruit/add",
        data={**payload, "image": image()},
        content_type="multipart/form-data",
    )
    response = client.post(
        "/fruit/add",
        data={**payload, "image": image()},
        content_type="multipart/form-data",
    )

    assert response.status_code == 400
    assert b"already exists" in response.data


def test_update_fruit_info_invalid_id(client):
    update_payload = {
        "price": 3.0,
        "total_quantity": 100,
        "sell_by_date": "2031-01-01T00:00:00",
    }

    response = client.put("/fruit/999", json=update_payload)
    assert response.status_code == 404
    assert b"Fruit not found" in response.data


def test_delete_fruit_not_found(client):
    response = client.delete("/fruit/delete", json={"ids": [-100]})
    assert response.status_code == 404
    assert b"Fruit not found" in response.data
