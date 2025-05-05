from app.models.fruit import Fruit, FruitInfo
from app import db
from datetime import datetime, timedelta

def test_fruit_to_dict(app):
    with app.app_context():
        fruit = Fruit(name="Pear", color="Green", size="L", has_seeds=False)
        db.session.add(fruit)
        db.session.commit()
        assert fruit.to_dict()["name"] == "Pear"

def test_fruit_exists(app):
    with app.app_context():
        fruit = Fruit(name="Apple", color="Red", size="M", has_seeds=True)
        db.session.add(fruit)
        db.session.commit()
        assert fruit.exists() == True

def test_fruitinfo_exists(app):
    with app.app_context():
        fruit = Fruit(name="Peach", color="Pink", size="S", has_seeds=True)
        db.session.add(fruit)
        db.session.flush()

        info = FruitInfo(
            fruit_id=fruit.fruit_id,
            weight=0.9,
            price=2.0,
            total_quantity=10,
            available_quantity=8,
            sell_by_date=datetime.utcnow() + timedelta(days=7)
        )
        db.session.add(info)
        db.session.commit()

        assert info.exists() == True
