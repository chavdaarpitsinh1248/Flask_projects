from app import db, login_manager
import os
from flask import url_for
from flask_login import UserMixin
from datetime import datetime

# ---------------------------------
#               LOGIN LOADER
# ---------------------------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ---------------------------------
#               USER
# ---------------------------------
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    profile_pic = db.Column(db.String(200), nullable=True)
    is_admin = db.Column(db.Boolean, default=False)

    @property
    def profile_pic_url(self):
        if self.profile_pic:
            filename = os.path.basename(self.profile_pic)
            return url_for('static', filename=f'uploads/profile_pics/{filename}')
        return url_for('static', filename='images/default_user.png')

    def __repr__(self):
        return f'<User {self.username}>'

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

    author_id = db.Column(db.Integer, db.ForeignKey('author.id'), nullable=False)
    author = db.relationship('Author', backref=db.backref('mangas', lazy=True))

    # ✅ One-way relationship (no duplicate in Chapter)
    chapters = db.relationship('Chapter', backref='manga', lazy=True, cascade="all, delete-orphan")

    # ✅ Optional backrefs added later (comments, likes, bookmarks)
    comments = db.relationship('Comment', backref='manga', lazy=True, cascade="all, delete-orphan")
    likes = db.relationship('Like', backref='manga', lazy=True, cascade="all, delete-orphan")
    bookmarked_by = db.relationship('Bookmark', backref='manga', lazy=True, cascade="all, delete-orphan")

    @property
    def latest_chapter_title(self):
        latest = Chapter.query.filter_by(manga_id=self.id).order_by(Chapter.upload_date.desc()).first()
        return latest.title if latest else None

    @property
    def cover_url(self):
        if self.cover_image:
            filename = os.path.basename(self.cover_image)
            return url_for('static', filename=f'uploads/manga_cover_images/{filename}')
        return url_for('static', filename='images/default_cover.jpg')

    def __repr__(self):
        return f"<Manga {self.title}>"

# ---------------------------------
#               CHAPTER
# ---------------------------------
class Chapter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    number = db.Column(db.Integer, nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    content_path = db.Column(db.String(255), nullable=True)
    manga_id = db.Column(db.Integer, db.ForeignKey('manga.id'), nullable=False)

    # ✅ Removed duplicate relationship (backref already created by Manga)
    comments = db.relationship('Comment', backref='chapter', lazy=True, cascade="all, delete-orphan")
    likes = db.relationship('Like', backref='chapter', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Chapter {self.title} (Manga ID: {self.manga_id})>"

# ---------------------------------
#               AUTHOR REQUEST
# ---------------------------------
class AuthorRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default="pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('author_request', uselist=False))

# ---------------------------------
#               BOOKMARK
# ---------------------------------
class Bookmark(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    manga_id = db.Column(db.Integer, db.ForeignKey('manga.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('bookmarks', lazy=True, cascade="all, delete-orphan"))

    __table_args__ = (db.UniqueConstraint('user_id', 'manga_id', name='_user_manga_uc'),)

    def __repr__(self):
        return f"<Bookmark User:{self.user_id} Manga:{self.manga_id}>"

# ---------------------------------
#               COMMENT
# ---------------------------------
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    manga_id = db.Column(db.Integer, db.ForeignKey('manga.id'), nullable=False)
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapter.id'), nullable=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=True)

    user = db.relationship('User', backref=db.backref('comments', lazy=True))
    replies = db.relationship('Comment', backref=db.backref('parent', remote_side=[id]), lazy=True)

    def __repr__(self):
        return f"<Comment {self.id} by User:{self.user_id}>"

# ---------------------------------
#               LIKE
# ---------------------------------
class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    manga_id = db.Column(db.Integer, db.ForeignKey('manga.id'), nullable=True)
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapter.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('likes', lazy=True, cascade="all, delete-orphan"))

    __table_args__ = (
        db.UniqueConstraint('user_id', 'manga_id', name='_user_manga_like_uc'),
        db.UniqueConstraint('user_id', 'chapter_id', name='_user_chapter_like_uc'),
    )

    def __repr__(self):
        if self.chapter_id:
            return f"<Like User:{self.user_id} Chapter:{self.chapter_id}>"
        return f"<Like User:{self.user_id} Manga:{self.manga_id}>"

# ---------------------------------
#               NOTIFICATION
# ---------------------------------
class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True, nullable=False)
    is_read = db.Column(db.Boolean, default=False, index=True)
    message = db.Column(db.String(255), nullable=False)
    link = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('notifications', lazy=True, cascade="all, delete-orphan"))

    def __repr__(self):
        return f"<Notification to:{self.user_id} message:{self.message[:25]}>"
