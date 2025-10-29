# app/__init__.py
import os
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask

# load .env from project root by default; you can pass an explicit path if needed
project_root = Path(__file__).resolve().parent.parent
env_path = project_root / '.env'
if env_path.exists():
    load_dotenv(env_path)
else:
    # try default loading (useful when running from project root)
    load_dotenv()

from .extensions import db, migrate, login_manager, csrf

def create_app(config_object=None):
    """Create and configure the Flask app."""
    app = Flask(
        __name__,
        static_folder='static',
        template_folder='templates'
    )

    # configuration: priority order
    # 1) explicit config_object param
    # 2) config.py in project root (optional)
    # 3) env vars with reasonable defaults
    if config_object:
        app.config.from_object(config_object)
    else:
        # try to load config.py at project root if present
        config_py = project_root / 'config.py'
        if config_py.exists():
            app.config.from_pyfile(str(config_py))

        # apply sensible defaults and override from env vars
        app.config.setdefault('SECRET_KEY', os.environ.get('SECRET_KEY', 'dev-secret-key'))
        app.config.setdefault('SQLALCHEMY_DATABASE_URI', os.environ.get('DATABASE_URL', f"sqlite:///{project_root/'data.db'}"))
        app.config.setdefault('SQLALCHEMY_TRACK_MODIFICATIONS', False)
        # file upload settings
        uploads_dir = os.environ.get('UPLOADS_DIR', 'uploads')  # relative to app/static
        app.config.setdefault('UPLOADS_DIR', uploads_dir)
        app.config.setdefault('PROFILE_PICS_DIR', os.environ.get('PROFILE_PICS_DIR', os.path.join(uploads_dir, 'profile_pic')))
        app.config.setdefault('MANGAS_DIR', os.environ.get('MANGAS_DIR', os.path.join(uploads_dir, 'mangas')))
        # maximum upload size (example: 32 MB)
        app.config.setdefault('MAX_CONTENT_LENGTH', int(os.environ.get('MAX_CONTENT_LENGTH', 32 * 1024 * 1024)))

    # initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    # login configuration
    login_manager.login_view = 'auth.login'  # update if your auth blueprint has a different endpoint
    login_manager.login_message = "Please log in to access this page."
    login_manager.login_message_category = "warning"

    # user loader (import inside to avoid circular imports)
    @login_manager.user_loader
    def load_user(user_id):
        from .models import User
        try:
            return User.query.get(int(user_id))
        except Exception:
            return None

    
    from .blueprints.auth.routes import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    #
    from .blueprints.manga.routes import manga_bp
    app.register_blueprint(manga_bp)
    #
    from .blueprints.author.routes import author_bp
    app.register_blueprint(author_bp, url_prefix='/author')
    #
    from .blueprints.admin.routes import admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')

    # simple example route to check app alive (remove later)
    @app.route('/_health')
    def _health():
        return 'ok', 200

    return app
