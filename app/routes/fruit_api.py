import os
import uuid
from datetime import datetime

from flasgger import swag_from
from flask import Blueprint, jsonify, request
from werkzeug.utils import secure_filename

import aws_utils.s3_utils as s3_utils
from app.services import fruit_service
from app.utils.log_config import get_logger

fruit_bp = Blueprint("fruit_bp", __name__)
logger = get_logger("fruit_routes")

# -----------------------------------------------
# Add Fruit and FruitInfo
# -----------------------------------------------


@fruit_bp.route("/add", methods=["POST"])
@swag_from("swagger_docs/fruit/add_fruit.yml")
def add_fruit_with_info():
    try:
        file = request.files.get("image")
        if not file:
            logger.warning("Image file missing")
            return jsonify({"error": "No image file received"}), 400

        # Reset stream pointer just in case
        file.stream.seek(0)

        filename = secure_filename(file.filename)
        image_url = s3_utils.upload_to_s3(
            file=file,
            bucket=os.getenv("S3_BUCKET_NAME"),
            region=os.getenv("AWS_REGION"),
            key=f"fruit-images/{uuid.uuid4().hex}_{filename}",
        )

        form_data = request.form.to_dict()
        form_data["has_seeds"] = (
            request.form.get("has_seeds", "false").lower() == "true"
        )

        try:
            form_data["weight"] = float(form_data["weight"])
            form_data["price"] = float(form_data["price"])
            form_data["total_quantity"] = int(form_data["total_quantity"])
            form_data["available_quantity"] = int(
                request.form.get("available_quantity") or form_data["total_quantity"]
            )
            form_data["sell_by_date"] = datetime.strptime(
                form_data["sell_by_date"], "%Y-%m-%d"
            ).date()
        except Exception as e:
            logger.warning("Invalid numeric or date field", extra={"error": str(e)})
            return jsonify({"error": "Invalid field", "details": str(e)}), 400

        if form_data["sell_by_date"] <= datetime.utcnow().date():
            return jsonify({"error": "sell_by_date must be a future date"}), 400

        fruit, fruit_info = fruit_service.add_fruit_with_info(form_data, image_url)

        return (
            jsonify(
                {
                    "message": "Fruit and FruitInfo added successfully",
                    "fruit": fruit.to_dict(),
                    "fruit_info_id": fruit_info.info_id,
                }
            ),
            201,
        )

    except ValueError as ve:
        logger.warning("Business validation failed", extra={"reason": str(ve)})
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        logger.exception("Upload failed")
        return jsonify({"error": "Upload failed", "details": str(e)}), 500


# -----------------------------------------------
# Get All Fruits
# -----------------------------------------------


@fruit_bp.route("/all", methods=["GET"])
@swag_from("swagger_docs/fruit/get_all_fruits.yml")
def get_all_fruits():
    try:
        data = fruit_service.get_all_fruits()
        return jsonify(data), 200
    except Exception as e:
        logger.exception("Failed to fetch fruits")
        return jsonify({"error": str(e)}), 500


# -----------------------------------------------
# Get Fruit by ID
# -----------------------------------------------


@fruit_bp.route("/<int:fruit_id>", methods=["GET"])
@swag_from("swagger_docs/fruit/get_fruit_by_id.yml")
def get_fruit_by_id(fruit_id):
    try:
        result = fruit_service.get_fruit_by_id(fruit_id)
        if not result:
            return jsonify({"error": "Fruit not found"}), 404
        return jsonify(result), 200
    except Exception as e:
        logger.exception("Failed to get fruit by ID")
        return jsonify({"error": str(e)}), 500


# -----------------------------------------------
# Search Fruits
# -----------------------------------------------


@fruit_bp.route("/search", methods=["GET"])
@swag_from("swagger_docs/fruit/search_fruits.yml")
def search_fruits():
    try:
        filters = dict(request.args)
        results = fruit_service.search_fruits(filters)
        return jsonify(results), 200
    except ValueError as ve:
        logger.warning("Search validation failed", error=str(ve))
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        logger.exception("Fruit search failed")
        return jsonify({"error": str(e)}), 500


# -----------------------------------------------
# Update Fruit Info
# -----------------------------------------------


@fruit_bp.route("/update/<int:fruit_id>", methods=["PUT"])
@swag_from("swagger_docs/fruit/update_fruit_info.yml")
def update_fruit_info(fruit_id):
    try:
        data = request.get_json()
        updated_info = fruit_service.update_fruit_info(fruit_id, data)
        if not updated_info:
            return jsonify({"error": "Fruit not found"}), 404

        return (
            jsonify(
                {
                    "message": "Fruit information updated successfully",
                    "fruit_info": {
                        "fruit_id": fruit_id,
                        "weight": updated_info.weight,
                        "price": updated_info.price,
                        "total_quantity": updated_info.total_quantity,
                        "available_quantity": updated_info.available_quantity,
                        "sell_by_date": updated_info.sell_by_date.isoformat(),
                    },
                }
            ),
            200,
        )

    except Exception as e:
        logger.exception("Failed to update fruit info")
        return jsonify({"error": str(e)}), 500


# -----------------------------------------------
# Delete Fruits
# -----------------------------------------------


@fruit_bp.route("/delete", methods=["DELETE"])
@fruit_bp.route("/delete/<int:fruit_id>", methods=["DELETE"])
@swag_from("swagger_docs/fruit/delete_fruits.yml")
def delete_fruits(fruit_id=None):
    try:
        if fruit_id is not None:
            ids = [fruit_id]
        else:
            data = request.get_json(silent=True) or {}
            ids = data.get("ids", [])

        if not ids:
            return jsonify({"error": "No fruit ID(s) provided"}), 400

        deleted = fruit_service.delete_fruits(ids)
        if deleted == 0:
            return jsonify({"error": "No fruits found to delete"}), 404

        return (
            jsonify(
                {
                    "message": f"Deleted {deleted} fruit{'s' if deleted > 1 else ''} successfully"
                }
            ),
            200,
        )

    except Exception as e:
        logger.exception("Failed to delete fruits")
        return jsonify({"error": "Deletion failed", "details": str(e)}), 500
