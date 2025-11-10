from flask import Blueprint, render_template, redirect, url_for, abort, current_app, request
from flask_login import current_user
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

    is_bookmarked = False
    if current_user.is_authenticated:
        is_bookmarked = any(b.manga_id == manga.id for b in current_user.bookmarks)
    return render_template('public/view_manga.html', manga=manga, chapters=chapters, is_bookmarked=is_bookmarked)

# read specific chapter
@public_bp.route('/read/<int:chapter_id>')
def read_chapter(chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)
    manga = chapter.manga

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
