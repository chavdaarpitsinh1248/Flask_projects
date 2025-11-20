import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY")  or "dev_secret_key_1234"
    SQLALCHEMY_DATABASE_URI = "sqlite:///expense_tracker.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False 