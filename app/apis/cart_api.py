from flasgger import swag_from
from flask import Blueprint, jsonify, request
from pydantic import ValidationError

from app import db
from app.models.cart import Cart
from app.models.fruit import FruitInfo
from app.models.users import User
from app.schemas.cart_validation import CartAddValidation, CartUpdateValidation

cart_bp = Blueprint("cart_bp", __name__)


@cart_bp.route("/add", methods=["POST"])
@swag_from(
    {
        "tags": ["Cart"],
        "description": "Add fruit to the cart",
        "parameters": [
            {
                "name": "body",
                "in": "body",
                "required": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "integer"},
                        "fruit_id": {"type": "integer"},
                        "quantity": {"type": "integer"},
                    },
                    "required": ["user_id", "fruit_id", "quantity"],
                },
            }
        ],
        "responses": {
            201: {"description": "Item added to cart successfully"},
            400: {"description": "Bad Request"},
            404: {"description": "FruitInfo or User not found"},
            500: {"description": "Internal Server Error"},
        },
    }
)
def add_to_cart():
    try:
        data = request.get_json()
        validated_data = CartAddValidation(**data)

        # Validate fruit info
        fruit_info = FruitInfo.query.filter_by(fruit_id=validated_data.fruit_id).first()
        if not fruit_info:
            return jsonify({"error": "FruitInfo not found for this fruit"}), 404

        # If user_id is provided and not -1, validate user
        if validated_data.user_id != -1:
            user = User.query.get(validated_data.user_id)
            if not user:
                return jsonify({"error": "User not found"}), 404

        cart_item = Cart(
            user_id=validated_data.user_id or -1,
            fruit_id=validated_data.fruit_id,
            info_id=fruit_info.info_id,
            quantity=validated_data.quantity,
            item_price=validated_data.quantity * fruit_info.price,
        )

        cart_item.save()
        return (
            jsonify(
                {
                    "message": "Item added to cart successfully",
                    "cart": cart_item.as_dict(),
                }
            ),
            201,
        )

    except ValidationError as ve:
        return jsonify({"error": "Validation Error", "details": ve.errors()}), 400

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@cart_bp.route("/associate-cart", methods=["POST"])
@swag_from(
    {
        "tags": ["Cart"],
        "description": "Associate cart items from one user to another",
        "parameters": [
            {
                "name": "body",
                "in": "body",
                "required": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "old_user_id": {"type": "integer"},
                        "new_user_id": {"type": "integer"},
                    },
                    "required": ["old_user_id", "new_user_id"],
                },
            }
        ],
        "responses": {
            200: {"description": "Cart items associated successfully"},
            400: {"description": "Bad Request"},
            404: {"description": "User not found"},
        },
    }
)
def associate_cart():
    data = request.get_json()
    old_user_id = data.get("old_user_id")
    new_user_id = data.get("new_user_id")

    if old_user_id is None or new_user_id is None:
        return jsonify({"error": "Both old_user_id and new_user_id are required"}), 400

    user = User.query.get(new_user_id)
    if not user:
        return jsonify({"error": "Target user not found"}), 404

    updated = Cart.query.filter_by(user_id=old_user_id).update({"user_id": new_user_id})
    db.session.commit()

    return (
        jsonify(
            {"message": f"{updated} cart items associated with user {new_user_id}"}
        ),
        200,
    )


# Get items from cart
@cart_bp.route("/<string:user_id>", methods=["GET"])
@swag_from(
    {
        "tags": ["Cart"],
        "description": "Get all cart items for a user",
        "parameters": [
            {
                "name": "user_id",
                "in": "path",
                "type": "string",
                "required": True,
                "description": "ID of the user to retrieve",
            }
        ],
        "responses": {
            200: {"description": "List of cart items"},
            404: {"description": "No cart items found for the user"},
        },
    }
)
def get_cart_items(user_id):
    try:
        user_id = int(user_id)  # convert to int manually
    except ValueError:
        return jsonify({"error": "Invalid user ID"}), 400

    cart_items = Cart.query.filter_by(user_id=user_id).all()
    if not cart_items:
        return jsonify({"message": "No cart items found for this user"}), 404

    return jsonify([item.as_dict() for item in cart_items]), 200


# Update Cart Items
@cart_bp.route("/update/<int:cart_id>", methods=["PUT"])
@swag_from(
    {
        "tags": ["Cart"],
        "description": "Update quantity of a cart item",
        "parameters": [
            {
                "name": "cart_id",
                "in": "path",
                "type": "integer",
                "required": True,
                "description": "Cart ID to update",
            },
            {
                "name": "body",
                "in": "body",
                "required": True,
                "schema": {
                    "type": "object",
                    "properties": {"quantity": {"type": "integer"}},
                    "required": ["quantity"],
                },
            },
        ],
        "responses": {
            200: {"description": "Cart item updated successfully"},
            404: {"description": "Cart item not found"},
        },
    }
)
def update_cart_item(cart_id):
    try:
        data = request.get_json()
        validated_data = CartUpdateValidation(**data)

        cart_item = Cart.query.get(cart_id)
        if not cart_item:
            return jsonify({"error": "Cart item not found"}), 404

        cart_item.quantity = validated_data.quantity

        if cart_item.fruit_info and cart_item.fruit_info.price:
            cart_item.item_price = cart_item.quantity * cart_item.fruit_info.price

        db.session.commit()
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
        return jsonify({"error": "Validation Error", "details": ve.errors()}), 400


# Delete Cart Items by Cart_ID
@cart_bp.route("/delete/<int:cart_id>", methods=["DELETE"])
@swag_from(
    {
        "tags": ["Cart"],
        "description": "Delete a specific cart item",
        "parameters": [
            {
                "name": "cart_id",
                "in": "path",
                "type": "integer",
                "required": True,
                "description": "ID of the cart to delete",
            }
        ],
        "responses": {
            200: {"description": "Cart item deleted"},
            404: {"description": "Cart item not found"},
        },
    }
)
def delete_cart_item(cart_id):
    cart_item = Cart.query.get(cart_id)

    if not cart_item:
        return jsonify({"error": "Cart item not found"}), 404

    db.session.delete(cart_item)
    db.session.commit()
    return jsonify({"message": "Cart item deleted successfully"}), 200


# Clear all Cart Items
@cart_bp.route("/clear/<int:user_id>", methods=["DELETE"])
@swag_from(
    {
        "tags": ["Cart"],
        "description": "Clear all items from a user's cart",
        "parameters": [
            {
                "name": "user_id",
                "in": "path",
                "type": "integer",
                "required": True,
                "description": "ID of the user to delete",
            }
        ],
        "responses": {
            200: {"description": "All cart items deleted"},
            404: {"description": "No cart items found"},
        },
    }
)
def clear_cart(user_id):
    cart_items = Cart.query.filter_by(user_id=user_id).all()

    if not cart_items:
        return jsonify({"message": "No cart items to delete"}), 404

    for item in cart_items:
        db.session.delete(item)

    db.session.commit()
    return jsonify({"message": "All cart items cleared for user"}), 200
