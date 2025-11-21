from flask import Flask 
from .extensions import db, migrate, login_manager
from .models import User
from config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # initialize extensionns
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # user loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    
    # register bluprints here


    return app
