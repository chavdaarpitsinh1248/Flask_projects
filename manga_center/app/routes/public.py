from flask import Blueprint, render_template, redirect, url_for, abort, current_app
from app.models import Manga, Chapter
import os

public_bp = Blueprint('public', __name__, url_prefix='/')

# HomePage - list all Mangas
@public_bp.route('/')
def index():
    mangas = Manga.query.all()
    return render_template('public/index.html', mangas=mangas)

# View manga's details (cover, description, chapters)
@public_bp.route('/manga/<int:manga_id>')
def view_manga(manga_id):
    manga = Manga.query.get_or_404(manga_id)
    chapters = Chapter.query.filter_by(manga_id=manga_id).order_by(Chapter.number).all()
    return render_template('public/view_manga.html', manga=manga, chapters=chapters)

# read specific chapter
@public_bp.route('/read/<int:chapter_id>')
def read_chapter(chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)
    manga = chapter.manga

    chapter_folder = os.path.join(current_app.root_path, chapter.content_path)
    if not os.path.exists(chapter_folder):
        abort(404)
    
    image_files = sorted(
        [f for f in os.listdir(chapter_folder) if f.lower().endswith('.png', '.jpg', '.jpeg', '.gif', '.webp')]
    )

    image_urls = [
        url_for('static', filename=os.path.relpath(os.path.join(chapter.content_path, img), 'static').replace('\\', '/'))
        for img in image_files
    ]

    return render_template('public/read_chapter.html', manga=manga, chapter=chapter, image_urls=image_urls)
