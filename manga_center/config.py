# config.py
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

class BaseConfig:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", f"sqlite:///{BASE_DIR/'data.db'}")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Uploads (relative to app.static_folder)
    UPLOADS_DIR = os.environ.get("UPLOADS_DIR", "uploads")
    PROFILE_PICS_DIR = os.environ.get("PROFILE_PICS_DIR", f"{UPLOADS_DIR}/profile_pic")
    MANGAS_DIR = os.environ.get("MANGAS_DIR", f"{UPLOADS_DIR}/mangas")

    # Max upload (bytes) - default 32 MB
    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_CONTENT_LENGTH", 32 * 1024 * 1024))

class DevelopmentConfig(BaseConfig):
    DEBUG = True

class ProductionConfig(BaseConfig):
    DEBUG = False
