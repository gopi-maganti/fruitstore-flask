from flasgger import swag_from
from flask import Blueprint, jsonify, request
from pydantic import ValidationError

from app.services import user_service
from app.utils.log_config import get_logger
from app.validations.user_validation import UserValidation

user_bp = Blueprint("user_bp", __name__)
logger = get_logger("user")

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
        validated = UserValidation(**data)
        user = user_service.create_user(validated.name, validated.email, validated.phone_number)
        logger.info("User created", user_id=user.user_id)
        return jsonify({"message": "User created", "user": user.to_dict()}), 201
    except ValidationError as ve:
        logger.warning("Validation failed", errors=ve.errors())
        return jsonify({"error": "Validation error", "details": ve.errors()}), 400
    except Exception as e:
        logger.exception("Unhandled error creating user")
        return jsonify({"error": str(e)}), 500


@user_bp.route("/", methods=["GET"])
@swag_from(
    {
        "tags": ["User"],
        "description": "Get all users",
        "responses": {200: {"description": "List of users"}},
    }
)
def get_all_users():
    """
    Get all registered users.
    """
    try:
        users = user_service.get_all_users()
        logger.info("Fetched all users", count=len(users))
        return jsonify([u.to_dict() for u in users]), 200
    except Exception as e:
        logger.exception("Error fetching users")
        return jsonify({"error": str(e)}), 500


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
def get_user_by_id(user_id):
    """
    Get user by ID.
    """
    try:
        user = user_service.get_user_by_id(user_id)
        if user:
            logger.info("User found", user_id=user_id)
            return jsonify(user.to_dict()), 200
        else:
            logger.warning("User not found", user_id=user_id)
            return jsonify({"error": "User not found"}), 404
    except Exception as e:
        logger.exception("Error retrieving user")
        return jsonify({"error": str(e)}), 500


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
    """
    Delete user by ID.
    """
    try:
        deleted = user_service.delete_user_by_id(user_id)
        if deleted:
            logger.info("User deleted", user_id=user_id)
            return jsonify({"message": "User deleted"}), 200
        else:
            logger.warning("User not found for deletion", user_id=user_id)
            return jsonify({"error": "User not found"}), 404
    except Exception as e:
        logger.exception("Error deleting user")
        return jsonify({"error": str(e)}), 500
