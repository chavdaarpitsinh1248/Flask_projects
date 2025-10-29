
from flask import render_template, request, abort, url_for, redirect, flash
from . import manga_bp
from .forms import MangaSearchForm
from ...models import Manga, Chapter, Page
from ...extensions import db

@manga_bp.route('/')
def index():
    # simple listing (latest mangas)
    page = request.args.get('page', 1, type=int)
    mangas = Manga.query.order_by(Manga.created_at.desc()).paginate(page=page, per_page=20)
    return render_template('manga/index.html', mangas=mangas)

@manga_bp.route('/manga/<slug>/')
def detail(slug):
    manga = Manga.query.filter_by(slug=slug).first_or_404()
    chapters = manga.chapters.order_by(Chapter.number.desc()).all()
    return render_template('manga/detail.html', manga=manga, chapters=chapters)

@manga_bp.route('/manga/<slug>/chapter/<int:chapter_number>/')
def read_chapter(slug, chapter_number):
    manga = Manga.query.filter_by(slug=slug).first_or_404()
    chapter = Chapter.query.filter_by(manga_id=manga.id, number=chapter_number).first_or_404()
    pages = chapter.pages.order_by(Page.page_number).all()
    # pages is a list of Page objects, each has image_path
    return render_template('manga/read_chapter.html', manga=manga, chapter=chapter, pages=pages)

@manga_bp.route('/search')
def search():
    q = request.args.get('q', '', type=str)
    page = request.args.get('page', 1, type=int)
    if q:
        # very simple search: title ilike
        items = Manga.query.filter(Manga.title.ilike(f"%{q}%")).paginate(page=page, per_page=20)
    else:
        items = Manga.query.order_by(Manga.created_at.desc()).paginate(page=page, per_page=20)
    return render_template('manga/search.html', mangas=items, q=q)
