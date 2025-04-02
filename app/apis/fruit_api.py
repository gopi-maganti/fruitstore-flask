from flask import Blueprint, request, jsonify
from flasgger import swag_from
from datetime import datetime

from app.models.fruit import Fruit, FruitInfo
from app import db

fruit_bp = Blueprint('fruit_bp', __name__)

# Add a new fruit with additional information
@fruit_bp.route('/add', methods=['POST'])
@swag_from({
    'tags': ['Fruit'],
    'description': 'Add a new fruit with additional information',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'name': {'type': 'string'},
                    'description': {'type': 'string'},
                    'color': {'type': 'string'},
                    'size': {'type': 'string'},
                    'image_url': {'type': 'string'},
                    'has_seeds': {'type': 'boolean'},
                    'weight': {'type': 'number'},
                    'price': {'type': 'number'},
                    'total_quantity': {'type': 'integer'},
                    'sell_by_date': {'type': 'string', 'format': 'date-time'}
                },
                'required': ['name', 'color', 'size', 'image_url',
                             'weight', 'price', 'total_quantity',
                             'sell_by_date']
            }
        }
    ],
    'responses': {
        201: {
            'description': 'Fruit and FruitInfo added successfully',
        },
        400: {
            'description': "Missing or invalid fields",
            "examples": {
                "application/json": {
                    "error": "Missing fields: name, color, size, image_url, weight, price, total_quantity, sell_by_date"
                }
            }
        },
        500: {
            "description": "Internal Server Error"
        }
    }
})
def add_fruit_with_info():
    data = request.get_json()

    # Split fruit and info fields
    fruit_fields = ['name', 'description', 'color', 'size', 'image_url', 'has_seeds']
    info_fields = ['weight', 'price', 'total_quantity', 'sell_by_date']

    missing_fruit = [f for f in fruit_fields if f not in data or (data[f] is (None or "") and f != 'description')]
    missing_info = [f for f in info_fields if f not in data or data[f] is None]

    if missing_fruit or missing_info:
        return jsonify({
            'error': f'Missing fields: {", ".join(missing_fruit + missing_info)}'
        }), 400

    try:
        fruit = Fruit(
            name=data['name'],
            color=data['color'],
            description=data.get('description'),
            has_seeds=data.get('has_seeds', False),
            size=data['size'],
            image_url=data['image_url']
        )

        if fruit.exists():
            raise ValueError("Fruit with these details already exists. If you want to update, use the update button.")

        db.session.add(fruit)
        db.session.flush()

        fruit_info = FruitInfo(
            fruit_id=fruit.fruit_id,
            weight=data['weight'],
            price=data['price'],
            total_quantity=data['total_quantity'],
            available_quantity=data.get('available_quantity', data['total_quantity']),
            created_at=datetime.utcnow(),
            sell_by_date=datetime.strptime(data['sell_by_date'], '%Y-%m-%dT%H:%M:%S')
        )

        if fruit_info.exists():
            raise ValueError("Fruit info with these details already exists. If you want to update, use the update button.")

        db.session.add(fruit_info)
        db.session.commit()

        return jsonify({
            'message': 'Fruit and FruitInfo added successfully',
            'fruit': fruit.to_dict(),
            'fruit_info_id': fruit_info.info_id
        }), 201

    except ValueError as ve:
        db.session.rollback()
        return jsonify({'error': str(ve)}), 400

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Internal Server Error', 'details': str(e)}), 500


# Get all fruits and their information
@fruit_bp.route('/', methods=['GET'])
@swag_from({
    'tags': ['Fruit'],
    'description': 'Get all fruits and their information',
    'responses': {
        200: {
            'description': 'List of fruits and their information',
            'schema': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'fruit_id': {'type': 'integer'},
                        'name': {'type': 'string'},
                        'description': {'type': 'string'},
                        'color': {'type': 'string'},
                        'size': {'type': 'string'},
                        'image_url': {'type': 'string'},
                        'has_seeds': {'type': 'boolean'},
                        'info_id': {'type': 'integer'},
                        'weight': {'type': 'number'},
                        'price': {'type': 'number'},
                        'total_quantity': {'type': 'integer'},
                        'sell_by_date': {'type': 'string', 'format': 'date-time'}
                    }
                }
            }
        },
        500: {
            "description": "Internal Server Error"
        }
    }
})
def get_all_fruits():
    fruits = Fruit.query.all()
    fruit_info = FruitInfo.query.all()

    result = []
    for fruit in fruits:
        info = next((fi for fi in fruit_info if fi.fruit_id == fruit.fruit_id), None)
        if info:
            result.append({
                'fruit_id': fruit.fruit_id,
                'name': fruit.name,
                'description': fruit.description,
                'color': fruit.color,
                'size': fruit.size,
                'image_url': fruit.image_url,
                'has_seeds': fruit.has_seeds,
                'info_id':info.info_id,
                'weight': info.weight,
                'price': info.price,
                'total_quantity': info.total_quantity,
                'available_quantity': info.available_quantity,
                'sell_by_date': info.sell_by_date.isoformat()
            })

    return jsonify(result), 200

#Get fruit by ID
@fruit_bp.route('/<int:fruit_id>', methods=['GET'])
@swag_from({
    'tags': ['Fruit'],
    'description': 'Get fruit by ID',
    'parameters': [
        {
            'name': 'fruit_id',
            'in': 'path',
            'required': True,
            'type': 'integer'
        }
    ],
    'responses': {
        200: {
            'description': 'Fruit found',
            'schema': {
                'type': 'object',
                'properties': {
                    'fruit_id': {'type': 'integer'},
                    'name': {'type': 'string'},
                    'description': {'type': 'string'},
                    'color': {'type': 'string'},
                    'size': {'type': 'string'},
                    'image_url': {'type': 'string'},
                    'has_seeds': {'type': 'boolean'},
                    'info_id': {'type': 'integer'},
                    'weight': {'type': 'number'},
                    'price': {'type': 'number'},
                    'total_quantity': {'type': 'integer'},
                    'sell_by_date': {'type': 'string', 'format': 'date-time'}
                }
            }
        },
        404: {
            "description": "Fruit not found"
        },
        500: {
            "description": "Internal Server Error"
        }
    }
})
def get_fruit_by_id(fruit_id):
    fruit = Fruit.query.get(fruit_id)
    if not fruit:
        return jsonify({'error': 'Fruit not found'}), 404

    fruit_info = FruitInfo.query.filter_by(fruit_id=fruit.fruit_id).first()
    if not fruit_info:
        return jsonify({'error': 'Fruit info not found'}), 404

    result = {
        'fruit_id': fruit.fruit_id,
        'name': fruit.name,
        'description': fruit.description,
        'color': fruit.color,
        'size': fruit.size,
        'image_url': fruit.image_url,
        'has_seeds': fruit.has_seeds,
        'info_id': fruit_info.info_id,
        'weight': fruit_info.weight,
        'price': fruit_info.price,
        'total_quantity': fruit_info.total_quantity,
        'sell_by_date': fruit_info.sell_by_date.isoformat()
    }

    return jsonify(result), 200

# Update only the necessary fields of fruit information
@fruit_bp.route('/<int:fruit_id>', methods=['PUT'])
@swag_from({
    'tags': ['Fruit'],
    'description': 'Update fruit information',
    'parameters': [
        {
            'name': 'fruit_id',
            'in': 'path',
            'required': True,
            'type': 'integer'
        },
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'weight': {'type': 'number'},
                    'price': {'type': 'number'},
                    'total_quantity': {'type': 'integer'},
                    'sell_by_date': {'type': 'string', 'format': 'date-time'}
                }
            }
        }
    ],
    'responses': {
        200: {
            'description': 'Fruit information updated successfully',
        },
        404: {
            "description": "Fruit not found"
        },
        500: {
            "description": "Internal Server Error"
        }
    }
})
def update_fruit_info(fruit_id):
    data = request.get_json()
    fruit = Fruit.query.get(fruit_id)
    if not fruit:
        return jsonify({'error': 'Fruit not found'}), 404

    fruit_info = FruitInfo.query.filter_by(fruit_id=fruit.fruit_id).first()
    if not fruit_info:
        return jsonify({'error': 'Fruit info not found'}), 404

    if 'total_quantity' in data:
        fruit_info.total_quantity = data['total_quantity']
        # Optionally update available_quantity too (only if explicitly provided)
        if 'available_quantity' in data:
            fruit_info.available_quantity = data['available_quantity']

    # Then continue updating other fields if any (weight, price, sell_by_date)
    for key, value in data.items():
        if key != 'available_quantity' and hasattr(fruit_info, key):
            setattr(fruit_info, key, value)

    db.session.commit()

    return jsonify({
        'message': 'Fruit information updated successfully',
        'fruit_info': {
            'fruit_id': fruit.fruit_id,
            'weight': fruit_info.weight,
            'price': fruit_info.price,
            'total_quantity': fruit_info.total_quantity,
            'available_quantity': fruit_info.available_quantity,
            'sell_by_date': fruit_info.sell_by_date.isoformat()
        }
    }), 200

# Delete fruit by ID
@fruit_bp.route('/<int:fruit_id>', methods=['DELETE'])
@swag_from({
    'tags': ['Fruit'],
    'description': 'Delete fruit by ID',
    'parameters': [
        {
            'name': 'fruit_id',
            'in': 'path',
            'required': True,
            'type': 'integer'
        }
    ],
    'responses': {
        200: {
            'description': 'Fruit deleted successfully',
        },
        404: {
            "description": "Fruit not found"
        },
        500: {
            "description": "Internal Server Error"
        }
    }
})
def delete_fruit(fruit_id):
    fruit = Fruit.query.get(fruit_id)
    if not fruit:
        return jsonify({'error': 'Fruit not found'}), 404

    db.session.delete(fruit)
    db.session.commit()

    return jsonify({'message': 'Fruit deleted successfully'}), 200