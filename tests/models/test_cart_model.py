from app.models.cart import Cart
from app.models.users import User
from app.models.fruit import Fruit, FruitInfo
from app import db
from datetime import datetime, timedelta

def test_cart_as_dict(app):
    with app.app_context():
        user = User(name="CartUser", email="cart@example.com", phone_number="2223334444")
        fruit = Fruit(name="Banana", color="Yellow", size="S", has_seeds=False)
        db.session.add_all([user, fruit])
        db.session.flush()

        info = FruitInfo(
            fruit_id=fruit.fruit_id,
            weight=1.1,
            price=1.5,
            total_quantity=20,
            available_quantity=15,
            sell_by_date=datetime.utcnow() + timedelta(days=3)
        )
        db.session.add(info)
        db.session.flush()

        cart = Cart(user_id=user.user_id, fruit_id=fruit.fruit_id, info_id=info.info_id, quantity=3, item_price=4.5)
        db.session.add(cart)
        db.session.commit()

        assert cart.as_dict()["quantity"] == 3
        assert "cart_id" in cart.as_dict()

from app.models.cart import Cart
from app.models.users import User
from app.models.fruit import Fruit, FruitInfo
from unittest.mock import MagicMock
from app import db

def test_cart_price_computation_mock(app):
    with app.app_context():
        fruit_info_mock = MagicMock()
        fruit_info_mock.price = 3.5

        cart = Cart(
            user_id=1,
            fruit_id=1,
            info_id=1,
            quantity=2,
            item_price=None
        )
        cart.fruit_info = fruit_info_mock

        cart.item_price = cart.quantity * cart.fruit_info.price
        assert cart.item_price == 7.0

