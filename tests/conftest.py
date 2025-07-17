import os
import sys

# ✅ Disable AWS secrets during test runs
os.environ["FLASK_ENV"] = "test"
os.environ["USE_AWS_SECRET"] = "false"
os.environ["DB_USER"] = "testuser"
os.environ["DB_PASSWORD"] = "testpass"
os.environ["DB_HOST"] = "localhost"
os.environ["DB_PORT"] = "5432"
os.environ["DB_NAME"] = "testdb"

# ✅ Ensure project root is in path before importing app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from datetime import datetime, timedelta

import pytest

from app import create_app, db
from app.models.cart import Cart
from app.models.fruit import Fruit, FruitInfo
from app.models.users import User


@pytest.fixture
def app():

    app = create_app()
    app.config.update(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",  # In-memory DB for test isolation
            "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        }
    )

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def setup_order_data(app):
    with app.app_context():
        # 👤 User
        user = User(
            name="OrderFixtureUser",
            email="fixtureuser@example.com",
            phone_number="1010101010",
        )
        db.session.add(user)
        db.session.flush()

        # 🍍 Fruit + Info
        fruit = Fruit(name="FixtureFruit", color="Red", size="Medium", has_seeds=True)
        db.session.add(fruit)
        db.session.flush()

        info = FruitInfo(
            fruit_id=fruit.fruit_id,
            weight=1.0,
            price=4.0,
            total_quantity=50,
            available_quantity=50,
            sell_by_date=datetime.utcnow() + timedelta(days=10),
        )
        db.session.add(info)
        db.session.flush()

        # 🛒 Cart
        cart = Cart(
            user_id=user.user_id,
            fruit_id=fruit.fruit_id,
            info_id=info.info_id,
            quantity=3,
            item_price=12.0,
        )
        db.session.add(cart)
        db.session.commit()

        return {
            "user_id": user.user_id,
            "cart_id": cart.cart_id,
            "fruit_id": fruit.fruit_id,
            "info_id": info.info_id,
        }
