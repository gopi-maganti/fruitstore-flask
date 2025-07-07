from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db
from app.models.users import User
from app.utils.log_config import get_logger

logger = get_logger("user_service")


def create_user(name: str, email: str, phone_number: str) -> User:
    """
    Create and save a new user.

    Parameters
    ----------
    name : str
        Full name of the user.
    email : str
        Unique email address.
    phone_number : str
        10-digit phone number.

    Returns
    -------
    User
        The created user object.
    """
    try:
        user = User(name=name, email=email, phone_number=phone_number)
        db.session.add(user)
        db.session.commit()
        logger.info("User created and committed", user_id=user.user_id)
        return user
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.exception("Failed to create user", name=name, email=email)
        raise


def get_all_users() -> list:
    """
    Retrieve all users from the database.

    Returns
    -------
    list
        List of User objects.
    """
    users = User.query.all()
    logger.info("Retrieved all users", count=len(users))
    return users


def get_user_by_id(user_id: int) -> User | None:
    """
    Retrieve a user by ID.

    Parameters
    ----------
    user_id : int
        ID of the user.

    Returns
    -------
    User or None
    """
    user = User.query.get(user_id)
    if user:
        logger.info("User found", user_id=user_id)
    else:
        logger.warning("User not found", user_id=user_id)
    return user


def delete_user_by_id(user_id: int) -> bool:
    """
    Delete a user by ID.

    Parameters
    ----------
    user_id : int

    Returns
    -------
    bool
        True if deleted, False otherwise.
    """
    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        logger.info("User deleted", user_id=user_id)
        return True
    logger.warning("Delete failed - user not found", user_id=user_id)
    return False
