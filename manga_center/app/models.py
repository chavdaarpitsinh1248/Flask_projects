from app import db, login_manager
from flask_login import UserMixin
from datetime import datetime

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ---------------------------------
#               USER
# ---------------------------------

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(25), unique=True, nullable = False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    #Relationship
    #author_profile = db.relationship('Author', backref='user', uselist=False)
    #admin_profile = db.relationship('Admin', backref='user', uselist=False)

    def __repr__(self):
        return f"<User {self.username}>"
    
# ---------------------------------
#               AUTHOR
# ---------------------------------

class Author(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    pen_name = db.Column(db.String(50), nullable=False)
    bio = db.Column(db.Text, nullable=True)
    joined_on = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='author_profile', lazy=True)

    def __repr__(self):
        return f"<Author {self.pen_name}>"
    
# ---------------------------------
#               ADMIN
# ---------------------------------

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    role = db.Column(db.String(20), default='moderator')
    date_assigned = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='admin_profile', lazy=True)

    def __repr__(self):
        return f"<Admin {self.user.username} ({self.role})>"