from flask import Blueprint, jsonify
from flasgger import swag_from

from app import db
from app.models.orders import Order
from app.models.users import User
from app.models.cart import Cart

order_bp = Blueprint('order', __name__)

@order_bp.route('/add/<int:user_id>', methods=['POST'])
@swag_from({
    'tags': ['Order'],
    'description': 'Create orders from cart items for a user and clear the cart',
    'parameters': [
        {
            'name': 'user_id',
            'in': 'path',
            'type': 'integer',
            'required': True,
            'description': 'User ID whose cart will be converted to orders'
        }
    ],
    'responses': {
        201: {
            'description': 'Orders created successfully from cart items'
        },
        400: {
            'description': 'Cart is empty or input invalid'
        },
        404: {
            'description': 'User not found'
        }
    }
})
def add_order(user_id):
    # Check if user exists
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    cart_items = Cart.query.filter_by(user_id=user_id).all()
    if not cart_items:
        return jsonify({'error': 'Cart is empty'}), 400

    created_orders = []

    try:
        for item in cart_items:
            price = item.fruit_info.price  # Fetch from FruitInfo
            order = Order(
                user_id=item.user_id,
                fruit_id=item.fruit_id,
                info_id=item.info_id,
                is_seeded=getattr(item, 'is_seeded', False),
                quantity=item.quantity,
                price_by_fruit=price
            )
            order.save()
            created_orders.append(order.as_dict())
            db.session.delete(item)  # Remove from cart after order is placed

        db.session.commit()

        return jsonify({
            'message': 'Order(s) placed successfully',
            'orders': created_orders
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to place orders', 'details': str(e)}), 500


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


@order_bp.route('/get/<int:user_id>', methods=['GET'])
@swag_from({
    'tags': ['Order'],
    'description': 'Get orders by user ID',
    'parameters': [
        {
            'name': 'user_id',
            'in': 'path',
            'required': True,
            'type': 'integer'
        }
    ],
    'responses': {
        200: {
            'description': 'List of orders for the specified user'
        },
        404: {
            'description': 'User not found'
        }
    }
})
def get_orders_by_user_id(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    orders = Order.query.filter_by(user_id=user_id).all()
    return jsonify([order.as_dict() for order in orders]), 200
