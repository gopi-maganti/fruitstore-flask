import os

from flasgger import Swagger
from flask import Flask
from flask_cors import CORS

from app.config.config import Config
from app.extensions import db
from app.utils.log_config import setup_logging


def create_app():
    setup_logging()
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    CORS(
        app,
        supports_credentials=True,
        resources={r"/*": {"origins": "https://d3pj8ooak7hbtk.cloudfront.net"}},
    )

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    Swagger(app)

    from app.routes.cart_api import cart_bp
    from app.routes.fruit_api import fruit_bp
    from app.routes.order_api import order_bp
    from app.routes.user_api import user_bp

    app.register_blueprint(fruit_bp, url_prefix="/fruit")
    app.register_blueprint(user_bp, url_prefix="/user")
    app.register_blueprint(order_bp, url_prefix="/order")
    app.register_blueprint(cart_bp, url_prefix="/cart")

    with app.app_context():
        db.create_all()
        seed_guest_user()

    return app


def seed_guest_user():
    from app.models.users import User

    guest_user = User.query.get(-1)
    if not guest_user:
        guest = User(
            user_id=-1,
            name="Guest",
            email="guest@fruitstore.com",
            phone_number="0000000000",
        )
        db.session.add(guest)
        db.session.commit()
