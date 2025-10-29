# app/models.py
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from .extensions import db

# Association tables for many-to-many relationships
manga_genres = db.Table(
    'manga_genres',
    db.Column('manga_id', db.Integer, db.ForeignKey('manga.id'), primary_key=True),
    db.Column('genre_id', db.Integer, db.ForeignKey('genre.id'), primary_key=True)
)

manga_tags = db.Table(
    'manga_tags',
    db.Column('manga_id', db.Integer, db.ForeignKey('manga.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)


class User(UserMixin, db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='reader')  # 'reader', 'author', 'admin'
    profile_pic = db.Column(db.String(255), nullable=True)  # relative path to profile pic in static/uploads/profile_pic/
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # relationships
    mangas = db.relationship('Manga', back_populates='author', lazy='dynamic')
    comments = db.relationship('Comment', back_populates='user', lazy='dynamic')
    bookmarks = db.relationship('Bookmark', back_populates='user', lazy='dynamic')
    history = db.relationship('History', back_populates='user', lazy='dynamic')
    notifications = db.relationship('Notification', back_populates='user', lazy='dynamic')

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def is_admin(self) -> bool:
        return self.role == 'admin'

    def is_author(self) -> bool:
        # admin is treated as author too (can manage everything)
        return self.role == 'author' or self.role == 'admin'

    def __repr__(self):
        return f"<User {self.username}>"


class Manga(db.Model):
    __tablename__ = 'manga'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(255), unique=True, nullable=False, index=True)  # friendly URL
    description = db.Column(db.Text, nullable=True)
    cover_image = db.Column(db.String(255), nullable=True)  # relative path to cover image
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    is_published = db.Column(db.Boolean, default=True, nullable=False)

    # relationships
    author = db.relationship('User', back_populates='mangas')
    genres = db.relationship('Genre', secondary=manga_genres, back_populates='mangas', lazy='dynamic')
    tags = db.relationship('Tag', secondary=manga_tags, back_populates='mangas', lazy='dynamic')
    chapters = db.relationship('Chapter', back_populates='manga', order_by='Chapter.number', lazy='dynamic')
    comments = db.relationship('Comment', back_populates='manga', lazy='dynamic')
    bookmarks = db.relationship('Bookmark', back_populates='manga', lazy='dynamic')

    def __repr__(self):
        return f"<Manga {self.title} (id={self.id})>"


class Genre(db.Model):
    __tablename__ = 'genre'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False, unique=True)
    slug = db.Column(db.String(80), nullable=False, unique=True)

    mangas = db.relationship('Manga', secondary=manga_genres, back_populates='genres', lazy='dynamic')

    def __repr__(self):
        return f"<Genre {self.name}>"


class Tag(db.Model):
    __tablename__ = 'tag'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False, unique=True)
    slug = db.Column(db.String(80), nullable=False, unique=True)

    mangas = db.relationship('Manga', secondary=manga_tags, back_populates='tags', lazy='dynamic')

    def __repr__(self):
        return f"<Tag {self.name}>"


class Chapter(db.Model):
    __tablename__ = 'chapter'

    id = db.Column(db.Integer, primary_key=True)
    manga_id = db.Column(db.Integer, db.ForeignKey('manga.id'), nullable=False)
    number = db.Column(db.Integer, nullable=False)  # chapter number (1, 2, 3, ...)
    title = db.Column(db.String(255), nullable=True)
    slug = db.Column(db.String(255), nullable=True, index=True)  # optional friendly slug for the chapter
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # relationships
    manga = db.relationship('Manga', back_populates='chapters')
    pages = db.relationship('Page', back_populates='chapter', order_by='Page.page_number', lazy='dynamic')
    comments = db.relationship('Comment', back_populates='chapter', lazy='dynamic')

    __table_args__ = (
        db.UniqueConstraint('manga_id', 'number', name='uq_chapter_manga_number'),
    )

    def __repr__(self):
        return f"<Chapter manga_id={self.manga_id} number={self.number}>"


class Page(db.Model):
    __tablename__ = 'page'

    id = db.Column(db.Integer, primary_key=True)
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapter.id'), nullable=False)
    page_number = db.Column(db.Integer, nullable=False)
    image_path = db.Column(db.String(255), nullable=False)  # relative path to static/uploads/...

    chapter = db.relationship('Chapter', back_populates='pages')

    __table_args__ = (
        db.UniqueConstraint('chapter_id', 'page_number', name='uq_page_chapter_pagenum'),
    )

    def __repr__(self):
        return f"<Page chapter_id={self.chapter_id} page={self.page_number}>"


class Comment(db.Model):
    __tablename__ = 'comment'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    manga_id = db.Column(db.Integer, db.ForeignKey('manga.id'), nullable=False)
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapter.id'), nullable=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=True)  # reply threads

    # relationships
    user = db.relationship('User', back_populates='comments')
    manga = db.relationship('Manga', back_populates='comments')
    chapter = db.relationship('Chapter', back_populates='comments')
    replies = db.relationship('Comment', backref=db.backref('parent', remote_side=[id]), lazy='dynamic')

    def __repr__(self):
        return f"<Comment id={self.id} user_id={self.user_id}>"


class Bookmark(db.Model):
    __tablename__ = 'bookmark'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    manga_id = db.Column(db.Integer, db.ForeignKey('manga.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship('User', back_populates='bookmarks')
    manga = db.relationship('Manga', back_populates='bookmarks')

    __table_args__ = (
        db.UniqueConstraint('user_id', 'manga_id', name='uq_user_manga_bookmark'),
    )

    def __repr__(self):
        return f"<Bookmark user={self.user_id} manga={self.manga_id}>"


class History(db.Model):
    __tablename__ = 'history'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    manga_id = db.Column(db.Integer, db.ForeignKey('manga.id'), nullable=False)
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapter.id'), nullable=True)
    last_page_read = db.Column(db.Integer, nullable=True)
    last_read_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship('User', back_populates='history')
    manga = db.relationship('Manga')     # optional convenience relationship
    chapter = db.relationship('Chapter') # optional convenience relationship

    __table_args__ = (
        db.UniqueConstraint('user_id', 'manga_id', name='uq_user_manga_history'),
    )

    def __repr__(self):
        return f"<History user={self.user_id} manga={self.manga_id} page={self.last_page_read}>"


class Notification(db.Model):
    __tablename__ = 'notification'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    manga_id = db.Column(db.Integer, db.ForeignKey('manga.id'), nullable=True)
    message = db.Column(db.String(255), nullable=False)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship('User', back_populates='notifications')

    def __repr__(self):
        return f"<Notification id={self.id} user={self.user_id} read={self.is_read}>"
