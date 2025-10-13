import os
from flask import Flask, g
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf import CSRFProtect
from time import time

#singletons to be imported elsewhere
db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()


def create_app():
    # instance db relative keeps db in \instance
    app = Flask(__name__, instance_relative_config = True)

    #basic config change SECRET_KEY for non-dev
    app.config.from_mapping(
        SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key"),
        SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(app.instance_path, "manga.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS = False,

        # where we'll store uploaded images
        UPLOAD_FOLDER=os.path.join(app.root_path, "static", "uploads"),
        MAX_CONTENT_LENGTH = 32*1024*1024 # 32MB
    )

    # ensure instance and upload folders exist
    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    #initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    #--- simple Local cache (dictionary) ---
    cache = {}

    @app.before_request
    def check_cache():
        g.cache = cache


    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please login to access this page"

    # register buleprints (import inside to avoid circuler imports)
    from manga_rocks.main.routes import main_bp
    from manga_rocks.auth.routes import auth_bp
    from manga_rocks.admin.routes import admin_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')

    #optional: shell context helper (models will be added later)
    @app.shell_context_processor
    def make_shell_context():
        #import models lazily so step 1 doesn't require them yet
        try:
            from .models import User, Manga, Chapter, Page, Genre, Favorite, Comment
            return {
                "db":db, "User":User, "Manga":Manga, "Chapter":Chapter, "Page":Page, "Genre":Genre, "Favorite":Favorite, "Comment":Comment
            }
        except Exception:
            return {"db": db}
        
    return app