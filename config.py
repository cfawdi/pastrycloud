import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "atelier-alami-secret-key-change-me")

    # Database: PostgreSQL via DATABASE_URL, SQLite fallback for local dev
    database_url = os.environ.get("DATABASE_URL", "")
    if database_url:
        # Neon/Heroku use postgres://, SQLAlchemy needs postgresql://
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        SQLALCHEMY_DATABASE_URI = database_url
    else:
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'pastry_shop.db')}"

    SQLALCHEMY_TRACK_MODIFICATIONS = False
