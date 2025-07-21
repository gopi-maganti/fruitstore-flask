from app.extensions import db
from app.models.cart import Cart
from app.models.fruit import FruitInfo
from app.models.users import User
from app.utils.log_config import get_logger

logger = get_logger("cart_service")


def add_to_cart(user_id: int, fruit_id: int, quantity: int) -> Cart:
    """
    Add a fruit item to the user's cart.

    Parameters
    ----------
    user_id : int
        The ID of the user adding the item.
    fruit_id : int
        The ID of the fruit being added.
    quantity : int
        Quantity of the fruit.

    Returns
    -------
    Cart
        The created cart item.
    """
    fruit_info = FruitInfo.query.filter_by(fruit_id=fruit_id).first()
    if not fruit_info:
        logger.warning("Fruit not found for cart add", fruit_id=fruit_id)
        raise ValueError("Fruit not found")

    if user_id != -1:
        user = User.query.get(user_id)
        if not user:
            logger.warning("User not found for cart add", user_id=user_id)
            raise ValueError("User not found")

    item_price = fruit_info.price * quantity
    cart = Cart(
        user_id=user_id,
        fruit_id=fruit_id,
        info_id=fruit_info.info_id,
        quantity=quantity,
        item_price=item_price,
    )

    try:
        db.session.add(cart)
        db.session.commit()
        logger.info("Cart item successfully added", cart_id=cart.cart_id, user_id=user_id, fruit_id=fruit_id, quantity=quantity)
        return cart
    except Exception as e:
        db.session.rollback()
        logger.exception("Failed to add cart item", user_id=user_id, fruit_id=fruit_id, quantity=quantity)
        raise


def get_cart_items_by_user(user_id: int) -> list:
    """
    Retrieve all cart items for a user.

    Parameters
    ----------
    user_id : int

    Returns
    -------
    list
        List of Cart items.
    """
    items = Cart.query.filter_by(user_id=user_id).all()
    logger.info("Fetched cart items for user", user_id=user_id, count=len(items))
    return items


def update_cart_item(cart_id: int, quantity: int) -> Cart:
    """
    Update the quantity of a specific cart item.

    Parameters
    ----------
    cart_id : int
        The ID of the cart item to update.
    quantity : int
        The new quantity for the cart item.

    Returns
    -------
    Cart
        The updated cart item.
    """
    cart_item = Cart.query.get(cart_id)
    if not cart_item:
        logger.warning("Cart item not found for update", cart_id=cart_id)
        raise ValueError("Cart item not found")

    cart_item.quantity = quantity
    if cart_item.fruit_info and cart_item.fruit_info.price:
        cart_item.item_price = quantity * cart_item.fruit_info.price

    db.session.commit()
    logger.info("Cart item updated", cart_id=cart_item.cart_id, quantity=quantity)
    return cart_item


def delete_cart_item(cart_id: int) -> bool:
    """
    Delete a specific cart item by ID.

    Parameters
    ----------
    cart_id : int

    Returns
    -------
    bool
        True if the item was deleted, False if not found.
    """
    cart = Cart.query.get(cart_id)
    if cart:
        db.session.delete(cart)
        db.session.commit()
        logger.info("Cart item deleted", cart_id=cart_id)
        return True

    logger.warning("Cart item not found for deletion", cart_id=cart_id)
    return False


def clear_cart_for_user(user_id: int) -> int:
    """
    Remove all cart items for a given user.

    Parameters
    ----------
    user_id : int

    Returns
    -------
    int
        Number of items deleted.
    """
    items = Cart.query.filter_by(user_id=user_id).all()
    count = len(items)

    for item in items:
        db.session.delete(item)

    db.session.commit()
    logger.info("Cleared cart for user", user_id=user_id, count=count)
    return count
