from flask import Blueprint, render_template, request, abort
from ..models import Manga, Chapter, Page

main_bp = Blueprint("main", __name__, template_folder="../templates")

@main_bp.route('/')
def index():
    mangas = Manga.query.order_by(Manga.title.asc()).all()
    return render_template("manga_list.html", mangas=mangas)


@main_bp.route('/manga/<int:manga_id>')
def manga_detail(manga_id):
    manga = Manga.query.get_or_404(manga_id)
    chapters = Chapter.query.filter_by(manga_id=manga.id).order_by(Chapter.number.asc()).all()
    return render_template("manga_detail.html", manga=manga, chapters=chapters)


@main_bp.route('/manga/<int:chapter_id')
def read_chapter(chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)
    manga = Chapter.manga

    pages = Page.query.filter_by(chapter_id=chapter.id).order_by(Page.page_number.asc()).all()
    next_chapter = (
        Chapter.query.filter(Chapter.manga_id == manga.id, Chapter.number > chapter.number)
        .order_by(Chapter.number.asc())
        .first()
    )
    prev_chapter = (
        Chapter.query.filter(Chapter.manga_id == manga.id, Chapter.number < chapter.number)
        .order_by(Chapter.number.desc())
        .first()
    )

    return render_template(
        "chapter_reader.html",
        manga=manga,
        chapter=chapter,
        pages=pages,
        next_chapter=next_chapter,
        prev_chapter=prev_chapter,
    )