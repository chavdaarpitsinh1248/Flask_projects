from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_moment import Moment
from flask_migrate import Migrate

db=SQLAlchemy()
login_manager=LoginManager()
moment=Moment()
migrate=Migrate()