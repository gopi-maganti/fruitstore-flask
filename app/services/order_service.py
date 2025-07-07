from datetime import datetime

from app.extensions import db
from app.models.cart import Cart
from app.models.fruit import FruitInfo
from app.models.orders import Order
from app.models.users import User
from app.utils.log_config import get_logger

logger = get_logger("order_service")

def place_order(user_id: int) -> dict:
    """
    Create an order from a user's cart.

    Parameters
    ----------
    user_id : int

    Returns
    -------
    dict
        Summary of the placed order.
    """
    try:
        cart_items = Cart.query.filter_by(user_id=user_id).all()
        if not cart_items:
            logger.warning("No cart items to place order", user_id=user_id)
            raise ValueError("Cart is empty")

        created_orders = []
        total = 0.0

        for item in cart_items:
            fruit_info = item.fruit_info
            if fruit_info.available_quantity < item.quantity:
                logger.warning("Not enough quantity", fruit_id=item.fruit_id)
                raise ValueError("Not enough stock for one or more fruits")

            fruit_info.available_quantity -= item.quantity

            order = Order(
                user_id=user_id,
                fruit_id=item.fruit_id,
                info_id=item.info_id,
                quantity=item.quantity,
                price_by_fruit=fruit_info.price,
                order_date=datetime.utcnow()
            )
            db.session.add(order)
            created_orders.append(order)
            total += order.total_price
            db.session.delete(item)

        db.session.commit()
        logger.info("Order placed", user_id=user_id, item_count=len(created_orders), total=total)
        return {
            "order_total": round(total, 2),
            "order_items": [o.as_dict() for o in created_orders]
        }

    except Exception as e:
        db.session.rollback()
        logger.exception("Failed to place order", user_id=user_id)
        raise


def get_order_history(user_id: int) -> list:
    """
    Retrieve all past orders for a user.

    Parameters
    ----------
    user_id : int

    Returns
    -------
    list
    """
    orders = Order.query.filter_by(user_id=user_id).order_by(Order.order_date.desc()).all()
    logger.info("Fetched order history", user_id=user_id, count=len(orders))
    return [o.as_dict() for o in orders]
