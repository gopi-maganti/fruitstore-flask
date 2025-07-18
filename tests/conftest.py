import os
import sys
from datetime import datetime, timedelta
import io
import pytest
import aws_utils.s3_utils as s3_utils

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
@pytest.fixture(autouse=True)
def cleanup_db():
    yield
    db.session.rollback()
    for model in [Cart, FruitInfo, Fruit, User]:
        db.session.query(model).delete()
    db.session.commit()

# ✅ Add a user dynamically
@pytest.fixture
def add_user():
    def _add_user(client, name="CartUser", email="cart@example.com", phone="1234567890"):
        resp = client.post("/user/add", json={
            "name": name, "email": email, "phone_number": phone
        })
        user = User.query.filter_by(email=email).first()
        return resp, user.user_id
    return _add_user

# ✅ Add a fruit dynamically with image
@pytest.fixture
def add_fruit():
    def _add_fruit(client):
        image = (io.BytesIO(b"fake"), "fruit.jpg")
        fruit_data = {
            "name": "Test Fruit",
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
            "/fruit/add", data={**data, "image": image}, content_type="multipart/form-data"
        )
    return _add_fruit

# ✅ Setup order data in DB (user, fruit, cart)
@pytest.fixture
def setup_order_data(app):
    with app.app_context():
        user = User(
            name="OrderFixtureUser",
            email="fixtureuser@example.com",
            phone_number="1010101010",
        )
        db.session.add(user)
        db.session.flush()

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
    def fake_upload_to_s3(file, bucket, key):
        return "https://example.com/mock-image.jpg"
    
    monkeypatch.setattr(s3_utils, "upload_to_s3", fake_upload_to_s3)