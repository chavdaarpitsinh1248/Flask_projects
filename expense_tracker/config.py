import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") 
    SQLALCHEMY_DATABASE_URI = "sqlite:///expense_tracker.db"
    SQLALCHEMY_TRACK_MODIFICATION = False 