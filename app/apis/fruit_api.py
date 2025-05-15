import os
from datetime import datetime

from flasgger import swag_from
from flask import Blueprint, current_app, jsonify, request
from werkzeug.utils import secure_filename

from app import db
from app.models.fruit import Fruit, FruitInfo
from app.schemas.fruit_validation import FruitValidation

fruit_bp = Blueprint("fruit_bp", __name__)


# Add a new fruit with additional information
@fruit_bp.route("/add", methods=["POST"])
@swag_from(
    {
        "tags": ["Fruit"],
        "consumes": ["multipart/form-data"],
        "parameters": [
            {"name": "name", "in": "formData", "type": "string", "required": True},
            {"name": "description", "in": "formData", "type": "string"},
            {"name": "color", "in": "formData", "type": "string", "required": True},
            {"name": "size", "in": "formData", "type": "string", "required": True},
            {"name": "has_seeds", "in": "formData", "type": "boolean"},
            {"name": "weight", "in": "formData", "type": "number", "required": True},
            {"name": "price", "in": "formData", "type": "number", "required": True},
            {
                "name": "total_quantity",
                "in": "formData",
                "type": "integer",
                "required": True,
            },
            {"name": "available_quantity", "in": "formData", "type": "integer"},
            {
                "name": "sell_by_date",
                "in": "formData",
                "type": "string",
                "format": "date",
                "required": True,
            },
            {"name": "image", "in": "formData", "type": "file", "required": True},
        ],
        "responses": {
            201: {"description": "Fruit and image added"},
            400: {"description": "Validation or file error"},
            500: {"description": "Server Error"},
        },
    }
)
def add_fruit_with_info():
    try:
        # Validate and save image
        file = request.files.get("image")
        if not file:
            return jsonify({"error": "No image file received"}), 400

        filename = secure_filename(file.filename)
        upload_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
        file.save(upload_path)
        image_url = f"/static/uploads/{filename}"

        # Parse form fields
        name = request.form.get("name")
        color = request.form.get("color")
        size = request.form.get("size")
        description = request.form.get("description")
        has_seeds = request.form.get("has_seeds", "false").lower() == "true"

        try:
            weight = float(request.form.get("weight"))
            price = float(request.form.get("price"))
            total_quantity = int(request.form.get("total_quantity"))
            available_quantity = int(
                request.form.get("available_quantity") or total_quantity
            )
        except Exception as value_err:
            return (
                jsonify({"error": "Invalid number field", "details": str(value_err)}),
                400,
            )

        # Parse and validate date only (no time)
        sell_by_date_str = request.form.get("sell_by_date")
        try:
            sell_by_date = datetime.strptime(sell_by_date_str, "%Y-%m-%d").date()
        except ValueError:
            return (
                jsonify(
                    {
                        "error": "Invalid date format",
                        "details": "Expected format: YYYY-MM-DD (e.g., 2025-04-24)",
                    }
                ),
                400,
            )
        
        # ✅ Enforce future date
        if sell_by_date <= datetime.utcnow().date():
            return (
                jsonify({
                    "error": "sell_by_date must be a future date",
                    "details": "Provided date is not in the future"
                }),
                400,
            )

        # Create and save Fruit
        fruit = Fruit(
            name=name,
            color=color,
            description=description,
            has_seeds=has_seeds,
            size=size,
            image_url=image_url,
        )

        if fruit.exists():
            return jsonify({"error": "Fruit with these details already exists."}), 400

        db.session.add(fruit)
        db.session.flush()

        # Create and save FruitInfo
        fruit_info = FruitInfo(
            fruit_id=fruit.fruit_id,
            weight=weight,
            price=price,
            total_quantity=total_quantity,
            available_quantity=available_quantity,
            created_at=datetime.utcnow(),
            sell_by_date=sell_by_date,
        )

        if fruit_info.exists():
            return (
                jsonify({"error": "Fruit info with these details already exists."}),
                400,
            )

        db.session.add(fruit_info)
        db.session.commit()

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

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Upload failed", "details": str(e)}), 500


# Get all fruits and their information
@fruit_bp.route("/", methods=["GET"])
@swag_from(
    {
        "tags": ["Fruit"],
        "description": "Get all fruits and their information",
        "responses": {
            200: {
                "description": "List of fruits and their information",
                "schema": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "fruit_id": {"type": "integer"},
                            "name": {"type": "string"},
                            "description": {"type": "string"},
                            "color": {"type": "string"},
                            "size": {"type": "string"},
                            "image_url": {"type": "string"},
                            "has_seeds": {"type": "boolean"},
                            "info_id": {"type": "integer"},
                            "weight": {"type": "number"},
                            "price": {"type": "number"},
                            "total_quantity": {"type": "integer"},
                            "sell_by_date": {"type": "string", "format": "date"},
                        },
                    },
                },
            },
            500: {"description": "Internal Server Error"},
        },
    }
)
def get_all_fruits():
    fruits = Fruit.query.all()
    fruit_info = FruitInfo.query.all()

    result = []
    for fruit in fruits:
        info = next((fi for fi in fruit_info if fi.fruit_id == fruit.fruit_id), None)
        if info:
            result.append(
                {
                    "fruit_id": fruit.fruit_id,
                    "name": fruit.name,
                    "description": fruit.description,
                    "color": fruit.color,
                    "size": fruit.size,
                    "image_url": fruit.image_url,
                    "has_seeds": fruit.has_seeds,
                    "info_id": info.info_id,
                    "weight": info.weight,
                    "price": info.price,
                    "total_quantity": info.total_quantity,
                    "available_quantity": info.available_quantity,
                    "sell_by_date": info.sell_by_date.isoformat(),
                }
            )

    return jsonify(result), 200


# Get fruit by ID
@fruit_bp.route("/<int:fruit_id>", methods=["GET"])
@swag_from(
    {
        "tags": ["Fruit"],
        "description": "Get fruit by ID",
        "parameters": [
            {"name": "fruit_id", "in": "path", "required": True, "type": "integer"}
        ],
        "responses": {
            200: {
                "description": "Fruit found",
                "schema": {
                    "type": "object",
                    "properties": {
                        "fruit_id": {"type": "integer"},
                        "name": {"type": "string"},
                        "description": {"type": "string"},
                        "color": {"type": "string"},
                        "size": {"type": "string"},
                        "image_url": {"type": "string"},
                        "has_seeds": {"type": "boolean"},
                        "info_id": {"type": "integer"},
                        "weight": {"type": "number"},
                        "price": {"type": "number"},
                        "total_quantity": {"type": "integer"},
                        "sell_by_date": {"type": "string", "format": "date-time"},
                    },
                },
            },
            404: {"description": "Fruit not found"},
            500: {"description": "Internal Server Error"},
        },
    }
)
def get_fruit_by_id(fruit_id):
    fruit = Fruit.query.get(fruit_id)
    if not fruit:
        return jsonify({"error": "Fruit not found"}), 404

    fruit_info = FruitInfo.query.filter_by(fruit_id=fruit.fruit_id).first()
    if not fruit_info:
        return jsonify({"error": "Fruit info not found"}), 404

    result = {
        "fruit_id": fruit.fruit_id,
        "name": fruit.name,
        "description": fruit.description,
        "color": fruit.color,
        "size": fruit.size,
        "image_url": fruit.image_url,
        "has_seeds": fruit.has_seeds,
        "info_id": fruit_info.info_id,
        "weight": fruit_info.weight,
        "price": fruit_info.price,
        "total_quantity": fruit_info.total_quantity,
        "sell_by_date": fruit_info.sell_by_date.isoformat(),
    }

    return jsonify(result), 200


@fruit_bp.route("/search", methods=["GET"])
@swag_from(
    {
        "tags": ["Fruit"],
        "description": "Search fruits by filters, range values, and keyword across name/description",
        "parameters": [
            {
                "name": "value",
                "in": "query",
                "type": "number",
                "required": False,
                "description": "Exact match on price, weight, total_quantity, or available_quantity",
            },
            {
                "name": "search",
                "in": "query",
                "type": "string",
                "required": False,
                "description": "Keyword search in name/description",
            },
            {"name": "price_min", "in": "query", "type": "number", "required": False},
            {"name": "price_max", "in": "query", "type": "number", "required": False},
            {
                "name": "available_quantity_min",
                "in": "query",
                "type": "number",
                "required": False,
            },
            {
                "name": "available_quantity_max",
                "in": "query",
                "type": "number",
                "required": False,
            },
            {
                "name": "total_quantity_min",
                "in": "query",
                "type": "number",
                "required": False,
            },
            {
                "name": "total_quantity_max",
                "in": "query",
                "type": "number",
                "required": False,
            },
            {"name": "weight_min", "in": "query", "type": "number", "required": False},
            {"name": "weight_max", "in": "query", "type": "number", "required": False},
        ],
        "responses": {
            200: {"description": "List of matching fruits"},
            400: {"description": "Bad Request"},
            500: {"description": "Internal Server Error"},
        },
    }
)
def search_fruits():
    try:
        query = FruitInfo.query.join(Fruit)

        # Exact match for numeric fields
        value = request.args.get("value")
        if value:
            try:
                val = float(value)
                query = query.filter(
                    (FruitInfo.price == val)
                    | (FruitInfo.weight == val)
                    | (FruitInfo.total_quantity == val)
                    | (FruitInfo.available_quantity == val)
                )
            except ValueError:
                return jsonify({"error": "Invalid numeric value"}), 400

        # Keyword search
        search_term = request.args.get("search", "").strip()
        if search_term:
            query = query.filter(
                (Fruit.name.ilike(f"%{search_term}%"))
                | (Fruit.color.ilike(f"%{search_term}%"))
            )

        # Helper to apply range filter and return updated query
        def apply_range(query, field):
            col = getattr(FruitInfo, field)
            min_val = request.args.get(f"{field}_min")
            max_val = request.args.get(f"{field}_max")
            if min_val:
                try:
                    query = query.filter(col >= float(min_val))
                except ValueError:
                    raise ValueError(f"{field}_min must be numeric")
            if max_val:
                try:
                    query = query.filter(col <= float(max_val))
                except ValueError:
                    raise ValueError(f"{field}_max must be numeric")
            return query

        # Apply filters
        for f in ["price", "available_quantity", "total_quantity", "weight"]:
            query = apply_range(query, f)

        # Fetch and format results
        infos = query.all()
        results = []
        for info in infos:
            fruit = info.fruit
            results.append(
                {
                    "fruit_id": fruit.fruit_id,
                    "name": fruit.name,
                    "description": fruit.description,
                    "color": fruit.color,
                    "size": fruit.size,
                    "image_url": fruit.image_url,
                    "has_seeds": fruit.has_seeds,
                    "info_id": info.info_id,
                    "weight": info.weight,
                    "price": info.price,
                    "total_quantity": info.total_quantity,
                    "available_quantity": info.available_quantity,
                    "sell_by_date": info.sell_by_date.isoformat(),
                }
            )

        return jsonify(results), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        return jsonify({"error": "Internal Server Error", "details": str(e)}), 500


# Update only the necessary fields of fruit information
@fruit_bp.route("/<int:fruit_id>", methods=["PUT"])
@swag_from(
    {
        "tags": ["Fruit"],
        "description": "Update fruit information",
        "parameters": [
            {"name": "fruit_id", "in": "path", "required": True, "type": "integer"},
            {
                "name": "body",
                "in": "body",
                "required": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "weight": {"type": "number"},
                        "price": {"type": "number"},
                        "total_quantity": {"type": "integer"},
                        "sell_by_date": {"type": "string", "format": "date-time"},
                    },
                },
            },
        ],
        "responses": {
            200: {
                "description": "Fruit information updated successfully",
            },
            404: {"description": "Fruit not found"},
            500: {"description": "Internal Server Error"},
        },
    }
)
def update_fruit_info(fruit_id):
    data = request.get_json()
    fruit = Fruit.query.get(fruit_id)
    if not fruit:
        return jsonify({"error": "Fruit not found"}), 404

    fruit_info = FruitInfo.query.filter_by(fruit_id=fruit.fruit_id).first()
    if not fruit_info:
        return jsonify({"error": "Fruit info not found"}), 404

    if "total_quantity" in data:
        fruit_info.total_quantity = data["total_quantity"]
        # Optionally update available_quantity too (only if explicitly provided)
        if "available_quantity" in data:
            fruit_info.available_quantity = data["available_quantity"]

    # Then continue updating other fields if any (weight, price, sell_by_date)
    for key, value in data.items():
        if key != "available_quantity" and hasattr(fruit_info, key):
            if key == "sell_by_date" and isinstance(value, str):
                value = datetime.strptime(value, "%Y-%m-%dT%H:%M:%S")
            setattr(fruit_info, key, value)

    db.session.commit()

    return (
        jsonify(
            {
                "message": "Fruit information updated successfully",
                "fruit_info": {
                    "fruit_id": fruit.fruit_id,
                    "weight": fruit_info.weight,
                    "price": fruit_info.price,
                    "total_quantity": fruit_info.total_quantity,
                    "available_quantity": fruit_info.available_quantity,
                    "sell_by_date": fruit_info.sell_by_date.isoformat(),
                },
            }
        ),
        200,
    )


# Delete fruit by ID
@fruit_bp.route("/delete", methods=["DELETE", "OPTIONS"])
@swag_from(
    {
        "tags": ["Fruit"],
        "description": "Delete multiple fruits by IDs",
        "parameters": [
            {
                "name": "body",
                "in": "body",
                "required": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "ids": {"type": "array", "items": {"type": "integer"}}
                    },
                    "required": ["ids"],
                },
            }
        ],
        "responses": {
            200: {"description": "Fruit(s) deleted successfully"},
            400: {"description": "No fruit IDs provided"},
            500: {"description": "Internal Server Error"},
        },
    }
)
def delete_fruits():
    if request.method == "OPTIONS":
        return "", 204

    try:
        data = request.get_json()
        ids = data.get("ids", [])

        if not ids:
            return jsonify({"error": "No fruit IDs provided"}), 400

        deleted_count = 0

        for fruit_id in ids:
            # Delete cart items first
            from app.models.cart import Cart

            Cart.query.filter_by(fruit_id=fruit_id).delete()

            # Delete orders referencing this fruit
            from app.models.orders import Order

            Order.query.filter_by(fruit_id=fruit_id).delete()

            # Delete fruit info
            fruit_info = FruitInfo.query.filter_by(fruit_id=fruit_id).first()
            if fruit_info:
                db.session.delete(fruit_info)

            # Delete fruit
            fruit = Fruit.query.get(fruit_id)
            if fruit:
                db.session.delete(fruit)
                deleted_count += 1

        if deleted_count == 0:
            return jsonify({"error": "Fruit not found"}), 404

        db.session.commit()
        return (
            jsonify({"message": f"Deleted {deleted_count} fruit(s) successfully"}),
            200,
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Deletion failed", "details": str(e)}), 500
