from flask import Blueprint, render_template, request, abort, flash, redirect, url_for
from ..models import Manga, Chapter, Page, Favorite, ReadingHistory, db
from sqlalchemy import or_
from flask_login import login_required, current_user
from datetime import datetime


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

#-------------Favorite-------------
@main_bp.route("/favorite/<int:manga_id>")
@login_required
def toggle_favorite(manga_id):
    manga = Manga.query.get_or_404(manga_id)
    existing = Favorite.query.filter_by(user_id=current_user.id, manga_id=manga_id).first()

    if existing:
        db.session.delete(existing)
        db.session.commit()
        flash(f"Removing {manga.title} from favorites.", "warning")
    else:
        fav = Favorite(user_id=current_user.id, manga_id=manga_id)
        db.session.add(fav)
        db.session.commit()
        flash(f"Added {manga.title} to favorites.", "success")

    return redirect(url_for('main.manga_detail', manga_id=manga_id))

@main_bp.route("/favorites")
@login_required
def user_favorites():
    favorites = Favorite.query.filter_by(user_id=current_user.id).all()
    return render_template("user_favorites.html", favorites=favorites)


#-------------- HISTORY----------------
@main_bp.route("/chapter/<int:chapter_id>/read")
@login_required
def track_read(chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)
    manga = chapter.manga

    # update or create history entry
    history = ReadingHistory.query.filter_by(user_id=current_user.id, manga_id=manga.id).first()
    if history:
        history.last_chapter_id = chapter_id
        history.last_read_at = datetime.utcnow()
    else:
        history = ReadingHistory(user_id=current_user.id, manga_id=manga.id, last_chapter_id=chapter.id)
        db.session.add(history)

    db.session.commmit()
    return redirect(url_for("main.read_chapter", chapter_id=chapter_id))

@main_bp.route("/history")
@login_required
def user_history():
    history_entries = (
        ReadingHistory.query.filter_by(user_id=current_user.id)
        .order_by(ReadingHistory.last_read_at.desc())
        .all()
    )

    return render_template("user_history.html", history_entries=history_entries)