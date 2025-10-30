from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)

    app.config['SECRET_KEY'] = 'ariptmanga123'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///manga_center.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    from app.routes.main import main_bp
    from app.routes.users import users_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(users_bp)

    #Import Models to make sure they are register
    from app import models

    #create database table if not exist
    with app.app_context():
        db.create_all()

    return app