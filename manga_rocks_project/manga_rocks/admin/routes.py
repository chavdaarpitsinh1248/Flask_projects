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
