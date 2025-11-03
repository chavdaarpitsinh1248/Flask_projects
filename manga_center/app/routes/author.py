from flask import Blueprint, render_template, redirect, url_for, flash, request, send_from_directory, current_app
from app.forms.manga_forms import MangaForm, ChapterForm
from app.utils.file_utils import generate_manga_cover_filename
from app.models import Manga, Chapter
from app.utils.helpers import ensure_manga_folder
from app import db
import os, zipfile
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

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
        title = form.title.data
        description = form.description.data
        cover_image_file = form.cover_image.data 

        # First create manga without cover image to get ID
        new_manga = Manga(
            title = title,
            description = description,
            author_id = current_user.author_profile.id
        )

        db.session.add(new_manga)
        db.session.commit()  # Generated Manga ID

        # Handle Cover upload if present
        if cover_image_file:
            filename = generate_manga_cover_filename(
                manga_title=title,
                manga_id=new_manga.id,
                author_id=current_user.author_profile.id,
                author_name=current_user.username,
                original_filename=cover_image_file.filename
            )
            save_path = os.path.join(current_app.config['COVER_UPLOAD_FOLDER'], filename)
            cover_image_file.save(save_path)
            new_manga.cover_image = filename
            db.session.commit()

        flash(f"Manga {title} Added Successfully!", "success")
        return redirect(url_for('author.dashboard'))
    
    return render_template('author/add_manga.html', form=form)

# View all Manga from author
@author_bp.route('/my_manga')
def my_manga():
    mangas = current_user.author_profile.mangas
    return render_template('author/my_manga.html', mangas=mangas)

#Edit existing manga
@author_bp.route('/edit_manga/<int:manga_id>', methods=['GET', 'POST'])
def edit_manga(manga_id):
    manga = Manga.query.get_or_404(manga_id)

    # Only the author who owns it can edit
    if manga.author_id != current_user.author_profile.id:
        flash('Access denied!', "danger")
        return redirect(url_for('author.my_manga'))
    
    form = MangaForm()

    if form.validate_on_submit():
        manga.title = form.title.data
        manga.description = form.description.data

        if form.cover_image.data:
            file = form.cover_image.data
            filename = generate_manga_cover_filename(
                manga_title=manga.title,
                manga_id=manga.id,
                author_id=current_user.author_profile.id,
                author_name=current_user.username,
                original_filename=file.filename
            )
            save_path = os.path.join(current_app.config['COVER_UPLOAD_FOLDER'], filename)
            file.save(save_path)
            manga.cover_image = filename
        
        db.session.commit()
        flash('Manga updated successfully!', "success")
        return redirect(url_for('author.my_manga'))
    
    #Pre-fill form with existing data
    elif request.method == 'GET':
        form.title.data = manga.title
        form.description.data = manga.description

    return render_template('author/edit_manga.html', form=form, manga=manga)

# Delete Manga
@author_bp.route('/delete_manga/<int:manga_id>', methods=['POST'])
def delete_manga(manga_id):
    manga = Manga.query.get_or_404(manga_id)

    if manga.author_id != current_user.author_profile.id:
        flash('Access denied!', "danger")
        return redirect(url_for('author.my_manga'))
    
    db.session.delete(manga)
    db.session.commit()

    flash("Manga deleted successfully!", "info")
    return redirect(url_for('author.my_manga'))


# Add Chapter
@author_bp.route('/add_chapter/<int:manga_id>', methods=['GET', 'POST'])
@login_required
def add_chapter(manga_id):
    manga = Manga.query.get_or_404(manga_id)

    # ensure only the author who owns this manga can add chapters
    if manga.author_id != current_user.author_profile.id:
        flash('You are not authorized to add chapters to this manga.', "danger")
        return redirect(url_for('author.my_manga'))
    
    form = ChapterForm()

    if form.validate_on_submit():
        # Create chapter entry
        chapter = Chapter(
            title=form.title.data,
            number=form.number.data,
            manga_id=manga.id
        )
        db.session.add(chapter)
        db.session.commit() # commit to generate chapter.id

        # Folder structure: static/uploads/manga/<manga_folder>/chapter_<id>/
        manga_folder = ensure_manga_folder(current_app, manga)
        chapter_folder = os.path.join(manga_folder, f"chapter_{chapter.id}")
        os.makedirs(chapter_folder, exist_ok=True)

        # Handle uploaded file ZIP or image
        file = form.content.data
        filename = secure_filename(file.filename)
        file_path = os.path.join(chapter_folder, filename)
        file.save(file_path)

        # If ZIP, extract it inside the folder
        if filename.lower().endswith('.zip'):
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(chapter_folder)
            os.remove(file_path) # remove zip after extracting

        # Update chapter record
        chapter.content_path = os.path.relpath(chapter_folder, current_app.root_path)
        db.session.commit()

        flash(f"Chapter '{chapter.title}' added successfully!", "success")
        return redirect(url_for('author.my_manga'))
    
    return render_template('author/add_chapter.html', form=form, manga=manga)

# Chapter List
@author_bp.route('/manga/<int:manga_id>/chapters')
@login_required
def view_chapters(manga_id):
    manga = Manga.query.get_or_404(manga_id)

    # Ensure only the manga's author can access it (for now)
    if manga.author_id != current_user.author_profile.id:
        flash("You are not authorized to view chapters of  this manga.", "danger")
        return redirect(url_for('author.my_manga'))
    
    chapters = Chapter.query.filter_by(manga_id=manga.id).order_by(Chapter.number.asc()).all()

    return render_template('author/view_chapter.html', manga=manga, chapters=chapters)