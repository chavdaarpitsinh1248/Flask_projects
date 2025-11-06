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
        #Find the last chapter number of this manga 
        last_chapter = Chapter.query.filter_by(manga_id=manga.id).order_by(Chapter.number.desc()).first()
        next_number = 1 if not last_chapter else last_chapter.number + 1

        chapter = Chapter(
            title=form.title.data,
            number=next_number,
            manga_id=manga.id
        )
        db.session.add(chapter)
        db.session.commit() # commit to generate chapter.id

        # Folder structure: static/uploads/manga/<manga_folder>/chapter_<id>/
        manga_folder = ensure_manga_folder(current_app, manga)
        chapter_folder = os.path.join(manga_folder, f"chapter_{chapter.number}")
        os.makedirs(chapter_folder, exist_ok=True)

        # Handle multiple image uploads
        uploaded_files = request.files.getlist("content")
        image_count = 0
        for file in uploaded_files:
            if file and file.filename:
                filename = secure_filename(file.filename)
                file_path = os.path.join(chapter_folder, filename)
                file.save(file_path)
                image_count += 1

        if image_count == 0:
            flash("No images uploaded. Please select atleast one.", "warning")
            db.session.delete(chapter)
            db.session.commit()
            return redirect(url_for('author.add_chapter', manga_id=manga.id))
        

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

    return render_template('author/view_chapters.html', manga=manga, chapters=chapters)

# Read Chapter
@author_bp.route('/chapter/<chapter_id>')
@login_required
def read_chapter(chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)
    manga = chapter.manga

    # Chapter permission (author view for now)
    if manga.author_id != current_user.author_profile.id:
        flash("You are not authorized to read this chapter.", "danger")
        return redirect(url_for('author.my_manga'))
    
    # Build full path to the chapter folder
    chapter_folder = os.path.join(current_app.root_path, chapter.content_path)

    # Collect all image files from that folder
    if not os.path.exists(chapter_folder):
        flash("Chapter folder not found.", "danger")
        return redirect(url_for('author.view_chapters', manga_id=manga.id))
    
    image_files = sorted(
        [f for f in os.listdir(chapter_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp'))]
    )

    image_urls = [
        url_for('static', filename=os.path.relpath(os.path.join(chapter.content_path, img), 'static').replace('\\','/'))
        for img in image_files
    ]


    return render_template('author/read_chapter.html', manga=manga, chapter=chapter, image_urls=image_urls)

# Edit Chapter
@author_bp.route('/edit_chapter/<int:chapter_id>', methods=['GET', 'POST'])
@login_required
def edit_chapter(chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)
    manga = chapter.manga

    # Only the author of this manga can edit
    if manga.author_id != current_user.author_profile.id:
        flash("You are not authorized to edit this chapter.", "danger")
        return redirect(url_for('author.view_chapters', manga_id=manga.id))
    
    form = ChapterForm(obj=chapter)

    # ---- Collect existing images ----
    chapter_folder = os.path.join(current_app.root_path, chapter.content_path)
    image_files = []
    if os.path.exists(chapter_folder):
        for img in os.listdir(chapter_folder):
            if img.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                rel_path = os.path.relpath(os.path.join(chapter.content_path, img), 'static').replace('\\', '/')
                image_files.append(url_for('static', filename=rel_path))

    # ---- Handle Form Submission ----
    if form.validate_on_submit():
        chapter.title = form.title.data
        chapter.number = form.number.data

        # Update images if new ones are uploaded
        if form.content.data:
            # Ensure folder exists
            os.makedirs(chapter_folder, exist_ok=True)

            # Remove old images first
            for old_file in os.listdir(chapter_folder):
                os.remove(os.path.join(chapter_folder, old_file))

            # Save New Images
            for file in form.content.data:
                if file and file.filename:
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(chapter_folder, filename))

        db.session.commit()
        flash('Chapter updated successfully!', "success")
        return redirect(url_for('author.view_chapters', manga_id=manga.id))
    
    return render_template(
        'author/edit_chapter.html',
        form=form,
        manga=manga,
        chapter=chapter,
        image_files=image_files
    )


# Delete Chapter
@author_bp.route('/delete_chapter/<int:chapter_id>', methods=['POST'])
@login_required
def delete_chapter(chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)
    manga = chapter.manga

    if manga.author_id != current_user.author_profile.id:
        flash("You are not authorized to delete this chapter.", "danger")
        return redirect(url_for('author.view_chapters', manga_id=manga.id))
    
    # Remove chapter folder and files
    chapter_folder = os.path.join(current_app.root_path, chapter.content_path)
    if os.path.exists(chapter_folder):
        import shutil
        shutil.rmtree(chapter_folder)

    db.session.delete(chapter)
    db.session.commit()

    flash('Chapter deleted successfully!', "success")
    return redirect(url_for('author.view_chapters', manga_id=manga.id))