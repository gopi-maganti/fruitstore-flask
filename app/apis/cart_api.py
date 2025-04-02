from flask import Blueprint, request, jsonify
from flasgger import swag_from

from app import db
from app.models.cart import Cart
from app.models.fruit import FruitInfo
from app.models.users import User

cart_bp = Blueprint('cart_bp', __name__)

@cart_bp.route('/add', methods=['POST'])
@swag_from({
    'tags': ['Cart'],
    'description': 'Add fruit to the cart',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'user_id': {'type': 'integer'},
                    'fruit_id': {'type': 'integer'},
                    'info_id': {'type': 'integer'},
                    'quantity': {'type': 'integer'}
                },
                'required': ['user_id', 'fruit_id', 'info_id', 'quantity']
            }
        }
    ],
    'responses': {
        201: {
            'description': 'Item added to cart successfully'
        },
        400: {
            'description': 'Bad Request'
        },
        404: {
            'description': 'FruitInfo or User not found'
        },
        500: {
            'description': 'Internal Server Error'
        }
    }
})
def add_to_cart():
    data = request.get_json()

    try:

        # Validate user
        user = User.query.get(data['user_id'])
        if not user:
            return jsonify({'error': 'User not found'}), 404

        # Validate fruit info
        fruit_info = FruitInfo.query.get(data['info_id'])
        if not fruit_info:
            return jsonify({'error': 'FruitInfo not found'}), 404

        # Assume price per fruit from FruitInfo
        price = fruit_info.price

        cart_item = Cart(
            user_id=data['user_id'],
            fruit_id=data['fruit_id'],
            info_id=data['info_id'],
            quantity=data['quantity'],
        )

        cart_item.save()

        return jsonify({'message': 'Item added to cart successfully', 'cart': cart_item.as_dict()}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

#Get items from cart
@cart_bp.route('/<int:user_id>', methods=['GET'])
@swag_from({
    'tags': ['Cart'],
    'description': 'Get all cart items for a user',
    'responses': {
        200: {'description': 'List of cart items'},
        404: {'description': 'No cart items found for the user'}
    }
})
def get_cart_items(user_id):
    cart_items = Cart.query.filter_by(user_id=user_id).all()
    if not cart_items:
        return jsonify({'message': 'No cart items found for this user'}), 404

    return jsonify([item.as_dict() for item in cart_items]), 200

@cart_bp.route('/update/<int:cart_id>', methods=['PUT'])
@swag_from({
    'tags': ['Cart'],
    'description': 'Update quantity of a cart item',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'quantity': {'type': 'integer'}
                },
                'required': ['quantity']
            }
        }
    ],
    'responses': {
        200: {'description': 'Cart item updated successfully'},
        404: {'description': 'Cart item not found'}
    }
})
def update_cart_item(cart_id):
    data = request.get_json()
    cart_item = Cart.query.get(cart_id)

    if not cart_item:
        return jsonify({'error': 'Cart item not found'}), 404

    cart_item.quantity = data['quantity']
    db.session.commit()
    return jsonify({'message': 'Cart item updated successfully', 'cart': cart_item.as_dict()}), 200

@cart_bp.route('/delete/<int:cart_id>', methods=['DELETE'])
@swag_from({
    'tags': ['Cart'],
    'description': 'Delete a specific cart item',
    'responses': {
        200: {'description': 'Cart item deleted'},
        404: {'description': 'Cart item not found'}
    }
})
def delete_cart_item(cart_id):
    cart_item = Cart.query.get(cart_id)

    if not cart_item:
        return jsonify({'error': 'Cart item not found'}), 404

    db.session.delete(cart_item)
    db.session.commit()
    return jsonify({'message': 'Cart item deleted successfully'}), 200

@cart_bp.route('/clear/<int:user_id>', methods=['DELETE'])
@swag_from({
    'tags': ['Cart'],
    'description': 'Clear all items from a user\'s cart',
    'responses': {
        200: {'description': 'All cart items deleted'},
        404: {'description': 'No cart items found'}
    }
})
def clear_cart(user_id):
    cart_items = Cart.query.filter_by(user_id=user_id).all()

    if not cart_items:
        return jsonify({'message': 'No cart items to delete'}), 404

    for item in cart_items:
        db.session.delete(item)

    db.session.commit()
    return jsonify({'message': 'All cart items cleared for user'}), 200
