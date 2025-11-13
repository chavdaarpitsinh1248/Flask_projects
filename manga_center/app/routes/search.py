from flask import Blueprint, request, render_template, jsonify
from app.models import Manga, Author, Bookmark, Like
from sqlalchemy import func

search_bp = Blueprint('search', __name__)

@search_bp.route('/search')
def search():
    query = request.args.get('q', '').strip()
    filter_type = request.args.get('filter', 'latest')

    mangas = Manga.query.join(Author)

    # Basic text search
    if query:
        mangas = mangas.filter(
            (Manga.title.ilike(f"%{query}%")) |
            (Author.pen_name.ilike(f"%{query}%"))
        )

    # Sorting / filtering options
    if filter_type == 'latest':
        mangas = mangas.order_by(Manga.created_at.desc())
    elif filter_type == 'bookmarked':
        mangas = mangas.outerjoin(Bookmark).group_by(Manga.id).order_by(func.count(Bookmark.id).desc())
    elif filter_type == 'liked':
        mangas = mangas.outerjoin(Like).group_by(Manga.id).order_by(func.count(Like.id).desc())

    mangas = mangas.all()

    # If AJAX request, return only the rendered card list
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'html': render_template('partials/_manga_cards.html', mangas=mangas)
        })

    return render_template('search_results.html', mangas=mangas, query=query)
