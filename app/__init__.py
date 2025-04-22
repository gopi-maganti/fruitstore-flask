from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from flasgger import Swagger
from flask_cors import CORS
import os

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True) 

    db.init_app(app)
    CORS(app, supports_credentials=True, resources={r"/*": {"origins": "*"}}, methods=["GET", "POST", "PUT", "DELETE"])

    Swagger(app)

    @app.before_request
    def before_request():
        if 'sqlite' in str(db.engine.url):
            db.session.execute(text('PRAGMA foreign_keys=ON'))

    from app.apis.fruit_api import fruit_bp
    from app.apis.user_api import user_bp
    from app.apis.order_api import order_bp
    from app.apis.cart_api import cart_bp

    app.register_blueprint(fruit_bp, url_prefix='/fruit')
    app.register_blueprint(user_bp, url_prefix='/user')
    app.register_blueprint(order_bp, url_prefix='/order')
    app.register_blueprint(cart_bp, url_prefix='/cart')

    with app.app_context():
        db.create_all()
        seed_guest_user()  # <-- this ensures guest user exists

    return app

# 🔽 Function to create the guest user if it doesn't exist
def seed_guest_user():
    from app.models.users import User
    guest_user = User.query.get(-1)
    if not guest_user:
        guest = User(
            user_id=-1,
            name="Guest",
            email="guest@fruitstore.com",
            phone_number="0000000000"
        )
        db.session.add(guest)
        db.session.commit()
