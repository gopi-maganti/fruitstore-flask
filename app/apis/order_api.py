from flask import Blueprint, jsonify, request
from flasgger import swag_from
from pydantic import ValidationError

from app import db
from app.models.orders import Order, ParentOrder
from app.models.users import User
from app.models.cart import Cart
from app.schemas.order_validation import OrderValidation

order_bp = Blueprint('order', __name__)

'''
PLACE NEW ORDER
'''
@order_bp.route('/add/<int:user_id>', methods=['POST'])
@swag_from({
    'tags': ['Order'],
    'description': 'Place one grouped order with multiple cart items and return the combined total.',
    'parameters': [
        {
            'name': 'user_id',
            'in': 'path',
            'type': 'integer',
            'required': True
        },
        {
            'name': 'body',
            'in': 'body',
            'required': False,
            'schema': {
                'type': 'object',
                'properties': {
                    'cart_ids': {
                        'type': 'array',
                        'items': {'type': 'integer'},
                        'description': 'Optional list of cart item IDs to checkout.'
                    }
                }
            }
        }
    ],
    'responses': {
        201: {'description': 'Grouped order created with combined total'},
        400: {'description': 'Cart is empty or invalid input'},
        404: {'description': 'User not found'},
        500: {'description': 'Internal server error'}
    }
})
def add_order(user_id):
    try:
        data = request.get_json(silent=True)
        validated_data = OrderValidation(**data) if data else OrderValidation()

        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        cart_ids = validated_data.cart_ids
        if cart_ids:
            cart_items = Cart.query.filter(Cart.user_id == user_id, Cart.cart_id.in_(cart_ids)).all()
        else:
            cart_items = Cart.query.filter_by(user_id=user_id).all()

        if not cart_items:
            return jsonify({'error': 'No items found in cart to checkout'}), 400

        created_order_items = []
        total_price_accumulator = 0.0

        # Create parent order
        parent_order = ParentOrder(user_id=user_id)
        db.session.add(parent_order)
        db.session.flush()

        for item in cart_items:
            fruit_info = item.fruit_info

            if fruit_info.available_quantity < item.quantity:
                raise ValueError(f"Not enough quantity for fruit ID {item.fruit_id}")

            fruit_info.available_quantity -= item.quantity

            order = Order(
                user_id=item.user_id,
                parent_order_id=parent_order.id,
                fruit_id=item.fruit_id,
                info_id=item.info_id,
                is_seeded=getattr(item, 'is_seeded', False),
                quantity=item.quantity,
                price_by_fruit=fruit_info.price
            )

            db.session.add(order)
            created_order_items.append(order)
            total_price_accumulator += order.total_price

            db.session.delete(item)

        db.session.commit()

        return jsonify({
            'message': 'Order placed successfully',
            'order_id': parent_order.id,
            'order_date': parent_order.order_date.isoformat(),
            'total_order_price': round(total_price_accumulator, 2),
            'items': [
                {
                    'fruit_name': item.fruit_name,
                    'quantity': item.quantity,
                    'price_by_fruit': item.price_by_fruit,
                    'total_price': item.total_price
                } for item in created_order_items
            ]
        }), 201

    except ValidationError as ve:
        return jsonify({'error': 'Validation Error', 'details': ve.errors()}), 400

    except ValueError as ve:
        db.session.rollback()
        return jsonify({'error': str(ve)}), 400

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to place order', 'details': str(e)}), 500

'''
GET ALL ORDERS
'''
@order_bp.route('/getall', methods=['GET'])
@swag_from({
    'tags': ['Order'],
    'description': 'Get all orders',
    'responses': {
        200: {
            'description': 'List of all orders'
        }
    }
})
def get_all_orders():
    orders = Order.query.all()
    return jsonify([order.as_dict() for order in orders]), 200

'''
GET ORDERS BY USER ID
'''
@order_bp.route('/history/<int:user_id>', methods=['GET'])
@swag_from({
    'tags': ['Order'],
    'description': 'Get all orders placed by a user, grouped by parent order.',
    'parameters': [
        {
            'name': 'user_id',
            'in': 'path',
            'type': 'integer',
            'required': True
        }
    ],
    'responses': {
        200: {'description': 'List of all parent orders with items'},
        404: {'description': 'User not found or no orders'}
    }
})
def get_order_history_by_user(user_id):
    from app.models.orders import ParentOrder

    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    parent_orders = ParentOrder.query.filter_by(user_id=user_id).order_by(ParentOrder.order_date.desc()).all()
    if not parent_orders:
        return jsonify({'message': 'No order history found'}), 404

    return jsonify([
        {
            'order_id': parent_order.id,
            'order_date': parent_order.order_date.isoformat(),
            'total_price': round(sum(item.total_price for item in parent_order.items), 2),
            'items': [
                {
                    'fruit_name': item.fruit_name,
                    'quantity': item.quantity,
                    'price_by_fruit': item.price_by_fruit,
                    'total_price': item.total_price
                } for item in parent_order.items
            ]
        } for parent_order in parent_orders
    ]), 200
