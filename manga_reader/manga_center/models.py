from . import db
from flask_login import UserMixin
from datetime import datetime, timedelta

ROLE_USER = 'user'
ROLE_STUDIO = 'studio'
ROLE_ADMIN = 'admin'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), default=ROLE_USER)  # user, studio, admin
    image_file = db.Column(db.String(100), default='default.jpg') #profile pic

    notifications = db.relationship('Notification', backref='user', lazy=True)
    comments = db.relationship('Comment', backref='user', lazy=True)
    mangas_created = db.relationship('Manga', backref='studio', lazy=True)
    reports_sent = db.relationship('Report', backref='reporter', lazy=True, foreign_keys='Report.reporter_id')
    reports_received = db.relationship('Report', backref='reported_user', lazy=True, foreign_keys='Report.reported_user_id')
    studio_requests = db.relationship('StudioRequest', backref='requester', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role == ROLE_ADMIN

    def is_studio(self):
        return self.role == ROLE_STUDIO

# Manga hierarchy
class Manga(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    image = db.Column(db.String(200))
    studio_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    studio_name = db.Column(db.String(150), nullable=True)  # denormalized for easier display

    chapters = db.relationship('Chapter', backref='manga', lazy=True)
    comments = db.relationship('Comment', backref='manga', lazy=True)

class Chapter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.Integer, nullable=False)  # Add chapter number
    title = db.Column(db.String(200), nullable=False)
    manga_id = db.Column(db.Integer, db.ForeignKey('manga.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    pages = db.relationship('Page', backref='chapter', lazy=True)

class Page(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapter.id'), nullable=False)
    image = db.Column(db.String(200), nullable=False)
    page_number = db.Column(db.Integer, nullable=False)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    manga_id = db.Column(db.Integer, db.ForeignKey('manga.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    children = db.relationship('Comment', backref=db.backref('parent', remote_side=[id]), lazy=True)
    reports = db.relationship('Report', backref='comment', lazy=True)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.String(300))
    read = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# Studio request table
class StudioRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    requested_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), default='pending')  # pending, accepted, rejected
    rejected_until = db.Column(db.DateTime, nullable=True)  # if rejected, cannot request until this time

# Reports
class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reporter_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    reported_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    comment_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


# History
class History(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    manga_id = db.Column(db.Integer, db.ForeignKey('manga.id'), nullable=False)
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapter.id'), nullable=False)
    last_viewed = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='history_entries', lazy=True)
    manga = db.relationship('Manga', backref='history_entries', lazy=True)
    chapter = db.relationship('Chapter', backref='history_entries', lazy=True)


# Bookmark
class Bookmark(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    manga_id = db.Column(db.Integer, db.ForeignKey('manga.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='bookmarks', lazy=True)
    manga = db.relationship('Manga', backref='bookmarked_by', lazy=True)