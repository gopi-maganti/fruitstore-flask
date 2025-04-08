from app import db

class Cart(db.Model):
    __tablename__ = 'cart'
    cart_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    fruit_id = db.Column(db.Integer, db.ForeignKey('fruit.fruit_id'), nullable=False)
    info_id = db.Column(db.Integer, db.ForeignKey('fruit_info.info_id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    item_price = db.Column(db.Float, nullable=True)
    added_date = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    user = db.relationship('User', backref='cart')
    fruit = db.relationship('Fruit', backref='cart')
    fruit_info = db.relationship('FruitInfo', backref='cart')

    def save(self):
        db.session.add(self)
        db.session.commit()
    
    def __repr__(self):
        return f"<Cart {self.cart_id}, User: {self.user_id}, Fruit: {self.fruit_id}, Quantity: {self.quantity}>"
    
    def as_dict(self):
        return {
            'cart_id': self.cart_id,
            'user_id': self.user_id,
            'fruit_id': self.fruit_id,
            'quantity': self.quantity,
            'item_price': self.item_price,
            'added_date': self.added_date.isoformat() if self.added_date else None,
            'fruit_name': self.fruit.name if self.fruit else None,
            'image_url': self.fruit.image_url if self.fruit else None
        }
