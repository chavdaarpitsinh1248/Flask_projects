from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os
from flask_migrate import Migrate
from flask_wtf import CSRFProtect
from flask_moment import Moment

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()
moment = Moment()


from datetime import datetime

def timeago(time):
    if not time:
        return ""
        
    now = datetime.utcnow()
    diff = now - time
    seconds = diff.total_seconds()

    if seconds < 60:
        return "just now"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    elif seconds < 86400:
        hours = int(seconds // 3600)
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif seconds < 2592000:
        days = int(seconds // 86400)
        return f"{days} day{'s' if days > 1 else ''} ago"
    else:
        months = int(seconds // 2592000)
        return f"{months} month{'s' if months > 1 else ''} ago"





def create_app():
    app = Flask(__name__, static_folder='static')

    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
    app.config['COVER_UPLOAD_FOLDER'] = os.path.join(app.config['UPLOAD_FOLDER'], 'manga_cover_images')
    app.config['MANGA_FOLDER'] = os.path.join(app.config['UPLOAD_FOLDER'], 'manga')
    app.config['PROFILE_PIC_FOLDER'] = os.path.join(app.config['UPLOAD_FOLDER'], 'profile_pic')

    # ensure directories exist
    os.makedirs(app.config['COVER_UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['MANGA_FOLDER'], exist_ok=True)
    os.makedirs(app.config['PROFILE_PIC_FOLDER'], exist_ok=True)

    app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2MB limit
    app.config['SECRET_KEY'] = 'ariptmanga123'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///manga_center.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


    csrf.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    migrate = Migrate(app, db)
    moment.init_app(app)

    login_manager.login_view = 'users.login'
    login_manager.login_message_category = 'info'

    from app.routes.main import main_bp
    from app.routes.users import users_bp
    from app.routes.admin import admin_bp
    from app.routes.author import author_bp
    from app.routes.public import public_bp
    from app.routes.comments import comment_bp
    from app.routes.notif import notif_bp
    from app.routes.search import search_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(author_bp)
    app.register_blueprint(public_bp)
    app.register_blueprint(comment_bp)
    app.register_blueprint(notif_bp)
    app.register_blueprint(search_bp)

    from app import models  # make sure models are imported
    from flask_wtf.csrf import generate_csrf

    @app.context_processor
    def inject_csrf_token():
        return dict(csrf_token=generate_csrf)


    # Register filter
    app.jinja_env.filters['timeago'] = timeago
    


    return app
