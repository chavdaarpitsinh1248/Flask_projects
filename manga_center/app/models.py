from . import db
from flask_login import UserMixin

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

class Manga(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)

class Chapter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    manga_id = db.Column(db.Integer, db.ForeignKey('manga.id'), nullable=False)
    number = db.Column(db.Integer, nullable=False)
    folder = db.Column(db.String(300), nullable=False)  # path under static/uploads
    manga = db.relationship('Manga', backref='chapters')
