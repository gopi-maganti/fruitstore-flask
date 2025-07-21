import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from app.services import order_service


@pytest.fixture(scope="module")
def app_context():
    from app import create_app
    app = create_app()
    with patch("app.extensions.db.session.remove"):  # optional safety net
        with app.app_context():
            yield

# -------------------------
# ✅ place_order tests
# -------------------------

@patch("app.services.order_service.db.session.commit")
@patch("app.services.order_service.db.session.delete")
@patch("app.services.order_service.db.session.add")
@patch("app.services.order_service.Cart.query")
@patch("app.services.order_service.User.query")
def test_place_order_success(mock_user_q, mock_cart_q, mock_add, mock_delete, mock_commit, app_context):
    user = MagicMock()
    mock_user_q.get.return_value = user

    cart_item = MagicMock()
    cart_item.quantity = 2
    cart_item.fruit_info.available_quantity = 10
    cart_item.fruit_info.price = 3.0
    cart_item.fruit_id = 1
    cart_item.info_id = 1

    mock_cart_q.filter_by.return_value.all.return_value = [cart_item]
    mock_cart_q.filter.return_value.all.return_value = [cart_item]

    result = order_service.place_order(user_id=1, cart_ids=[1])
    assert result["order_total"] == 6.0
    assert isinstance(result["order_items"], list)
    mock_commit.assert_called_once()


@patch("app.services.order_service.User.query")
def test_place_order_user_not_found(mock_user_q, app_context):
    mock_user_q.get.return_value = None
    with pytest.raises(ValueError, match="User not found"):
        order_service.place_order(user_id=1, cart_ids=[1])


@patch("app.services.order_service.User.query")
def test_place_order_empty_cart_ids(mock_user_q, app_context):
    mock_user_q.get.return_value = MagicMock()
    with pytest.raises(ValueError, match="Cart is empty"):
        order_service.place_order(user_id=1, cart_ids=[])


@patch("app.services.order_service.Cart.query")
@patch("app.services.order_service.User.query")
def test_place_order_cart_not_found(mock_user_q, mock_cart_q, app_context):
    mock_user_q.get.return_value = MagicMock()
    mock_cart_q.filter.return_value.all.return_value = []
    with pytest.raises(ValueError, match="Cart is empty"):
        order_service.place_order(user_id=1, cart_ids=[999])


@patch("app.services.order_service.Cart.query")
@patch("app.services.order_service.User.query")
def test_place_order_cart_items_missing(mock_user_q, mock_cart_q, app_context):
    mock_user_q.get.return_value = MagicMock()
    mock_cart_q.filter.return_value.all.return_value = [MagicMock()]
    mock_cart_q.filter_by.return_value.all.return_value = []
    with pytest.raises(ValueError, match="Cart is empty"):
        order_service.place_order(user_id=1, cart_ids=[1])


@patch("app.services.order_service.Cart.query")
@patch("app.services.order_service.User.query")
def test_place_order_insufficient_stock(mock_user_q, mock_cart_q, app_context):
    mock_user_q.get.return_value = MagicMock()

    cart = MagicMock()
    cart.quantity = 5
    cart.fruit_info.available_quantity = 3
    mock_cart_q.filter.return_value.all.return_value = [cart]
    mock_cart_q.filter_by.return_value.all.return_value = [cart]

    with pytest.raises(ValueError, match="Not enough stock"):
        order_service.place_order(user_id=1, cart_ids=[1])


@patch("app.services.order_service.db.session.rollback")
@patch("app.services.order_service.db.session.commit", side_effect=Exception("DB failure"))
@patch("app.services.order_service.Cart.query")
@patch("app.services.order_service.User.query")
def test_place_order_commit_fail(mock_user_q, mock_cart_q, mock_commit, mock_rollback, app_context):
    user = MagicMock()
    mock_user_q.get.return_value = user

    cart = MagicMock()
    cart.quantity = 1
    cart.fruit_info.available_quantity = 2
    cart.fruit_info.price = 3.0
    cart.fruit_id = 1
    cart.info_id = 1

    mock_cart_q.filter.return_value.all.return_value = [cart]
    mock_cart_q.filter_by.return_value.all.return_value = [cart]

    with pytest.raises(Exception, match="DB failure"):
        order_service.place_order(user_id=1, cart_ids=[1])
    mock_rollback.assert_called_once()


# -------------------------
# ✅ get_order_history tests
# -------------------------

@patch("app.services.order_service.Order.query")
def test_get_order_history_success(mock_query, app_context):
    mock_order = MagicMock()
    mock_order.as_dict.return_value = {"id": 1}
    mock_query.filter_by.return_value.order_by.return_value.all.return_value = [mock_order]

    result = order_service.get_order_history(1)
    assert isinstance(result, list)
    assert result[0]["id"] == 1


@patch("app.services.order_service.Order.query")
def test_get_order_history_exception(mock_query, app_context):
    mock_query.filter_by.side_effect = Exception("fail")
    with pytest.raises(Exception, match="fail"):
        order_service.get_order_history(1)


# -------------------------
# ✅ get_all_orders tests
# -------------------------

class FakeOrder:
    def as_dict(self):
        return {"id": 1}

@patch("app.services.order_service.Order.query")
def test_get_all_orders_success(mock_query, app_context):
    mock_query.order_by.return_value.all.return_value = [FakeOrder()]
    result = order_service.get_all_orders()
    assert result == [{"id": 1}]


@patch("app.services.order_service.Order.query")
def test_get_order_history_success(mock_query, app_context):
    mock_query.filter_by.return_value.order_by.return_value.all.return_value = [FakeOrder()]
    result = order_service.get_order_history(1)
    assert result == [{"id": 1}]

