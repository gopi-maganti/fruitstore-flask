from app import db

class User(db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone_number = db.Column(db.String(10), unique=True, nullable=True)

    def __repr__(self):
        return f"<User {self.name}, Email: {self.email}, Phone: {self.phone_number}>"
    
    def exists(self):
        return User.query.filter_by(
            name=self.name,
            email=self.email,
            phone_number=self.phone_number
        ).first() is not None
    
    def save(self):
        if self.exists():
            raise ValueError("User with these details already exists.")
        db.session.add(self)
        db.session.commit()

    def to_dict(self):
        return {
            'user_id': self.user_id,
            'name': self.name,
            'email': self.email,
            'phone_number': self.phone_number,
        }