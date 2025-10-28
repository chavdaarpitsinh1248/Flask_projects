# manga_center/routes/search_routes.py

from flask import Blueprint, render_template, request
from ..models import Manga

search_bp = Blueprint("search", __name__)

@search_bp.route("/search")
def search():
    query = request.args.get("q", "").strip()
    mangas = []

    if query:
        # Perform case-insensitive partial search
        search_pattern = f"%{query}%"
        mangas = Manga.query.filter(
            (Manga.title.ilike(search_pattern)) |
            (Manga.description.ilike(search_pattern)) |
            (Manga.studio_name.ilike(search_pattern))
        ).all()

    return render_template("search/results.html", mangas=mangas, query=query)
