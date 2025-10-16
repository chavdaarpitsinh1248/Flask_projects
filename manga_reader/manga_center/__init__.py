from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from flask_migrate import Migrate
from .models import Notification, User

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
migrate = Migrate()

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config['SECRET_KEY'] = 'chavdaarpit123'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../instance/manga_reader.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    # Import blueprints
    from .routes.auth_routes import auth_bp
    from .routes.manga_routes import manga_bp
    from .routes.comment_routes import comment_bp
    from .routes.profile_routes import profile_bp
    from .routes.search_routes import search_bp
    from .routes.notif_routes import notif_bp
    from .routes.studio_routes import studio_bp
    from .routes.admin_routes import admin_bp
    from .routes.report_routes import report_bp
    from .routes.user_routes import user_bp
    from .routes.bookmark_routes import bookmark_bp

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(manga_bp, url_prefix='/manga')
    app.register_blueprint(comment_bp, url_prefix='/comment')
    app.register_blueprint(profile_bp, url_prefix='/profile')
    app.register_blueprint(search_bp, url_prefix='/search')
    app.register_blueprint(notif_bp, url_prefix='/notifications')
    app.register_blueprint(studio_bp, url_prefix='/studio')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(report_bp, url_prefix='/reports')
    app.register_blueprint(user_bp, url_prefix='/user')
    app.register_blueprint(bookmark_bp, url_prefix='/bookmarks')


    #Flask login user loader
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    @app.context_processor
    def inject_unread_notifications():
        if current_user.is_authenticated:
            unread_count = Notification.query.filter_by(user_id=current_user.id, read=False).count()
            return dict(unread_count=unread_count)
        return dict(unread_count=0)        

    return app
