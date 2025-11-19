from flask import Flask 
from .extensions import db, migrate, login_manager, bcrypt
from .routes.auth_routes import auht_bp
from .routes.expense_routes import expense_bp
from .routes.dashboard_routes import dashboard_bp
from .models import User, Expense 

def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")

    # initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    bcrypt.init_app(app)

    login_manager.login_view="auth.login"

    # register blueprints
    app.register_blueprint(auht_bp, url_prefix="/auth")
    app.register_blueprint(expense_bp, url_prefix="/expense")
    app.register_blueprint(dashboard_bp, url_prefix="/dashboard")

    return app