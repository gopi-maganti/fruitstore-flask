from flasgger import swag_from
from flask import Blueprint, jsonify

from app.services import order_service
from app.utils.log_config import get_logger

order_bp = Blueprint("order_bp", __name__)
logger = get_logger("order_routes")

@order_bp.route("/place/<int:user_id>", methods=["POST"])
@swag_from("swagger_docs/order/place_order.yml")
def place_order(user_id):
    try:
        summary = order_service.place_order(user_id)
        return jsonify({"message": "Order placed", **summary}), 201
    except ValueError as ve:
        logger.warning("Order placement failed", user_id=user_id, reason=str(ve))
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        logger.exception("Unexpected error placing order", user_id=user_id)
        return jsonify({"error": str(e)}), 500

@order_bp.route("/history/<int:user_id>", methods=["GET"])
@swag_from("swagger_docs/order/get_order_history.yml")
def get_order_history(user_id):
    try:
        history = order_service.get_order_history(user_id)
        return jsonify(history), 200
    except Exception as e:
        logger.exception("Failed to retrieve order history", user_id=user_id)
        return jsonify({"error": str(e)}), 500
