from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from . import db, login_manager

#---------------------User---------------------#
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    favorites = db.relationship("Favorite", back_populates="user", cascade="all, delete-orphan")
    comments = db.relationship("Comment", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.username}>"
    
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

#---------------------Genre---------------------#
manga_genre = db.Table(
    "manga_genre",
    db.Column("manga_id", db.Integer, db.ForeignKey("manga.id"), primary_key=True),
    db.Column("genre_id", db.Integer, db.ForeignKey("genre.id"), primary_key=True)
)

class Genre(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    mangas = db.relationship("Manga", secondary=manga_genre, back_populates="genres")

    def __repr__(self):
        return f"<Genre {self.name}>"
    
#---------------------Manga---------------------#
class Manga(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False, unique=True)
    author = db.Column(db.String(100))
    description = db.Column(db.Text)
    cover_image = db.Column(db.String(255)) #path to cover image file
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    chapters = db.relationship("Chapter", back_populates="manga", cascade="all, delete-orphan")
    genres = db.relationship("Genre", secondary=manga_genre, back_populates="mangas")
    comments = db.relationship("Comment", back_populates="manga", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Manga {self.title}>"
    
#---------------------Chapter---------------------#
class Chapter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(150))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    manga_id = db.Column(db.Integer, db.ForeignKey("manga.id"), nullable=False)
    manga = db.relationship("Manga", back_populates="chapters")

    pages = db.relationship("Page", back_populates="chapter", cascade="all, delete-orphan")
    comments = db.relationship("Comment", back_populates="chapter", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Chapter {self.number} - {self.manga.title}>"
    
#---------------------Page---------------------#
class Page(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image_path = db.Column(db.String(255), nullable=False) #local file path
    page_number = db.Column(db.Integer, nullable=False)

    chapter_id = db.Column(db.Integer, db.ForeignKey("chapter.id"), nullable=False)
    chapter = db.relationship("Chapter", back_populates="pages")

    def __repr__(self):
        return f"<Page {self.page_number} of Chapter {self.chapter_id}>"
    

#---------------------Favorite---------------------#
class Favorite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    manga_id = db.Column(db.Integer, db.ForeignKey("manga.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="favorites")
    manga = db.relationship("Manga")

    def __repr__(self):
        return f"<Favorite {self.user.username} -> {self.manga.title}>"
    

#---------------------Comment---------------------#
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    manga_id = db.Column(db.Integer, db.ForeignKey("manga.id"))
    chapter_id = db.Column(db.Integer, db.ForeignKey("chapter.id"))

    user = db.relationship("User", back_populates="comments")
    manga = db.relationship("Manga", back_populates="comments")
    chapter = db.relationship("Chapter", back_populates="comments")

    def __repr__(self):
        return f"<Comment {self.id} by {self.user.username}>"
