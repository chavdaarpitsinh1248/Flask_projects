from flask import Blueprint, render_template, url_for, abort
from ..models import Manga, Chapter
from .. import db
import os

main_bp = Blueprint("main", __name__)

@main_bp.route("/")
def index():
    mangas = Manga.query.order_by(Manga.title).all()
    return render_template("index.html", mangas=mangas)

@main_bp.route("/manga/<slug>/")
def manga_page(slug):
    manga = Manga.query.filter_by(slug=slug).first_or_404()
    chapters = sorted(manga.chapters, key=lambda c: c.number)
    return render_template("manga.html", manga=manga, chapters=chapters)

@main_bp.route("/manga/<slug>/chapter/<int:chapter_id>/")
def read_chapter(slug, chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)
    if chapter.manga.slug != slug:
        abort(404)
    # list files in static/uploads/<folder>
    static_folder = os.path.join("app", "static")
    chapter_dir = os.path.join(static_folder, chapter.folder)
    if not os.path.isdir(chapter_dir):
        abort(404)
    images = sorted([f for f in os.listdir(chapter_dir) if f.lower().endswith((".jpg",".jpeg",".png"))])
    image_urls = [url_for("static", filename=f"uploads/{chapter.folder}/{img}") for img in images]
    return render_template("read.html", images=image_urls, chapter=chapter)
