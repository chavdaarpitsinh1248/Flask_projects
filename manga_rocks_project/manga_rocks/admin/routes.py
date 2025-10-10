import os
from flask import Blueprint, render_template, request, redirect, url_for, current_app, flash
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from .. import db
from ..models import Manga, Genre, Chapter, Page
from .forms import AddMangaForm, AddChapterForm, UploadPagesForm


admin_bp = Blueprint("admin", __name__, template_folder="../templates")


#Restrict access to Admin users only
def admin_required(func):
    from functools import wraps
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin :
            flash("Admin access required", "danger")
            return redirect(url_for("auth.login"))
        return func(*args, **kwargs)
    return wrapper

@admin_bp.route("/")
@login_required
@admin_required
def admin_index():
    mangas = Manga.query.all()
    return render_template("admin_index.html", mangas=mangas)

@admin_bp.route("/add_manga", methods=["GET", "POST"])
@login_required
@admin_required
def add_manga():
    form = AddMangaForm()
    form.genres.choices = [(g.id, g.name) for g in Genre.query.all()]

    if form.validate_on_submit():
        filename = None
        if form.cover_image.data:
            filename = secure_filename(form.cover_image.data.filename)
            upload_path = os.path.join(current_app.conifg["UPLOAD_FOLDER"], filename)
            form.cover_image.data.save(upload_path)

        manga = Manga(
            title = form.title.data,
            author = form.author.data,
            description = form.description.data,
            cover_image= f"uploads.{filename}" if filename else None,
        )
        
        for genre_id in form.genres.data:
            genre = Genre.query.get(genre_id)
            if genre:
                manga.genres.append(genre)

        
        db.session.add(manga)
        db.session.commit()
        flash("Manga Added Successfully!", "success")
        return redirect(url_for("admin.admin_index"))
    
    return render_template("admin_add_manga.html", form=form)
