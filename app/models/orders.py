from app import db
from app.models.fruit import Fruit, FruitInfo
from app.models.users import User

class Order(db.Model):
    __tablename__ = 'orders'
    order_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    fruit_id = db.Column(db.Integer, db.ForeignKey('fruit.fruit_id'), nullable=False)
    info_id = db.Column(db.Integer, db.ForeignKey('fruit_info.info_id'), nullable=False)
    is_seeded = db.Column(db.Boolean, default=False)
    quantity = db.Column(db.Integer, nullable=False)
    order_date = db.Column(db.DateTime, default=db.func.current_timestamp())
    price_by_fruit = db.Column(db.Float, nullable=False)

    user = db.relationship('User', backref='orders')
    fruit = db.relationship('Fruit', backref='orders')
    fruit_info = db.relationship('FruitInfo', backref='orders')

    @property
    def fruit_name(self):
        return self.fruit.name if self.fruit else None

    @property
    def fruit_size(self):
        return self.fruit.size if self.fruit else None

    @property
    def total_price(self):
        return self.quantity * self.price_by_fruit

    def save(self):
        db.session.add(self)
        db.session.commit()

    def __repr__(self):
        return f"<Order {self.order_id}, User: {self.user_id}, Fruit: {self.fruit_name}, Quantity: {self.quantity}>"

    def as_dict(self):
        return {
            'order_id': self.order_id,
            'user_id': self.user_id,
            'fruit_id': self.fruit_id,
            'info_id': self.info_id,
            'fruit_name': self.fruit_name,
            'fruit_size': self.fruit_size,
            'is_seeded': self.is_seeded,
            'quantity': self.quantity,
            'order_date': str(self.order_date),
            'price_by_fruit': self.price_by_fruit,
            'total_price': self.total_price
        }
