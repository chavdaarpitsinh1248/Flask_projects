from flask import Blueprint, render_template, redirect, url_for, flash, request
from app.forms.manga_forms import MangaForm
from app.models import Manga
from app import db
import os
from flask_login import login_required, current_user

author_bp = Blueprint('author', __name__, url_prefix='/author')

# Restrict access to authors only
@author_bp.before_request
@login_required
def restrict_to_authors():
    if not current_user.author_profile:
        flash("Access denied! Authors Only!", "danger")
        return redirect(url_for('main.home'))
    
# Author dashboard route
@author_bp.route('/')
def dashboard():
    return render_template('author/dashboard.html')

# Add Manga
@author_bp.route('/add_manga', methods=['GET', 'POST'])
def add_manga():
    form = MangaForm()

    if form.validate_on_submit():
        title = form.title.data,
        description = form.description.data,
        cover_image = None  # We'll add upload support later

        new_manga = Manga(
            title = title,
            description = description,
            cover_image = cover_image,
            author_id = current_user.author_profile.id
        )

        db.session.add(new_manga)
        db.session.commit()

        flash(f"Manga {title} Added Successfully!", "success")
        return redirect(url_for('author.dashboard'))
    
    return render_template('author/add_manga.html', form=form)
