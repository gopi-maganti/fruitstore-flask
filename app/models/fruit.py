from datetime import datetime

from app import db


class Fruit(db.Model):
    __tablename__ = "fruit"
    fruit_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    color = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(200), nullable=True)
    has_seeds = db.Column(db.Boolean, default=False)
    size = db.Column(db.String(50), nullable=True)
    image_url = db.Column(db.String(200), nullable=True)

    fruit_info = db.relationship(
        "FruitInfo",
        back_populates="fruit",
        cascade="all, delete-orphan",
        lazy=True,
        passive_deletes=True,
    )

    def exists(self):
        filters = {
            "name": self.name,
            "color": self.color,
            "size": self.size,
            "has_seeds": self.has_seeds,
        }

        if self.description is not None:
            filters["description"] = self.description

        return Fruit.query.filter_by(**filters).first() is not None

    def to_dict(self):
        return {
            "fruit_id": self.fruit_id,
            "name": self.name,
            "color": self.color,
            "description": self.description,
            "has_seeds": self.has_seeds,
            "size": self.size,
            "image_url": self.image_url,
        }


class FruitInfo(db.Model):
    __tablename__ = "fruit_info"
    info_id = db.Column(db.Integer, primary_key=True)
    fruit_id = db.Column(
        db.Integer, db.ForeignKey("fruit.fruit_id", ondelete="CASCADE"), nullable=False
    )
    weight = db.Column(db.Float, nullable=False)
    price = db.Column(db.Float, nullable=False)
    total_quantity = db.Column(db.Integer, nullable=False)
    available_quantity = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    sell_by_date = db.Column(db.DateTime, nullable=False)

    fruit = db.relationship("Fruit", back_populates="fruit_info")

    def exists(self):
        return (
            FruitInfo.query.filter_by(
                fruit_id=self.fruit_id,
                weight=self.weight,
                price=self.price,
                total_quantity=self.total_quantity,
                sell_by_date=self.sell_by_date,
            ).first()
            is not None
        )

    def __repr__(self):
        return f"<FruitInfo {self.fruit_id}, Weight: {self.weight}, Price: {self.price}, Quantity: {self.total_quantity}>"
