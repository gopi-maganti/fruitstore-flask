import pytest
from unittest.mock import patch, MagicMock
from app import create_app
from app.services import cart_service
from app.models.cart import Cart
from app.models.fruit import FruitInfo
from app.models.users import User


@pytest.fixture(scope="module")
def app_context():
    app = create_app()
    with app.app_context():
        yield

# --------------------------------------
# ✅ add_to_cart tests
# --------------------------------------

@patch("app.services.cart_service.FruitInfo.query")
def test_add_to_cart_fruit_not_found(mock_fruit_query, app_context):
    mock_fruit_query.filter_by.return_value.first.return_value = None

    with pytest.raises(ValueError, match="Fruit not found"):
        cart_service.add_to_cart(user_id=1, fruit_id=1, quantity=2)


@patch("app.services.cart_service.User.query")
@patch("app.services.cart_service.FruitInfo.query")
def test_add_to_cart_user_not_found(mock_fruit_query, mock_user_query, app_context):
    fruit_mock = MagicMock()
    fruit_mock.price = 2.0
    fruit_mock.info_id = 1
    mock_fruit_query.filter_by.return_value.first.return_value = fruit_mock
    mock_user_query.get.return_value = None

    with pytest.raises(ValueError, match="User not found"):
        cart_service.add_to_cart(user_id=123, fruit_id=1, quantity=2)


@patch("app.services.cart_service.db.session.commit", side_effect=Exception("DB failure"))
@patch("app.services.cart_service.db.session.add")
@patch("app.services.cart_service.User.query")
@patch("app.services.cart_service.FruitInfo.query")
def test_add_to_cart_db_failure(mock_fruit_query, mock_user_query, mock_add, mock_commit, app_context):
    fruit = MagicMock()
    fruit.price = 1.5
    fruit.info_id = 1
    mock_fruit_query.filter_by.return_value.first.return_value = fruit
    mock_user_query.get.return_value = User(user_id=1)

    with pytest.raises(Exception, match="DB failure"):
        cart_service.add_to_cart(user_id=1, fruit_id=1, quantity=3)


# --------------------------------------
# ✅ get_cart_items_by_user tests
# --------------------------------------

@patch("app.services.cart_service.Cart.query")
def test_get_cart_items_by_user_returns_list(mock_cart_query, app_context):
    mock_cart1 = MagicMock()
    mock_cart2 = MagicMock()
    mock_cart_query.filter_by.return_value.all.return_value = [mock_cart1, mock_cart2]

    result = cart_service.get_cart_items_by_user(user_id=1)
    assert isinstance(result, list)
    assert len(result) == 2


# --------------------------------------
# Update cart item tests
# --------------------------------------

@patch("app.services.cart_service.Cart.query")
@patch("app.services.cart_service.db.session")
def test_update_cart_item_success(mock_session, mock_cart_query, app_context):
    fruit_mock = MagicMock()
    fruit_mock.price = 5.0

    cart_item = MagicMock()
    cart_item.cart_id = 1
    cart_item.fruit_info = fruit_mock
    mock_cart_query.get.return_value = cart_item

    result = cart_service.update_cart_item(cart_id=1, quantity=3)

    assert result == cart_item
    assert cart_item.quantity == 3
    assert cart_item.item_price == 15.0
    mock_session.commit.assert_called_once()


@patch("app.services.cart_service.Cart.query")
def test_update_cart_item_not_found(mock_cart_query, app_context):
    mock_cart_query.get.return_value = None

    with pytest.raises(ValueError, match="Cart item not found"):
        cart_service.update_cart_item(cart_id=9999, quantity=2)


# --------------------------------------
# ✅ delete_cart_item tests
# --------------------------------------

@patch("app.services.cart_service.Cart.query")
@patch("app.services.cart_service.db.session")
def test_delete_cart_item_not_found(mock_session, mock_cart_query):
    mock_cart_query.get.return_value = None
    result = cart_service.delete_cart_item(cart_id=1234)
    assert result is False


@patch("app.services.cart_service.Cart.query")
@patch("app.services.cart_service.db.session")
def test_delete_cart_item_success(mock_session, mock_cart_query):
    mock_cart = MagicMock()
    mock_cart_query.get.return_value = mock_cart
    result = cart_service.delete_cart_item(cart_id=1)
    assert result is True
    mock_session.delete.assert_called_once_with(mock_cart)
    mock_session.commit.assert_called_once()


# --------------------------------------
# ✅ clear_cart_for_user tests
# --------------------------------------

@patch("app.services.cart_service.Cart.query")
@patch("app.services.cart_service.db.session")
def test_clear_cart_for_user_with_items(mock_session, mock_cart_query):
    mock_item1 = MagicMock()
    mock_item2 = MagicMock()
    mock_cart_query.filter_by.return_value.all.return_value = [mock_item1, mock_item2]

    result = cart_service.clear_cart_for_user(user_id=1)
    assert result == 2
    assert mock_session.delete.call_count == 2
    mock_session.commit.assert_called_once()


@patch("app.services.cart_service.Cart.query")
@patch("app.services.cart_service.db.session")
def test_clear_cart_for_user_empty(mock_session, mock_cart_query):
    mock_cart_query.filter_by.return_value.all.return_value = []
    result = cart_service.clear_cart_for_user(user_id=1)
    assert result == 0
    mock_session.commit.assert_called_once()
