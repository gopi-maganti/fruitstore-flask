from flasgger import swag_from
from flask import Blueprint, jsonify, request
from pydantic import ValidationError

from app.extensions import db
from app.models.cart import Cart
from app.models.users import User
from app.services import cart_service
from app.utils.log_config import get_logger
from app.validations.cart_validation import CartAddValidation, CartUpdateValidation

cart_bp = Blueprint("cart_bp", __name__)
logger = get_logger("cart_routes")

# -----------------------------------------------
# Add Cart Item
# -----------------------------------------------


@cart_bp.route("/add", methods=["POST"])
@swag_from("swagger_docs/cart/add_cart_item.yml")
def add_cart_item():
    try:
        data = request.get_json()
        logger.info("Cart add request received", data=data)

        validated = CartAddValidation(**data)
        item = cart_service.add_to_cart(
            validated.user_id, validated.fruit_id, validated.quantity
        )

        return jsonify(item.as_dict()), 201
    except ValidationError as ve:
        logger.warning("Validation error in cart add", errors=ve.errors())
        return jsonify({"error": ve.errors()}), 400  # ✅ Correct status code

    except ValueError as ve:
        logger.warning("Business logic error in cart add", exception=str(ve))
        return jsonify({"error": str(ve)}), 404

    except Exception as e:
        logger.error("Unhandled exception in cart add", exception=str(e))
        return jsonify({"error": "Internal Server Error"}), 500


# -----------------------------------------------
# Associate Cart with User
# -----------------------------------------------


@cart_bp.route("/associate-cart", methods=["POST"])
@swag_from("swagger_docs/cart/associate_cart.yml")
def associate_cart():
    data = request.get_json()
    old_user_id = data.get("old_user_id")
    new_user_id = data.get("new_user_id")
    logger.info("Associating cart", old_user_id=old_user_id, new_user_id=new_user_id)

    if old_user_id is None or new_user_id is None:
        logger.warning("Missing user IDs in associate-cart request")
        return jsonify({"error": "Both old_user_id and new_user_id are required"}), 400

    user = User.query.get(new_user_id)
    if not user:
        logger.warning("Target user not found", user_id=new_user_id)
        return jsonify({"error": "Target user not found"}), 404

    updated = Cart.query.filter_by(user_id=old_user_id).update({"user_id": new_user_id})
    db.session.commit()
    logger.info("Cart reassignment complete", updated=updated)
    return (
        jsonify(
            {"message": f"{updated} cart items associated with user {new_user_id}"}
        ),
        200,
    )


# -----------------------------------------------
# Get Cart Items by User ID
# -----------------------------------------------


@cart_bp.route("/<string:user_id>", methods=["GET"])
@swag_from("swagger_docs/cart/get_user_cart.yml")
def get_cart_items(user_id):
    try:
        user_id = int(user_id)
    except ValueError:
        logger.warning("Invalid user ID format", user_id=user_id)
        return jsonify({"error": "Invalid user ID"}), 400

    cart_items = Cart.query.filter_by(user_id=user_id).all()
    if not cart_items:
        logger.info("No cart items found", user_id=user_id)
        return jsonify({"message": "No cart items found for this user"}), 404

    logger.info("Cart items fetched", count=len(cart_items), user_id=user_id)
    return jsonify([item.as_dict() for item in cart_items]), 200


# -----------------------------------------------
# Update Cart Item
# -----------------------------------------------


@cart_bp.route("/update/<int:cart_id>", methods=["PUT"])
@swag_from("swagger_docs/cart/update_cart_item.yml")
def update_cart_item(cart_id):
    try:
        data = request.get_json()
        logger.info("Updating cart item", cart_id=cart_id, data=data)
        validated_data = CartUpdateValidation(**data)

        cart_item = Cart.query.get(cart_id)
        if not cart_item:
            logger.warning("Cart item not found", cart_id=cart_id)
            return jsonify({"error": "Cart item not found"}), 404

        cart_item.quantity = validated_data.quantity
        if cart_item.fruit_info and cart_item.fruit_info.price:
            cart_item.item_price = cart_item.quantity * cart_item.fruit_info.price

        db.session.commit()
        logger.info("Cart item updated", cart_id=cart_item.cart_id)
        return (
            jsonify(
                {
                    "message": "Cart item updated successfully",
                    "cart": cart_item.as_dict(),
                }
            ),
            200,
        )

    except ValidationError as ve:
        logger.error("Validation error on update", cart_id=cart_id, errors=ve.errors())
        return jsonify({"error": "Validation Error", "details": ve.errors()}), 400
    except Exception as e:
        logger.exception("Error updating cart item")
        return jsonify({"error": str(e)}), 500


# -----------------------------------------------
# Delete Cart Item
# -----------------------------------------------


@cart_bp.route("/delete/<int:cart_id>", methods=["DELETE"])
@swag_from("swagger_docs/cart/delete_cart_item.yml")
def delete_cart_item(cart_id):
    try:
        cart_item = Cart.query.get(cart_id)
        if not cart_item:
            logger.warning("Cart item not found for deletion", cart_id=cart_id)
            return jsonify({"error": "Cart item not found"}), 404

        db.session.delete(cart_item)
        db.session.commit()
        logger.info("Cart item deleted", cart_id=cart_id)
        return jsonify({"message": "Cart item deleted successfully"}), 200
    except Exception:
        logger.exception("Failed to delete cart item")
        return jsonify({"error": "Internal Server Error"}), 500


# -----------------------------------------------
# Clear User Cart
# -----------------------------------------------


@cart_bp.route("/clear/<int:user_id>", methods=["DELETE"])
@swag_from("swagger_docs/cart/clear_user_cart.yml")
def clear_cart(user_id):
    try:
        cart_items = Cart.query.filter_by(user_id=user_id).all()

        if not cart_items:
            logger.info("No cart items to clear", user_id=user_id)
            return jsonify({"message": "No cart items to delete"}), 404

        for item in cart_items:
            db.session.delete(item)

        db.session.commit()
        logger.info("All cart items cleared", user_id=user_id)
        return jsonify({"message": "All cart items cleared for user"}), 200
    except Exception:
        logger.exception("Failed to clear cart")
        return jsonify({"error": "Internal Server Error"}), 500
