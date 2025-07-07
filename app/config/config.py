import os
from dotenv import load_dotenv
from aws_utils.secrets_manager import get_db_credentials

load_dotenv()

class Config:
    """
    Application configuration class.

    Prioritizes AWS Secrets Manager for DB credentials if USE_AWS_SECRET=true,
    otherwise falls back to .env values.
    """

    USE_AWS_SECRET = os.getenv("USE_AWS_SECRET", "false").lower() == "true"

    if USE_AWS_SECRET:
        secret_name = os.getenv("AWS_SECRET_NAME", "fruitstore-db-secret")
        region = os.getenv("AWS_REGION", "us-east-1")
        try:
            secret = get_db_credentials(secret_name, region)
            DB_USER = secret["username"]
            DB_PASSWORD = secret["password"]
            DB_HOST = secret["host"]
            DB_PORT = str(secret.get("port", 5432))
            DB_NAME = secret["dbname"]
        except Exception as e:
            raise RuntimeError(f"Failed to fetch DB credentials from AWS: {e}")
    else:
        DB_USER = os.getenv("DB_USER")
        DB_PASSWORD = os.getenv("DB_PASSWORD")
        DB_HOST = os.getenv("DB_HOST", "localhost")
        DB_PORT = os.getenv("DB_PORT", "5432")
        DB_NAME = os.getenv("DB_NAME")

    SQLALCHEMY_DATABASE_URI = (
        f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(os.getcwd(), "static", "uploads")
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB max
