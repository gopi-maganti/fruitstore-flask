from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from app.models.fruit import Fruit, FruitInfo
from app.services import fruit_service


@pytest.fixture(scope="module")
def app_context():
    from app import create_app

    app = create_app()
    with app.app_context():
        yield


# -------------------------------
# ✅ add_fruit_with_info
# -------------------------------


@patch("app.services.fruit_service.db.session.commit")
@patch("app.services.fruit_service.db.session.flush")
@patch("app.services.fruit_service.db.session.add")
@patch("app.services.fruit_service.FruitInfo")
@patch("app.services.fruit_service.Fruit")
def test_add_fruit_with_info_success(
    mock_fruit, mock_fruit_info, mock_add, mock_flush, mock_commit, app_context
):
    mock_fruit_instance = MagicMock()
    mock_fruit_instance.fruit_id = 1
    mock_fruit_instance.exists.return_value = False
    mock_fruit.return_value = mock_fruit_instance

    mock_fruit_info_instance = MagicMock()
    mock_fruit_info_instance.exists.return_value = False
    mock_fruit_info.return_value = mock_fruit_info_instance

    data = {
        "name": "Apple",
        "color": "Red",
        "size": "M",
        "has_seeds": True,
        "weight": 1.2,
        "price": 3.0,
        "total_quantity": 100,
        "available_quantity": 100,
        "sell_by_date": datetime.utcnow(),
    }

    fruit, info = fruit_service.add_fruit_with_info(data, "http://image.jpg")
    assert fruit == mock_fruit_instance
    assert info == mock_fruit_info_instance


@patch("app.services.fruit_service.db.session.rollback")
@patch("app.services.fruit_service.Fruit")
def test_add_fruit_duplicate_fruit(mock_fruit, mock_rollback, app_context):
    mock_fruit_instance = MagicMock()
    mock_fruit_instance.exists.return_value = True
    mock_fruit.return_value = mock_fruit_instance

    data = {
        "name": "Apple",
        "color": "Red",
        "size": "M",
        "has_seeds": True,
        "weight": 1.2,
        "price": 3.0,
        "total_quantity": 100,
        "available_quantity": 100,
        "sell_by_date": datetime.utcnow(),
    }

    with pytest.raises(ValueError, match="already exists"):
        fruit_service.add_fruit_with_info(data, "http://image.jpg")


@patch("app.services.fruit_service.db.session.rollback")
@patch("app.services.fruit_service.db.session.flush", side_effect=Exception("fail"))
@patch("app.services.fruit_service.Fruit")
def test_add_fruit_with_info_db_failure(
    mock_fruit, mock_flush, mock_rollback, app_context
):
    fruit_mock = MagicMock()
    fruit_mock.exists.return_value = False
    mock_fruit.return_value = fruit_mock

    data = {
        "name": "Pear",
        "color": "Green",
        "size": "S",
        "has_seeds": True,
        "weight": 1.0,
        "price": 2.0,
        "total_quantity": 10,
        "available_quantity": 10,
        "sell_by_date": datetime.utcnow(),
    }

    with pytest.raises(Exception, match="fail"):
        fruit_service.add_fruit_with_info(data, "image")
    mock_rollback.assert_called_once()


# -------------------------------
# ✅ get_all_fruits
# -------------------------------


@patch("app.services.fruit_service.FruitInfo.query")
@patch("app.services.fruit_service.Fruit.query")
def test_get_all_fruits_returns_list(mock_fruit_query, mock_info_query, app_context):
    mock_fruit = MagicMock()
    mock_fruit.fruit_id = 1
    mock_fruit.to_dict.return_value = {"name": "Apple"}

    mock_info = MagicMock()
    mock_info.fruit_id = 1
    mock_info.info_id = 10
    mock_info.weight = 1.0
    mock_info.price = 2.0
    mock_info.total_quantity = 50
    mock_info.available_quantity = 25
    mock_info.sell_by_date.isoformat.return_value = "2030-01-01"

    mock_fruit_query.all.return_value = [mock_fruit]
    mock_info_query.all.return_value = [mock_info]

    results = fruit_service.get_all_fruits()
    assert isinstance(results, list)
    assert results[0]["name"] == "Apple"
    assert results[0]["info_id"] == 10


# -------------------------------
# ✅ get_fruit_by_id
# -------------------------------


@patch("app.services.fruit_service.FruitInfo.query")
@patch("app.services.fruit_service.Fruit.query")
def test_get_fruit_by_id_success(mock_fruit_query, mock_info_query, app_context):
    fruit = MagicMock()
    fruit.to_dict.return_value = {"name": "Banana"}
    info = MagicMock()
    info.info_id = 5
    info.sell_by_date.isoformat.return_value = "2030-01-01"
    mock_fruit_query.get.return_value = fruit
    mock_info_query.filter_by.return_value.first.return_value = info

    result = fruit_service.get_fruit_by_id(1)
    assert result["name"] == "Banana"
    assert result["info_id"] == 5


@patch("app.services.fruit_service.FruitInfo.query")
def test_search_fruits_success(mock_query, app_context):
    mock_q = MagicMock()
    mock_info = MagicMock()
    mock_info.fruit.to_dict.return_value = {"name": "Lemon"}
    mock_info.sell_by_date.isoformat.return_value = "2030-01-01"
    mock_q.all.return_value = [mock_info]
    mock_query.join.return_value = mock_q

    result = fruit_service.search_fruits({"search": "lem"})
    assert isinstance(result, list)


@patch("app.services.fruit_service.FruitInfo.query")
def test_search_fruits_exception(mock_query, app_context):
    mock_query.join.side_effect = Exception("fail")
    with pytest.raises(Exception, match="fail"):
        fruit_service.search_fruits({"search": "lem"})


# -------------------------------
# ✅ update_fruit_info
# -------------------------------


@patch("app.services.fruit_service.db.session.commit")
@patch("app.services.fruit_service.FruitInfo.query")
@patch("app.services.fruit_service.Fruit.query")
def test_update_fruit_info_success(
    mock_fruit_query, mock_info_query, mock_commit, app_context
):
    mock_fruit = MagicMock()
    mock_info = MagicMock()
    mock_fruit_query.get.return_value = mock_fruit
    mock_info_query.filter_by.return_value.first.return_value = mock_info

    data = {"price": 4.5, "sell_by_date": "2030-01-01T00:00:00"}
    updated_info = fruit_service.update_fruit_info(1, data)

    assert updated_info == mock_info
    mock_commit.assert_called_once()


from app.models.fruit import Fruit


@patch("app.services.fruit_service.db.session.rollback")
@patch("app.services.fruit_service.db.session.flush", side_effect=Exception("fail"))
@patch("app.services.fruit_service.db.session.add")
def test_add_fruit_with_info_db_failure(
    mock_add, mock_flush, mock_rollback, app_context
):
    data = {
        "name": "Pear",
        "color": "Green",
        "size": "S",
        "has_seeds": True,
        "weight": 1.0,
        "price": 2.0,
        "total_quantity": 10,
        "available_quantity": 10,
        "sell_by_date": datetime.utcnow(),
    }

    # Patch Fruit.exists to return False
    with patch.object(Fruit, "exists", return_value=False):
        with pytest.raises(Exception, match="fail"):
            fruit_service.add_fruit_with_info(data, "image")

    mock_rollback.assert_called_once()


# -------------------------------
# ✅ delete_fruits
# -------------------------------


def test_delete_fruits_success(app_context):
    Cart = MagicMock()
    Order = MagicMock()
    FruitInfo = MagicMock()
    Fruit = MagicMock()
    session = MagicMock()

    Cart.query.filter_by.return_value.delete.return_value = 1
    Order.query.filter_by.return_value.delete.return_value = 1
    FruitInfo.query.filter_by.return_value.delete.return_value = 1
    Fruit.query.get.return_value = MagicMock()

    with patch.dict(
        "sys.modules",
        {
            "app.models.cart": MagicMock(Cart=Cart),
            "app.models.orders": MagicMock(Order=Order),
        },
    ), patch("app.services.fruit_service.FruitInfo", FruitInfo), patch(
        "app.services.fruit_service.Fruit", Fruit
    ), patch(
        "app.services.fruit_service.db.session", session
    ):

        result = fruit_service.delete_fruits([1])
        assert result == 1
        session.delete.assert_called_once_with(Fruit.query.get.return_value)
        session.commit.assert_called_once()
