import os
from datetime import timedelta
from urllib.parse import quote_plus
from dotenv import load_dotenv

# Load variables from .env into the environment. Without this line, every
# os.environ.get(...) below silently falls back to its default value,
# ignoring whatever was typed into .env (this was the cause of the
# "Access denied for user 'root'@'localhost'" MySQL error).
load_dotenv()


class Config:
    """Base configuration."""

    # ---- Core Flask ----
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")

    # ---- MySQL / SQLAlchemy ----
    DB_USER = os.environ.get("DB_USER", "root")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "password")
    DB_HOST = os.environ.get("DB_HOST", "localhost")
    DB_PORT = os.environ.get("DB_PORT", "3306")
    DB_NAME = os.environ.get("DB_NAME", "freelancehub")

    _raw_db_url = os.environ.get("DATABASE_URL")
    if _raw_db_url:
        if _raw_db_url.startswith("postgres://"):
            SQLALCHEMY_DATABASE_URI = _raw_db_url.replace("postgres://", "postgresql://", 1)
        else:
            SQLALCHEMY_DATABASE_URI = _raw_db_url
    elif os.environ.get("DB_HOST") and os.environ.get("DB_HOST") != "localhost":
        SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_USER}:{quote_plus(DB_PASSWORD)}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    else:
        # Fallback to SQLite in /tmp for serverless environment compatibility
        _tmp_dir = "/tmp" if os.name != "nt" else os.getenv("TEMP", "C:\\tmp")
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(_tmp_dir, 'freelancehub.db')}"

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_recycle": 280,
        "pool_pre_ping": True,
    }

    # ---- JWT ----
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "dev-jwt-secret-change-in-production")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=8)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    JWT_BLACKLIST_ENABLED = True
    JWT_BLACKLIST_TOKEN_CHECKS = ["access", "refresh"]

    # ---- Uploads ----
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "static", "uploads")
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}
