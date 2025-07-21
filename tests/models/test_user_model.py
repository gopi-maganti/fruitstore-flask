import uuid
import pytest
from unittest.mock import patch
from app.models.users import User
from app import db
import random


def generate_test_user():
    uid = uuid.uuid4().hex
    unique_suffix = uid[:8]
    random_phone = f"{random.randint(1000000000, 9999999999)}"
    return {
        "name": f"Test-{unique_suffix}",
        "email": f"user-{uid}@example.com",
        "phone_number": random_phone
    }


def test_user_to_dict(app):
    with app.app_context():
        user_data = generate_test_user()
        user = User(**user_data)
        expected = {
            "user_id": None,
            "name": user.name,
            "email": user.email,
            "phone_number": user.phone_number,
        }
        assert user.to_dict() == expected


@patch("app.models.users.User.exists", return_value=False)
def test_user_exists(mock_exists, app):
    with app.app_context():
        user_data = generate_test_user()
        user = User(**user_data)
        user.save()
        mock_exists.assert_called()


def test_user_save_duplicate_raises(app):
    with app.app_context():
        
        email = "duptest@example.com"
        phone = "9876543210"

        user1 = User(name="User One", email=email, phone_number=phone)
        user1.save()

        # Same email/phone for user2 to trigger duplication
        user2 = User(name="User Two", email=email, phone_number=phone)

        with pytest.raises(ValueError, match="User with these details already exists."):
            user2.save()



def test_user_repr():
    user = User(name="John", email="john@example.com", phone_number="9876543210")
    expected = "<User John, Email: john@example.com, Phone: 9876543210>"
    assert repr(user) == expected


@patch("app.models.users.db.session")
@patch("app.models.users.User.exists", return_value=False)
def test_user_save(mock_exists, mock_session):
    user = User(name="Jane", email="jane@example.com", phone_number="1234567890")
    user.save()
    mock_session.add.assert_called_once_with(user)
    mock_session.commit.assert_called_once()
