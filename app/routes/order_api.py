from flasgger import swag_from
from flask import Blueprint, jsonify, request
from pydantic import ValidationError

from app.services import order_service
from app.utils.log_config import get_logger
from app.validations.order_validation import OrderValidation

order_bp = Blueprint("order_bp", __name__)
logger = get_logger("order_routes")

# -----------------------------------------------
# Place Order
# -----------------------------------------------


@order_bp.route("/place/<int:user_id>", methods=["POST"])
@swag_from("swagger_docs/order/place_order.yml")
def place_order(user_id: int):
    try:
        validated = OrderValidation(**request.get_json())
        summary = order_service.place_order(user_id, validated.cart_ids)
        return jsonify({"message": "Order placed", **summary}), 201
    except ValidationError as ve:
        logger.warning("Validation error placing order", extra={"errors": ve.errors()})
        return jsonify({"error": ve.errors()}), 400
    except ValueError as ve:
        logger.warning("Order placement failed", user_id=user_id, reason=str(ve))
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        logger.exception("Unexpected error placing order", user_id=user_id)
        return jsonify({"error": str(e)}), 500


# -----------------------------------------------
# Get Order by User ID
# -----------------------------------------------


@order_bp.route("/history/<int:user_id>", methods=["GET"])
@swag_from("swagger_docs/order/get_order_history.yml")
def get_order_history(user_id):
    try:
        history = order_service.get_order_history(user_id)
        if not history:
            return jsonify({"error": "No orders found for this user"}), 404
        return jsonify(history), 200
    except Exception as e:
        logger.exception("Failed to retrieve order history", user_id=user_id)
        return jsonify({"error": str(e)}), 500


# -----------------------------------------------
# Get All Orders
# -----------------------------------------------


@order_bp.route("/all", methods=["GET"])
@swag_from("swagger_docs/order/get_all_orders.yml")
def get_all_orders():
    try:
        orders = order_service.get_all_orders()
        if not orders:
            return jsonify({"error": "No orders found"}), 404
        return jsonify(orders), 200
    except Exception as e:
        logger.exception("Failed to retrieve all orders")
        return jsonify({"error": str(e)}), 500
