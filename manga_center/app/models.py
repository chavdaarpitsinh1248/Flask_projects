from app import db, login_manager
import os
from flask import url_for
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

    user = db.relationship('User', backref=db.backref('author_profile', uselist=False))

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
    
# ---------------------------------
#               MANGA
# ---------------------------------

class Manga(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    cover_image = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Foreign key to Author
    author_id = db.Column(db.Integer, db.ForeignKey('author.id'), nullable=False)

    # Relationship back to auhtor
    author = db.relationship('Author', backref=db.backref('mangas', lazy=True))

    # computed property for template
    @property
    def cover_url(self):
        if self.cover_image:
            # Ensure we build the correct URL to the uploaded image
            filename = os.path.basename(self.cover_image)  # extract just the filename
            return url_for('static', filename=f'uploads/manga_cover_images/{filename}')
        # fallback to default cover
        return url_for('static', filename='images/default_cover.jpg')


    def __repr__(self):
        return f"<Manga {self.title}>"
    
class Chapter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    number = db.Column(db.Integer, nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    content_path = db.Column(db.String(255), nullable=True) # Folder or zip path
    manga_id = db.Column(db.Integer, db.ForeignKey('manga.id'), nullable=False)

    # Relationship back to Manga
    manga = db.relationship('Manga', backref=db.backref('chapters', lazy=True))

    def __repr__(self):
        return f"<Chapter {self.title} (Manga ID: {self.manga_id})>"