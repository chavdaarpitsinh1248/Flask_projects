from flask import Blueprint, render_template, request, abort
from ..models import Manga, Chapter, Page
from sqlalchemy import or_


main_bp = Blueprint("main", __name__, template_folder="../templates")

@main_bp.route('/')
def index():
    page = request.args.get("page", 1, type=int)
    query = request.args.get("q", "")

    base_query = Manga.query

    if query:
        base_query = base_query.filter(
            or_(
                Manga.title.ilike(f"%{query}%"),
                Manga.author.ilike(f"%{query}%")
            )
        )

    pagination = base_query.order_by(Manga.title.asc()).paginate(page=page, per_page=10)
    mangas = pagination.items


    return render_template(
        "manga_list.html",
         mangas=mangas,
         pagination=pagination,
         query=query
         )


@main_bp.route('/manga/<int:manga_id>')
def manga_detail(manga_id):
    manga = Manga.query.get_or_404(manga_id)
    chapters = Chapter.query.filter_by(manga_id=manga.id).order_by(Chapter.number.asc()).all()
    return render_template("manga_detail.html", manga=manga, chapters=chapters)


@main_bp.route('/chapter/<int:chapter_id>')
def read_chapter(chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)
    manga = chapter.manga

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