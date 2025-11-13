from flask import Blueprint, render_template, redirect, url_for, abort, current_app, request
from flask_login import current_user
from app.models import Manga, Chapter, Bookmark, Comment
import os
from app import db
from app.forms.comment_form import CommentForm
from sqlalchemy import func, desc


public_bp = Blueprint('public', __name__, url_prefix='/')

# HomePage - list all Mangas
@public_bp.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    per_page = 20  # 4 per row × 5 rows

    # Sort mangas by latest uploaded chapter
    mangas_query = (
        db.session.query(Manga)
        .outerjoin(Chapter)
        .group_by(Manga.id)
        .order_by(func.max(Chapter.upload_date).desc().nullslast())
    )

    pagination = mangas_query.paginate(page=page, per_page=per_page, error_out=False)
    mangas = pagination.items

    return render_template('public/index.html', mangas=mangas, pagination=pagination)


# View manga's details (cover, description, chapters)
@public_bp.route('/manga/<int:manga_id>')
def view_manga(manga_id):
    manga = Manga.query.get_or_404(manga_id)
    chapters = Chapter.query.filter_by(manga_id=manga_id).order_by(Chapter.number).all()

    is_bookmarked = False
    if current_user.is_authenticated:
        bookmark = Bookmark.query.filter_by(user_id=current_user.id, manga_id=manga_id).first()
        is_bookmarked = bookmark is not None
    return render_template('public/view_manga.html', manga=manga, chapters=chapters, is_bookmarked=is_bookmarked)

# read specific chapter
@public_bp.route('/read/<int:chapter_id>')
def read_chapter(chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)
    manga = chapter.manga
    
    # top-level comments (no parent) ordered desc
    top_comments = Comment.query.filter_by(
        chapter_id=chapter_id, parent_id=None
    ).order_by(Comment.created_at.desc()).all()

    # For each top-level comment, fetch its replies ordered asc and attach to the object
    for c in top_comments:
        # Query replies for this comment, ordered by created_at ascending
        replies = Comment.query.filter_by(parent_id=c.id).order_by(Comment.created_at.asc()).all()
        # Attach prepared list to attribute used in template
        c.replies_sorted = replies

        # If you want deeper nesting (replies to replies), you can repeat recursively
        # or build a recursive helper function to attach replies_sorted for each reply.


    form = CommentForm()

    # Get all chapters of this manga in order
    chapters = Chapter.query.filter_by(manga_id=manga.id).order_by(Chapter.number).all()

    # Find next and previous chapters
    next_chapter = None
    prev_chapter = None
    for idx, ch in enumerate(chapters):
        if ch.id == chapter.id:
            if idx > 0:
                prev_chapter = chapters[idx - 1]
            if idx < len(chapters) - 1:
                next_chapter = chapters[idx + 1]
            break

    # Build image URLs
    chapter_folder = os.path.join(current_app.root_path, chapter.content_path)
    if not os.path.exists(chapter_folder):
        abort(404)

    image_files = sorted(
        [f for f in os.listdir(chapter_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp'))]
    )
    image_urls = [
        url_for('static', filename=os.path.relpath(os.path.join(chapter.content_path, img), 'static').replace('\\', '/'))
        for img in image_files
    ]

    return render_template(
        'public/read_chapter.html',
        manga=manga,
        chapter=chapter,
        comments=top_comments,
        form=form,
        image_urls=image_urls,
        next_chapter=next_chapter,
        prev_chapter=prev_chapter
    )

@public_bp.route('/author/<int:author_id>')
def view_author(author_id):
    from app.models import Author  # local import to avoid circular imports

    author = Author.query.get_or_404(author_id)
    mangas = author.mangas  # all manga by this author

    return render_template('public/view_author.html', author=author, mangas=mangas)

@public_bp.route('/manga')
def all_manga():
    from app.models import Manga, Author

    search_query = request.args.get('search', '').strip()
    author_filter = request.args.get('author', '').strip()
    page = request.args.get('page', 1, type=int)

    mangas_query = Manga.query

    # --- Apply filters ---
    if search_query:
        mangas_query = mangas_query.filter(Manga.title.ilike(f'%{search_query}%'))

    if author_filter:
        mangas_query = mangas_query.join(Author).filter(
            (Author.pen_name.ilike(f'%{author_filter}%')) |
            (Author.user.has(username=author_filter))
        )

    mangas_query = mangas_query.order_by(Manga.created_at.desc())

    # --- Pagination ---
    per_page = 6  # number of manga per page
    pagination = mangas_query.paginate(page=page, per_page=per_page, error_out=False)
    mangas = pagination.items

    authors = Author.query.all()

    return render_template(
        'public/all_manga.html',
        mangas=mangas,
        authors=authors,
        search_query=search_query,
        author_filter=author_filter,
        pagination=pagination
    )

@public_bp.route('/search')
def search():
    q = request.args.get('q', '')
    mangas = Manga.query.filter(Manga.title.ilike(f"%{q}%")).all() if q else []
    return render_template('public/search_results.html', mangas=mangas, query=q)

@public_bp.route('/genre/<genre_name>')
def genre(genre_name):
    page = request.args.get('page', 1, type=int)
    mangas = Manga.query.filter(Manga.genre.ilike(f'%{genre_name}%')) \
                        .order_by(Manga.id.desc()) \
                        .paginate(page=page, per_page=20)
    return render_template('public/genre.html',
                           genre=genre_name.capitalize(),
                           mangas=mangas.items,
                           pagination=mangas)

