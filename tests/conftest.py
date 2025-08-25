import io
import os
import random
import sys
import uuid
from datetime import datetime, timedelta

import pytest

from aws_utils import s3_utils
from aws_utils.s3_utils import upload_to_s3

# ✅ Override env for local test run
os.environ["FLASK_ENV"] = "test"
os.environ["USE_AWS_SECRET"] = "false"
os.environ["DB_USER"] = "testuser"
os.environ["DB_PASSWORD"] = "testpass"
os.environ["DB_HOST"] = "localhost"
os.environ["DB_PORT"] = "5432"
os.environ["DB_NAME"] = "testdb"

# ✅ Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app, db
from app.models.cart import Cart
from app.models.fruit import Fruit, FruitInfo
from app.models.users import User


# ✅ Core app fixture using in-memory DB
@pytest.fixture(scope="module")
def app():
    app = create_app()
    app.config.update(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        }
    )
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope="module")
def client(app):
    return app.test_client()


# ✅ Global DB cleanup between tests
import pytest
from flask import has_app_context

from app import db


@pytest.fixture(autouse=True)
def cleanup_db():
    yield
    if has_app_context():
        db.session.rollback()


# ✅ Add a user dynamically
@pytest.fixture
def add_user():
    def _add_user(client, name=None, email=None, phone=None):
        if name is None:
            name = f"Test User {uuid.uuid4()}"
        if email is None:
            email = f"{name.lower()}_{random.randint(1000,9999)}@example.com"
        if phone is None:
            phone = f"{random.randint(1000000000,9999999999)}"

        response = client.post(
            "/user/add", json={"name": name, "email": email, "phone_number": phone}
        )

        user = User.query.filter_by(email=email).first()
        return response, user.user_id

    return _add_user


# ✅ Add a fruit dynamically with image
@pytest.fixture
def add_fruit():
    def _add_fruit(client, name=None):
        unique_name = name or f"Test Fruit {uuid.uuid4()}"
        image = (io.BytesIO(b"fake"), "fruit.jpg")
        fruit_data = {
            "name": unique_name,
            "description": "desc",
            "color": "Red",
            "size": "M",
            "has_seeds": "true",
            "weight": "1.0",
            "price": "10.0",
            "total_quantity": "50",
            "available_quantity": "50",
            "sell_by_date": "2030-01-01",
            "image": image,
        }
        data = {k: v for k, v in fruit_data.items() if k != "image"}
        return client.post(
            "/fruit/add",
            data={**data, "image": image},
            content_type="multipart/form-data",
        )

    return _add_fruit


# ✅ Setup order data in DB (user, fruit, cart)
import uuid
from datetime import datetime, timedelta

import pytest

from app import db
from app.models.cart import Cart
from app.models.fruit import Fruit, FruitInfo
from app.models.users import User


@pytest.fixture
def setup_order_data(app):
    with app.app_context():
        # Generate unique suffix
        uid = uuid.uuid4().hex[:6]

        # Create unique user
        user = User(
            name=f"OrderFixtureUser-{uid}",
            email=f"fixtureuser-{uid}@example.com",
            phone_number=f"10101{uid[:5]}",
        )
        db.session.add(user)
        db.session.flush()

        # Create unique fruit
        fruit = Fruit(
            name=f"FixtureFruit-{uid}",
            description="A juicy test fruit",
            color="Red",
            size="Medium",
            has_seeds=True,
            image_url="https://example.com/fruit.jpg",
        )
        db.session.add(fruit)
        db.session.flush()

        # Create fruit info
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

        # Create cart item
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


@pytest.fixture(autouse=True)
def mock_s3_upload(monkeypatch):
    def fake_upload_to_s3(file, bucket, key, **kwargs):
        return "https://example.com/mock-image.jpg"

    monkeypatch.setattr(s3_utils, "upload_to_s3", fake_upload_to_s3)
