from flasgger import swag_from
from flask import Blueprint, jsonify, request
from pydantic import ValidationError

from app import db
from app.models.cart import Cart
from app.models.orders import Order, ParentOrder
from app.models.users import User
from app.schemas.order_validation import OrderValidation

order_bp = Blueprint("order", __name__)

"""
PLACE NEW ORDER
"""


@order_bp.route("/add/<string:user_id>", methods=["POST"])
@swag_from(
    {
        "tags": ["Order"],
        "description": "Place one grouped order with multiple cart items and return the combined total.",
        "parameters": [
            {"name": "user_id", "in": "path", "type": "string", "required": True},
            {
                "name": "body",
                "in": "body",
                "required": False,
                "schema": {
                    "type": "object",
                    "properties": {
                        "cart_ids": {"type": "array", "items": {"type": "integer"}},
                        "guest_info": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "email": {"type": "string"},
                                "phone_number": {"type": "string"},
                            },
                        },
                    },
                },
            },
        ],
        "responses": {
            201: {"description": "Grouped order created with combined total"},
            400: {"description": "Cart is empty or invalid input"},
            404: {"description": "User not found"},
            500: {"description": "Internal server error"},
        },
    }
)
def add_order(user_id):
    try:
        data = request.get_json(silent=True)
        validated_data = OrderValidation(**data) if data else OrderValidation()

        if user_id == -1:
            if not validated_data.guest_info:
                return (
                    jsonify({"error": "Guest info is required for guest checkout"}),
                    400,
                )

            guest_info = validated_data.guest_info

            guest_user = User(
                name=guest_info.name,
                email=guest_info.email,
                phone_number=guest_info.phone_number,
            )
            try:
                guest_user.save()
            except ValueError:
                guest_user = User.query.filter_by(
                    email=guest_info.email, phone_number=guest_info.phone_number
                ).first()

                if not guest_user:
                    return (
                        jsonify({"error": "Could not create or find guest user"}),
                        500,
                    )

            user_id = guest_user.user_id

        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        cart_ids = validated_data.cart_ids
        if cart_ids:
            cart_items = Cart.query.filter(
                Cart.user_id == user_id, Cart.cart_id.in_(cart_ids)
            ).all()
        else:
            cart_items = Cart.query.filter_by(user_id=user_id).all()

        if not cart_items:
            return jsonify({"error": "No items found in cart to checkout"}), 400

        created_order_items = []
        total_price_accumulator = 0.0

        parent_order = ParentOrder(user_id=user_id)
        db.session.add(parent_order)
        db.session.flush()

        for item in cart_items:
            fruit_info = item.fruit_info

            if fruit_info.available_quantity < item.quantity:
                raise ValueError(f"Not enough quantity for fruit: {item.fruit_name}")

            fruit_info.available_quantity -= item.quantity

            order = Order(
                user_id=user_id,
                parent_order_id=parent_order.id,
                fruit_id=item.fruit_id,
                info_id=item.info_id,
                is_seeded=getattr(item, "is_seeded", False),
                quantity=item.quantity,
                price_by_fruit=fruit_info.price,
            )

            db.session.add(order)
            created_order_items.append(order)
            total_price_accumulator += order.total_price

            db.session.delete(item)

        db.session.commit()

        return (
            jsonify(
                {
                    "message": "Order placed successfully",
                    "order_id": parent_order.id,
                    "order_date": parent_order.order_date.isoformat(),
                    "total_order_price": round(total_price_accumulator, 2),
                    "items": [
                        {
                            "fruit_name": item.fruit_name,
                            "quantity": item.quantity,
                            "price_by_fruit": item.price_by_fruit,
                            "total_price": item.total_price,
                        }
                        for item in created_order_items
                    ],
                }
            ),
            201,
        )

    except ValidationError as ve:
        return jsonify({"error": "Validation Error", "details": ve.errors()}), 400

    except ValueError as ve:
        db.session.rollback()
        return jsonify({"error": str(ve)}), 400

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to place order", "details": str(e)}), 500


"""
GET ALL ORDERS
"""


@order_bp.route("/getall", methods=["GET"])
@swag_from(
    {
        "tags": ["Order"],
        "description": "Get all orders with user names",
        "responses": {200: {"description": "List of all orders with user info"}},
    }
)
def get_all_orders():
    orders = Order.query.all()
    return (
        jsonify(
            [
                {
                    "order_id": order.order_id,
                    "user_id": order.user_id,
                    "user_name": order.user.name if order.user else "Unknown",
                    "fruit": order.fruit_name,
                    "size": order.fruit_size,
                    "quantity": order.quantity,
                    "price": order.price_by_fruit,
                    "total": order.total_price,
                    "date": order.order_date.isoformat(),
                }
                for order in orders
            ]
        ),
        200,
    )


"""
GET ORDERS BY USER ID
"""


@order_bp.route("/history/<int:user_id>", methods=["GET"])
@swag_from(
    {
        "tags": ["Order"],
        "description": "Get all orders placed by a user, grouped by parent order.",
        "parameters": [
            {"name": "user_id", "in": "path", "type": "integer", "required": True}
        ],
        "responses": {
            200: {"description": "List of all parent orders with items"},
            404: {"description": "User not found or no orders"},
        },
    }
)
def get_order_history_by_user(user_id):
    from app.models.orders import ParentOrder

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    parent_orders = (
        ParentOrder.query.filter_by(user_id=user_id)
        .order_by(ParentOrder.order_date.desc())
        .all()
    )
    if not parent_orders:
        return jsonify({"message": "No order history found"}), 404

    return (
        jsonify(
            [
                {
                    "order_id": parent_order.id,
                    "order_date": parent_order.order_date.isoformat(),
                    "total_price": round(
                        sum(item.total_price for item in parent_order.items), 2
                    ),
                    "items": [
                        {
                            "fruit_name": item.fruit_name,
                            "quantity": item.quantity,
                            "price_by_fruit": item.price_by_fruit,
                            "total_price": item.total_price,
                        }
                        for item in parent_order.items
                    ],
                }
                for parent_order in parent_orders
            ]
        ),
        200,
    )


@order_bp.route("/grouped", methods=["GET"])
@swag_from(
    {
        "tags": ["Order"],
        "description": "Get all orders grouped by parent order with user names",
        "responses": {
            200: {"description": "List of all grouped orders with user info"}
        },
    }
)
def get_grouped_orders():
    parent_orders = ParentOrder.query.order_by(ParentOrder.order_date.desc()).all()

    grouped = []
    for parent in parent_orders:
        grouped.append(
            {
                "parent_order_id": parent.id,
                "order_date": parent.order_date.isoformat(),
                "user_name": parent.user.name if parent.user else "Unknown",
                "orders": [
                    {
                        "fruit_name": item.fruit_name,
                        "size": item.fruit_size,
                        "quantity": item.quantity,
                        "price": item.price_by_fruit,
                        "total": item.total_price,
                    }
                    for item in parent.items
                ],
            }
        )
    return jsonify(grouped), 200
