from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()

def create_app(config: dict = None):
    app = Flask(__name__, instance_relative_config=False)
    app.config.update(
        SECRET_KEY = config.get("SECRET_KEY", "dev") if config else "dev",
        SQLALCHEMY_DATABASE_URI = config.get("DATABASE_URI", "sqlite:///manga.db") if config else "sqlite:///manga.db",
        SQLALCHEMY_TRACK_MODIFICATIONS = False,
    )

    db.init_app(app)
    login_manager.init_app(app)

    # register blueprints
    from .routes.main import main_bp
    app.register_blueprint(main_bp)

    # create DB tables if they don't exist
    with app.app_context():
        from . import models
        db.create_all()

    return app
