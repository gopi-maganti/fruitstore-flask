import pytest

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