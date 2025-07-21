from app.models.cart import Cart
from app.models.fruit import Fruit
from unittest.mock import patch, MagicMock
from datetime import datetime
from app import db, create_app


def test_cart_to_dict():
    cart = Cart(user_id=1, fruit_id=2, quantity=3, item_price=30.0)
    cart.cart_id = 1
    cart.added_date = datetime(2025, 7, 18)
    cart.fruit = Fruit(name="Apple", image_url="https://example.com/apple.jpg")
    result = cart.as_dict()

    assert result["cart_id"] == 1
    assert result["user_id"] == 1
    assert result["fruit_id"] == 2
    assert result["quantity"] == 3
    assert result["item_price"] == 30.0
    assert result["fruit_name"] == "Apple"
    assert result["image_url"] == "https://example.com/apple.jpg"
    assert result["added_date"] == "2025-07-18T00:00:00"


def test_cart_repr():
    cart = Cart(user_id=2, fruit_id=5, quantity=1, item_price=10.0)
    cart.cart_id = 42
    assert repr(cart) == "<Cart 42, User: 2, Fruit: 5, Quantity: 1>"


@patch("app.models.cart.db.session")
@patch("app.models.cart.Cart.exists", return_value=False)
def test_cart_save(mock_exists, mock_session):
    cart = Cart(user_id=1, fruit_id=1, quantity=2, item_price=20.0)
    cart.save()
    mock_session.add.assert_called_once_with(cart)
    mock_session.commit.assert_called_once()


@patch("app.models.cart.Cart.query")
def test_cart_exists(mock_query, app):
    with app.app_context():
        mock_query.filter_by.return_value.first.return_value = MagicMock()
        assert Cart.exists(user_id=1, fruit_id=1)
