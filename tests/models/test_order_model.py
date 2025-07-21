from datetime import datetime, timedelta

from app import db
from app.models.fruit import Fruit, FruitInfo
from app.models.orders import Order, ParentOrder
from app.models.users import User
from aws_utils import s3_utils


def test_order_total_price(app):
    with app.app_context():
        user = User(
            name="OrderUser", email="order@example.com", phone_number="0009998888"
        )
        fruit = Fruit(name="Mango", color="Yellow", size="L", has_seeds=True)
        db.session.add_all([user, fruit])
        db.session.flush()

        info = FruitInfo(
            fruit_id=fruit.fruit_id,
            weight=1.2,
            price=3.0,
            total_quantity=30,
            available_quantity=28,
            sell_by_date=datetime.utcnow() + timedelta(days=5),
        )
        db.session.add(info)
        db.session.flush()

        parent = ParentOrder(user_id=user.user_id)
        db.session.add(parent)
        db.session.flush()

        order = Order(
            parent_order_id=parent.id,
            user_id=user.user_id,
            fruit_id=fruit.fruit_id,
            info_id=info.info_id,
            is_seeded=True,
            quantity=4,
            price_by_fruit=3.0,
        )
        db.session.add(order)
        db.session.commit()

        assert order.total_price == 12.0
        assert order.fruit_name == "Mango"
        assert order.fruit_size == "L"
