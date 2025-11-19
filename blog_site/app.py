from flask import Flask
from flask_login import current_user
from forms import SearchForm
from extensions import db, login_manager, moment, migrate
from routes.auth_routes import auth_bp
from routes.posts_routes import post_bp
from routes.ajax_routes import ajax_bp
from routes.search_routes import search_bp
from routes.main_routes import main_bp
from routes.notif_routes import notif_bp
#from routes.ai_routes import ai_bp
from dotenv import load_dotenv


load_dotenv()


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'arpitchavda123'
    import os
    os.makedirs(app.instance_path, exist_ok=True)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.instance_path, 'blog.db')
    
    #Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    moment.init_app(app)
    migrate.init_app(app, db)
    
    

    from models import User, Comment, Post

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    login_manager.login_view = 'auth.login'

    #Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(ajax_bp)
    app.register_blueprint(post_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(notif_bp)
    #app.register_blueprint(ai_bp)


    #Context Processors
    @app.context_processor
    def inject_user():
        from flask_login import current_user
        return dict(current_user=current_user)
    @app.context_processor
    def inject_search_form():
        return dict(search_form=SearchForm())
    @app.context_processor
    def inject_comment_model():
        return dict(Comment = Comment)
    @app.context_processor
    def inject_notifications():
        if hasattr(current_user, 'notifications'):
            unread_count = sum(1 for n in current_user.notifications if not n.is_read)
            return dict(unread_notifications=unread_count)
        return dict(unread_notifications=0)

    
    return app

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(debug=True)