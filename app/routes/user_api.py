from flasgger import swag_from
from flask import Blueprint, jsonify, request
from pydantic import ValidationError

from app.services import user_service
from app.utils.log_config import get_logger
from app.validations.user_validation import UserValidation

user_bp = Blueprint("user_bp", __name__)
logger = get_logger("user")

@user_bp.route("/add", methods=["POST"])
@swag_from("swagger_docs/user/add_user.yml")
def add_user():
    try:
        data = request.get_json()
        validated = UserValidation(**data)
        user = user_service.create_user(validated.name, validated.email, validated.phone_number)
        logger.info("User created", user_id=user.user_id)
        return jsonify({"message": "User created", "user": user.to_dict()}), 201
    except ValidationError as ve:
        logger.warning("Validation failed", errors=ve.errors())

        # Clean ctx for serialization
        cleaned_errors = []
        for err in ve.errors():
            if "ctx" in err and "error" in err["ctx"]:
                err["ctx"]["error"] = str(err["ctx"]["error"])
            cleaned_errors.append(err)

        return jsonify({"error": "Validation error", "details": cleaned_errors}), 400
    except Exception as e:
        logger.exception("Unhandled error creating user")
        return jsonify({"error": str(e)}), 500


@user_bp.route("/all", methods=["GET"])
@swag_from("swagger_docs/user/get_all_users.yml")
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
@swag_from("swagger_docs/user/get_user_by_id.yml")
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


@user_bp.route("/delete/<int:user_id>", methods=["DELETE"])
@swag_from("swagger_docs/user/delete_user.yml")
def delete_user(user_id):
    """
    Delete user by ID.
    """
    try:
        deleted = user_service.delete_user_by_id(user_id)
        if deleted:
            logger.info("User deleted successfully!!", user_id=user_id)
            return jsonify({"message": "User deleted successfully!!"}), 200
        else:
            logger.warning("User not found for deletion", user_id=user_id)
            return jsonify({"error": "User not found"}), 404
    except Exception as e:
        logger.exception("Error deleting user")
        return jsonify({"error": str(e)}), 500
