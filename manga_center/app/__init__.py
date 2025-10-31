from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)

    app.config['SECRET_KEY'] = 'ariptmanga123'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///manga_center.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    login_manager.init_app(app)

    #Redirect unauthorized users to login page
    login_manager.login_view = 'users.login'
    login_manager.login_message_category = 'info'

    from app.routes.main import main_bp
    from app.routes.users import users_bp
    from app.routes.admin import admin_bp
    from app.routes.author import author_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(author_bp)

    #Import Models to make sure they are register
    from app import models

    #create database table if not exist
    with app.app_context():
        db.create_all()

    return app