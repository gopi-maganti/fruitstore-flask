from flasgger import swag_from
from flask import Blueprint, jsonify, request
from pydantic import ValidationError

from app import db
from app.models.users import User
from app.schemas.user_validation import UserValidation

user_bp = Blueprint("user_bp", __name__)


@user_bp.route("/add", methods=["POST"])
@swag_from(
    {
        "tags": ["User"],
        "description": "Add a new user",
        "parameters": [
            {
                "name": "body",
                "in": "body",
                "required": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "email": {"type": "string"},
                        "phone_number": {"type": "string"},
                    },
                    "required": ["name", "email", "phone_number"],
                },
            }
        ],
        "responses": {
            201: {"description": "User added successfully"},
            400: {"description": "Bad request or user already exists"},
            500: {"description": "Internal server error"},
        },
    }
)
def add_user():
    try:
        data = request.get_json()
        validated_data = UserValidation(**data)

        user = User(
            name=validated_data.name,
            email=validated_data.email,
            phone_number=validated_data.phone_number,
        )
        user.save()
        return (
            jsonify(
                {"message": f"User added successfully with USER ID: {user.user_id}"}
            ),
            201,
        )

    except ValidationError as ve:
        return jsonify({"error": "Validation Error", "details": str(ve)}), 400

    except ValueError as e:
        return jsonify({"error": "Validation Error", "details": str(e)}), 400

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Internal Server Error", "details": str(e)}), 500


@user_bp.route("/", methods=["GET"])
@swag_from(
    {
        "tags": ["User"],
        "description": "Get all users",
        "responses": {200: {"description": "List of users"}},
    }
)
def get_users():
    users = User.query.all()
    return jsonify([u.to_dict() for u in users]), 200


@user_bp.route("/<int:user_id>", methods=["GET"])
@swag_from(
    {
        "tags": ["User"],
        "description": "Get user by ID",
        "parameters": [
            {
                "name": "user_id",
                "in": "path",
                "type": "integer",
                "required": True,
                "description": "ID of the user to retrieve",
            }
        ],
        "responses": {
            200: {"description": "User found"},
            404: {"description": "User not found"},
        },
    }
)
def get_user(user_id):
    user = User.query.get(user_id)
    if user:
        return jsonify(user.to_dict()), 200
    return jsonify({"error": "User not found"}), 404


@user_bp.route("/<int:user_id>", methods=["DELETE"])
@swag_from(
    {
        "tags": ["User"],
        "description": "Delete user by ID",
        "responses": {
            200: {"description": "User deleted successfully"},
            404: {"description": "User not found"},
        },
    }
)
def delete_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": "User deleted successfully"}), 200
