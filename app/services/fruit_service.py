from datetime import datetime
from typing import Any, Dict, List

from sqlalchemy import or_

from app.extensions import db
from app.models.fruit import Fruit, FruitInfo
from app.utils.log_config import get_logger

logger = get_logger("fruit_service")


def add_fruit_with_info(data: dict, image_url: str) -> tuple[Fruit, FruitInfo]:
    """
    Add a new fruit and its associated FruitInfo.

    Parameters
    ----------
    data : dict
        Parsed form data with validated fields.
    image_url : str
        Path or URL to uploaded image.

    Returns
    -------
    tuple
        Fruit and FruitInfo objects
    """
    try:
        fruit = Fruit(
            name=data["name"],
            color=data["color"],
            size=data["size"],
            has_seeds=data["has_seeds"],
            description=data.get("description"),
            image_url=image_url,
        )

        if fruit.exists():
            logger.warning("Duplicate fruit exists", name=fruit.name)
            raise ValueError("Fruit with these details already exists")

        db.session.add(fruit)
        db.session.flush()  # generate fruit_id

        fruit_info = FruitInfo(
            fruit_id=fruit.fruit_id,
            weight=data["weight"],
            price=data["price"],
            total_quantity=data["total_quantity"],
            available_quantity=data["available_quantity"],
            sell_by_date=data["sell_by_date"],
            created_at=datetime.utcnow(),
        )

        if fruit_info.exists():
            logger.warning("Duplicate fruit info exists", fruit_id=fruit.fruit_id)
            raise ValueError("Fruit info with these details already exists")

        db.session.add(fruit_info)
        db.session.commit()
        logger.info("Fruit and FruitInfo added", fruit_id=fruit.fruit_id)

        return fruit, fruit_info

    except Exception as e:
        db.session.rollback()
        logger.exception("Error adding fruit")
        raise


def get_all_fruits() -> List[Dict[str, Any]]:
    """
    Retrieve all fruits with their FruitInfo.

    Returns
    -------
    List[Dict]
    """
    fruits = Fruit.query.all()
    fruit_infos = FruitInfo.query.all()

    result = []
    for fruit in fruits:
        info = next((i for i in fruit_infos if i.fruit_id == fruit.fruit_id), None)
        if info:
            result.append(
                {
                    **fruit.to_dict(),
                    "info_id": info.info_id,
                    "weight": info.weight,
                    "price": info.price,
                    "total_quantity": info.total_quantity,
                    "available_quantity": info.available_quantity,
                    "sell_by_date": info.sell_by_date.isoformat(),
                }
            )

    logger.info("Fetched all fruits", count=len(result))
    return result


def get_fruit_by_id(fruit_id: int) -> Dict[str, Any] | None:
    """
    Retrieve fruit with its FruitInfo by ID.

    Parameters
    ----------
    fruit_id : int

    Returns
    -------
    dict or None
    """
    fruit = Fruit.query.get(fruit_id)
    if not fruit:
        return None

    info = FruitInfo.query.filter_by(fruit_id=fruit_id).first()
    if not info:
        return None

    logger.info("Fetched fruit by ID", fruit_id=fruit_id)
    return {
        **fruit.to_dict(),
        "info_id": info.info_id,
        "weight": info.weight,
        "price": info.price,
        "total_quantity": info.total_quantity,
        "available_quantity": info.available_quantity,
        "sell_by_date": info.sell_by_date.isoformat(),
    }


def search_fruits(filters: dict) -> List[Dict[str, Any]]:
    """
    Search fruits by keyword or numeric filters.

    Parameters
    ----------
    filters : dict
        Includes keys like 'search', 'value', 'price_min', etc.

    Returns
    -------
    list
        Filtered fruit results
    """
    try:
        query = FruitInfo.query.join(Fruit)

        value = filters.get("value")
        if value:
            val = float(value)
            query = query.filter(
                or_(
                    FruitInfo.price == val,
                    FruitInfo.weight == val,
                    FruitInfo.total_quantity == val,
                    FruitInfo.available_quantity == val,
                )
            )

        search_term = filters.get("search", "").strip()
        if search_term:
            query = query.filter(
                or_(
                    Fruit.name.ilike(f"%{search_term}%"),
                    Fruit.color.ilike(f"%{search_term}%"),
                )
            )

        for field in ["price", "weight", "total_quantity", "available_quantity"]:
            min_val = filters.get(f"{field}_min")
            max_val = filters.get(f"{field}_max")
            col = getattr(FruitInfo, field)

            if min_val:
                query = query.filter(col >= float(min_val))
            if max_val:
                query = query.filter(col <= float(max_val))

        infos = query.all()
        result = [
            {
                **info.fruit.to_dict(),
                "info_id": info.info_id,
                "weight": info.weight,
                "price": info.price,
                "total_quantity": info.total_quantity,
                "available_quantity": info.available_quantity,
                "sell_by_date": info.sell_by_date.isoformat(),
            }
            for info in infos
        ]

        logger.info("Search results returned", count=len(result))
        return result

    except Exception as e:
        logger.exception("Failed to search fruits")
        raise


def update_fruit_info(fruit_id: int, data: dict) -> FruitInfo | None:
    """
    Update FruitInfo by fruit ID.

    Parameters
    ----------
    fruit_id : int
    data : dict

    Returns
    -------
    FruitInfo or None
    """
    fruit = Fruit.query.get(fruit_id)
    if not fruit:
        return None

    info = FruitInfo.query.filter_by(fruit_id=fruit_id).first()
    if not info:
        return None

    try:
        if "total_quantity" in data:
            info.total_quantity = data["total_quantity"]
        if "available_quantity" in data:
            info.available_quantity = data["available_quantity"]

        for key in ["weight", "price", "sell_by_date"]:
            if key in data:
                value = data[key]
                if key == "sell_by_date" and isinstance(value, str):
                    value = datetime.strptime(value, "%Y-%m-%dT%H:%M:%S")
                setattr(info, key, value)

        db.session.commit()
        logger.info("Fruit info updated", fruit_id=fruit_id)
        return info

    except Exception as e:
        db.session.rollback()
        logger.exception("Failed to update fruit info", fruit_id=fruit_id)
        raise


def delete_fruits(ids: List[int]) -> int:
    """
    Delete fruits and related info by list of IDs.

    Parameters
    ----------
    ids : List[int]

    Returns
    -------
    int
        Number of fruits deleted
    """
    from app.models.cart import Cart
    from app.models.orders import Order

    deleted_count = 0

    try:
        for fruit_id in ids:
            Cart.query.filter_by(fruit_id=fruit_id).delete()
            Order.query.filter_by(fruit_id=fruit_id).delete()
            FruitInfo.query.filter_by(fruit_id=fruit_id).delete()

            fruit = Fruit.query.get(fruit_id)
            if fruit:
                db.session.delete(fruit)
                deleted_count += 1

        db.session.commit()
        logger.info("Fruits deleted", count=deleted_count)
        return deleted_count

    except Exception as e:
        db.session.rollback()
        logger.exception("Error deleting fruits")
        raise
