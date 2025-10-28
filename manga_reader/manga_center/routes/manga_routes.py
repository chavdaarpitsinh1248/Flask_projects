from flask import Blueprint, render_template, abort, url_for
from flask_login import login_required, current_user
from ..models import Manga, Chapter, Page, History
from .. import db
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
    # load manga + chapter (404 if not found)
    manga = Manga.query.get_or_404(manga_id)
    chapter = Chapter.query.get_or_404(chapter_id)

    # fetch pages ordered by page_number
    pages_q = Page.query.filter_by(chapter_id=chapter.id).order_by(Page.page_number).all()

    # convert each Page.image into a URL string for templates
    page_urls = []
    for p in pages_q:
        if not p.image:
            continue
        # if it's already an absolute URL, keep it; otherwise treat as static-relative path
        if p.image.startswith('http://') or p.image.startswith('https://'):
            page_urls.append(p.image)
        else:
            # p.image is stored relative to static/, e.g. "uploads/1/2/1.jpg"
            page_urls.append(url_for('static', filename=p.image))

    # update history
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

    # pass page URL strings to template
    return render_template('manga/read_chapter.html', manga=manga, chapter=chapter, pages=page_urls)