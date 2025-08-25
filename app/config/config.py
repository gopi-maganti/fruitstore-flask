import os

from dotenv import load_dotenv

from aws_utils.secrets_manager import get_db_credentials

load_dotenv()


class Config:
    """
    Application configuration class.

    - Uses SQLite if FLASK_ENV=test
    - Prioritizes AWS Secrets Manager if USE_AWS_SECRET=true (non-test envs)
    - Falls back to .env-based credentials otherwise
    """

    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    USE_AWS_SECRET = os.getenv("USE_AWS_SECRET", "false").lower() == "true"
    USE_S3_UPLOADS = os.getenv("USE_S3_UPLOADS", "true").lower() == "true"

    if FLASK_ENV == "test":
        # ✅ Force SQLite for test runs
        SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
        DB_USER = ""
        DB_PASSWORD = ""
        DB_HOST = ""
        DB_PORT = ""
        DB_NAME = ""
    else:
        if USE_AWS_SECRET:
            secret_name = os.getenv("DB_SECRET_NAME", "fruitstore/db_credentials")
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
            DB_HOST = os.getenv(
                "DB_HOST",
                "fruitstore-cluster.cluster-c69cq4mcm794.us-east-1.rds.amazonaws.com",
            )
            DB_PORT = os.getenv("DB_PORT", "5432")
            DB_NAME = os.getenv("DB_NAME")

        SQLALCHEMY_DATABASE_URI = (
            f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ✅ Dummy path to avoid KeyError in tests when using S3
    if not USE_S3_UPLOADS:
        UPLOAD_FOLDER = os.path.join(os.getcwd(), "static", "uploads")
    else:
        UPLOAD_FOLDER = "/tmp/uploads"

    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB
