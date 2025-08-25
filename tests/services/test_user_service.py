from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.exc import SQLAlchemyError

from app.services import user_service

# ----------------------------------------
# ✅ Positive Test Cases
# ----------------------------------------


@patch("app.services.user_service.db.session.commit")
@patch("app.services.user_service.db.session.add")
def test_create_user_success(mock_add, mock_commit):
    mock_user = MagicMock()
    mock_user.user_id = 1
    with patch("app.services.user_service.User", return_value=mock_user):
        result = user_service.create_user("Alice", "alice@example.com", "1234567890")
        assert result.user_id == 1


@patch("app.services.user_service.User.query")
def test_get_all_users(mock_query, app):
    with app.app_context():
        mock_user1 = MagicMock(user_id=1)
        mock_user2 = MagicMock(user_id=2)
        mock_query.all.return_value = [mock_user1, mock_user2]

        result = user_service.get_all_users()
        assert isinstance(result, list)
        assert len(result) == 2  # Fix


@patch("app.services.user_service.User.query")
def test_get_user_by_id_found(mock_query, app):
    with app.app_context():
        mock_user = MagicMock()
        mock_user.user_id = 1
        mock_query.get.return_value = mock_user

        result = user_service.get_user_by_id(1)
        assert result.user_id == 1


@patch("app.services.user_service.User.query.get")
def test_get_user_by_id_not_found(mock_get, app):
    with app.app_context():
        mock_get.return_value = None
        result = user_service.get_user_by_id(999)
        assert result is None


@patch("app.services.user_service.db.session.commit")
@patch("app.services.user_service.db.session.delete")
@patch("app.services.user_service.User.query")
def test_delete_user_by_id_success(mock_query, mock_delete, mock_commit, app):
    with app.app_context():
        mock_user = MagicMock()
        mock_user.user_id = 1
        mock_query.get.return_value = mock_user

        result = user_service.delete_user_by_id(1)
        assert result is True


@patch("app.services.user_service.User.query.get")
def test_delete_user_by_id_not_found(mock_get, app):
    with app.app_context():
        mock_get.return_value = None
        result = user_service.delete_user_by_id(999)
        assert result is False


# ----------------------------------------
# ❌ Negative Test Cases
# ----------------------------------------


@patch("app.services.user_service.db.session.rollback")
@patch("app.services.user_service.db.session.add")
def test_create_user_db_failure(mock_add, mock_rollback):
    mock_add.side_effect = SQLAlchemyError("Insert failed")
    with patch("app.services.user_service.User", return_value=MagicMock()):
        with pytest.raises(SQLAlchemyError, match="Insert failed"):
            user_service.create_user("Bob", "bob@example.com", "0987654321")
        mock_rollback.assert_called_once()
