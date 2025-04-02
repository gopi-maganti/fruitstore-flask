from flask import Blueprint, request, jsonify
from flasgger import swag_from

from app import db
from app.models.fruit import FruitInfo
from app.models.orders import Order
from app.models.users import User

order_bp = Blueprint('order', __name__)

@order_bp.route('/add', methods=['POST'])
@swag_from({
    'tags': ['Order'],
    'description': 'Add a new order',
    'parameters': [
        {
            'name': 'order_data',
            'in': 'body',
            'required': True,
            'schema': {
                '$ref': '#/definitions/Order'
            }
        }
    ],
    'responses': {
        200: {
            'description': 'Order created successfully',
            'examples': {
                'application/json': {
                    'order_id': 1,
                    'user_id': 1,
                    'fruit_id': 1,
                    'info_id': 1,
                    'is_seeded': False,
                    'quantity': 10,
                    'order_date': '2023-10-01T12:00:00',
                    'price_by_fruit': 5.0,
                    'total_price': 50.0
                }
            }
        },
        400: {
            'description': 'Bad Request',
            'examples': {
                'application/json': {
                    'error': 'Invalid input data'
                }
            }
        },
        404: {
            'description': 'User or Fruit not found',
            'examples': {
                'application/json': {
                    'error': 'User or Fruit not found'
                }
            }
        }
    }
})
def add_order():
    data = request.get_json()
    user_id = data.get('user_id')
    fruit_id = data.get('fruit_id')
    info_id = data.get('info_id')
    is_seeded = data.get('is_seeded', False)
    quantity = data.get('quantity')
    price_by_fruit = data.get('price_by_fruit')

    # Validate input
    if not user_id or not fruit_id or not info_id or not quantity or not price_by_fruit:
        return jsonify({'error': 'Invalid input data'}), 400

    # Check if user exists
    user = User.query.filter_by(user_id=user_id).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    fruit_info = FruitInfo.query.get(info_id)
    if not fruit_info:
        return jsonify({'error': 'FruitInfo not found'}), 404

    if fruit_info.available_quantity < quantity:
        return jsonify({'error': 'Not enough available quantity'}), 400

    fruit_info.available_quantity -= quantity

    order = Order(
        user_id=user_id,
        fruit_id=fruit_id,
        info_id=info_id,
        is_seeded=is_seeded,
        quantity=quantity,
        price_by_fruit=price_by_fruit
    )
    order.save()
    db.session.commit()

    return jsonify(order.as_dict()), 200

@order_bp.route('/getall', methods=['GET'])
@swag_from({
    'tags': ['Order'],
    'description': 'Get all orders',
    'responses': {
        200: {
            'description': 'List of all orders',
            'examples': {
                'application/json': [
                    {
                        'order_id': 1,
                        'user_id': 1,
                        'fruit_id': 1,
                        'info_id': 1,
                        'is_seeded': False,
                        'quantity': 10,
                        'order_date': '2023-10-01T12:00:00',
                        'price_by_fruit': 5.0,
                        'total_price': 50.0
                    }
                ]
            }
        }
    }
})
def get_all_orders():
    orders = Order.query.all()
    return jsonify([order.as_dict() for order in orders]), 200

#get order by user id
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
            'description': 'List of orders for the specified user',
            'examples': {
                'application/json': [
                    {
                        'order_id': 1,
                        'user_id': 1,
                        'fruit_id': 1,
                        'info_id': 1,
                        'is_seeded': False,
                        'quantity': 10,
                        'order_date': '2023-10-01T12:00:00',
                        'price_by_fruit': 5.0,
                        'total_price': 50.0
                    }
                ]
            }
        },
        404: {
            'description': 'User not found',
            'examples': {
                'application/json': {
                    'error': 'User not found'
                }
            }
        }
    }
})
def get_orders_by_user_id(user_id):
    # Check if user exists
    user = User.query.filter_by(user_id=user_id).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Get orders for the user
    orders = Order.query.filter_by(user_id=user_id).all()
    return jsonify([order.as_dict() for order in orders]), 200

