from flask import Blueprint, render_template, abort, url_for
from flask_login import login_required, current_user
from ..models import Manga, Chapter, Page, History
from .. import db
from ..utils import chapter_page_urls
from datetime import datetime

manga_bp = Blueprint('manga', __name__)

# Manga List Page
@manga_bp.route('/')
def index():
    mangas = Manga.query.all()
    return render_template('manga/manga_list.html', mangas=mangas)


# View Chapters of Manga
@manga_bp.route('/<int:manga_id>')
def view_manga(manga_id):
    manga = Manga.query.get_or_404(manga_id)
    chapters = Chapter.query.filter_by(manga_id=manga_id).order_by(Chapter.number).all()
    return render_template('manga/manga_detail.html', manga=manga, chapters=chapters)


# Read Chapter pages
@manga_bp.route('/<int:manga_id>/chapter/<int:chapter_id>')
@login_required
def read_chapter(manga_id, chapter_id):
    manga = Manga.query.get_or_404(manga_id)
    chapter = Chapter.query.get_or_404(chapter_id)

    # Use helper to get page URLs
    page_urls = chapter_page_urls(chapter)

    # Update history (same as before)
    history_entry = History.query.filter_by(
        user_id=current_user.id,
        manga_id=manga_id,
        chapter_id=chapter.id
    ).first()
    if history_entry:
        history_entry.last_viewed = datetime.utcnow()
    else:
        history_entry = History(
            user_id=current_user.id,
            manga_id=manga_id,
            chapter_id=chapter.id
        )
        db.session.add(history_entry)
    db.session.commit()

    return render_template('manga/read_chapter.html', manga=manga, chapter=chapter, pages=page_urls)