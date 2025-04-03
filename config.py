import os

class Config:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///fruitbasket.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'static', 'uploads')
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 5MB limit
