from app.models.users import User
from app import db
import pytest

def test_user_to_dict(app):
    with app.app_context():
        user = User(name="Alice", email="alice@example.com", phone_number="1234567890")
        db.session.add(user)
        db.session.commit()
        result = user.to_dict()
        assert result["name"] == "Alice"
        assert result["email"] == "alice@example.com"

def test_user_exists(app):
    with app.app_context():
        user = User(name="Bob", email="bob@example.com", phone_number="9876543210")
        db.session.add(user)
        db.session.commit()
        assert user.exists() == True

def test_user_save_duplicate_raises(app):
    with app.app_context():
        user1 = User(name="Tom", email="tom@example.com", phone_number="1111111111")
        db.session.add(user1)
        db.session.commit()

        user2 = User(name="Tom", email="tom@example.com", phone_number="1111111111")
        with pytest.raises(ValueError):
            user2.save()
