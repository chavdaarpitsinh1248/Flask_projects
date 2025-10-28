from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, send_from_directory
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from .. import db
from ..utils import chapter_page_urls
from ..models import StudioRequest, User, Notification, Manga, Page, Chapter, History
from ..forms.studio_forms import StudioRequestForm, MangaForm, ChapterForm
from .decorators import studio_required
from datetime import datetime, timedelta
import os

studio_bp = Blueprint('studio', __name__)

@studio_bp.route('/request', methods=['POST'])
@login_required
def request_studio():
    # Check if Studio already exist
    if current_user.role=="studio":
        flash('You are already registered as a Studio.', 'info')
        return redirect(url_for('profile.my_account'))
    
    # check if a request already exist
    existing_request = StudioRequest.query.filter_by(user_id=current_user.id).order_by(StudioRequest.timestamp.desc()).first()

    # If a request exists and was rejected recently
    if existing_request and existing_request.status == "rejected":
        days_since = (datetime.utcnow() - existing_request.timestamp).days
        if days_since < 30:
            flash(f'Your pervious request was rejected. You can request again after {30 - days_since} days.', 'danger')
            return redirect(url_for('profile.my_account'))

    
    # If pending request alreay exist
    if existing_request and existing_request.status == "pending":
        flash('You already have a pending request.', 'info')
        return redirect(url_for('profile.my_account'))
    

    # Create New Studio request
    new_request = StudioRequest(user_id=current_user.id, status="pending")
    db.session.add(new_request)
    db.session.commit()


    # Notify Admin
    admin_notification = Notification(
        user_id=1,
        message=f'{current_user.username} has requested to become a studio.',
        link=url_for('admin.view_studio_requests')
    )
    db.session.add(admin_notification)
    db.session.commit()

    flash('Your Studio request has been submitted sucessfully.', 'success')
    return redirect(url_for('profile.my_account'))



# Create Manga
@studio_bp.route('/manga/create', methods=["POST", "GET"])
@login_required
@studio_required
def create_manga():
    form = MangaForm()
    if form.validate_on_submit():
        manga = Manga(
            title=form.title.data,
            description=form.description.data,
            studio_id=current_user.id,
            studio_name=current_user.username            
        )

        # Handle cover Image
        if form.cover_image.data:
            image=form.cover_image.data
            filename = secure_filename(image.filename)
            folder = os.path.join(current_app.root_path, 'static/manga_covers')
            os.makedirs(folder, exist_ok=True)
            image_path = os.path.join(folder, filename)
            image.save(image_path)
            manga.cover_image = filename

        db.session.add(manga)
        db.session.commit()
        flash('Manga Created successsfully!', 'success')
        return redirect(url_for('studio.view_manga'))
    return render_template('studio/create_manga.html', form = form)


#List Studio Mangas
@studio_bp.route('/mangas')
@login_required
@studio_required
def view_manga():
    mangas = Manga.query.filter_by(studio_id=current_user.id).all()
    return render_template('studio/mangas.html', mangas=mangas)


# Add chapter to manga
# Add chapter pages to manga
# Add chapter to manga (save pages under static/uploads/<manga_id>/<chapter_number>/)
@studio_bp.route('/manga/<int:manga_id>/add_chapter', methods=["GET", "POST"])
@login_required
@studio_required
def add_chapter(manga_id):
    manga = Manga.query.get_or_404(manga_id)
    if manga.studio_id != current_user.id:
        flash("You cannot add chapters to another studio's manga.", "danger")
        return redirect(url_for('studio.view_manga'))

    form = ChapterForm()
    if form.validate_on_submit():
        chapter = Chapter(
            number=form.number.data,
            title=form.title.data,
            manga_id=manga_id
        )
        db.session.add(chapter)
        db.session.commit()

        # Create folder inside static: static/uploads/<manga_id>/<chapter_number>/
        folder = os.path.join(current_app.static_folder, 'uploads', str(manga.id), str(chapter.number))
        os.makedirs(folder, exist_ok=True)

        # Save uploaded pages (form field name: 'pages')
        for idx, page_file in enumerate(request.files.getlist('pages'), start=1):
            if page_file and page_file.filename:
                filename = secure_filename(page_file.filename)
                filepath = os.path.join(folder, f"{idx}_{filename}")
                page_file.save(filepath)

                # Store path relative to static folder for url_for('static', filename=...)
                rel_path = os.path.join('uploads', str(manga.id), str(chapter.number), f"{idx}_{filename}")
                page = Page(
                    chapter_id=chapter.id,
                    image=rel_path.replace('\\', '/'),
                    page_number=idx
                )
                db.session.add(page)
        db.session.commit()

        # Notify Bookmarked Users
        for bookmark in manga.bookmarked_by:
            notif = Notification(
                user_id=bookmark.user_id,
                message=f'New Chapter "{chapter.title}" added to "{manga.title}"'
            )
            db.session.add(notif)
        db.session.commit()

        flash('Chapter and pages uploaded successfully!', 'success')
        return redirect(url_for('studio.view_manga'))

    return render_template('studio/add_chapter.html', form=form, manga=manga)

#
# Preview/read chapter for studio (serve pages saved in static/uploads)
@studio_bp.route('/<int:manga_id>/chapter/<int:chapter_number>')
@login_required
def read_chapter(manga_id, chapter_number):
    manga = Manga.query.get_or_404(manga_id)
    chapter = Chapter.query.filter_by(manga_id=manga_id, number=chapter_number).first_or_404()

    # Use helper to get page URLs (stored relative to static/)
    page_urls = chapter_page_urls(chapter)

    # Update history (works for studio users reading too)
    history_entry = History.query.filter_by(
        user_id=current_user.id,
        manga_id=manga_id,
        chapter_id=chapter.id
    ).first()
    if history_entry:
        history_entry.last_viewed = datetime.utcnow()
    else:
        history_entry = History(
            user_id=current_user.id,
            manga_id=manga_id,
            chapter_id=chapter.id
        )
        db.session.add(history_entry)
    db.session.commit()

    return render_template('manga/read_chapter.html', manga=manga, chapter=chapter, pages=page_urls)

# DashBoard
@studio_bp.route('/dashboard')
@login_required
@studio_required
def dashboard():
    mangas = Manga.query.filter_by(studio_id=current_user.id).all()
    return render_template('studio/dashboard.html', mangas=mangas)


# Edit chapter (update chapter info, add new pages)
@studio_bp.route('/chapter/<int:chapter_id>/edit', methods=['GET', 'POST'])
@login_required
@studio_required
def edit_chapter(chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)
    manga = chapter.manga
    if manga.studio_id != current_user.id:
        flash("You cannot edit another studio's chapter.", "danger")
        return redirect(url_for('studio.view_manga'))

    if request.method == 'POST':
        # Update chapter metadata
        # Request form values are strings — cast where needed
        num = request.form.get('number')
        if num and str(num).isdigit():
            chapter.number = int(num)
        chapter.title = request.form.get('title', chapter.title)

        # Update page order (page_order_{page.id})
        for page in chapter.pages:
            new_order = request.form.get(f'page_order_{page.id}')
            if new_order and str(new_order).isdigit():
                page.page_number = int(new_order)

        # Add new uploaded pages (field name: 'new_pages')
        new_files = request.files.getlist('new_pages')
        folder = os.path.join(current_app.static_folder, 'uploads', str(manga.id), str(chapter.number))
        os.makedirs(folder, exist_ok=True)

        next_page_number = max([p.page_number for p in chapter.pages], default=0) + 1
        for file in new_files:
            if file and file.filename:
                filename = secure_filename(file.filename)
                # Ensure unique filename in folder
                base, ext = os.path.splitext(filename)
                counter = 1
                unique_name = filename
                while os.path.exists(os.path.join(folder, unique_name)):
                    unique_name = f"{base}_{counter}{ext}"
                    counter += 1

                path = os.path.join(folder, unique_name)
                file.save(path)

                rel = os.path.join('uploads', str(manga.id), str(chapter.number), unique_name).replace('\\', '/')
                new_page = Page(chapter_id=chapter.id, image=rel, page_number=next_page_number)
                db.session.add(new_page)
                next_page_number += 1

        db.session.commit()
        flash("Chapter updated successfully!", "success")
        return redirect(url_for('studio.edit_chapter', chapter_id=chapter.id))

    return render_template('studio/edit_chapter.html', chapter=chapter)

# Delete chapter (remove page files from static/uploads and delete DB rows)
@studio_bp.route('/chapter/<int:chapter_id>/delete')
@login_required
@studio_required
def delete_chapter(chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)
    if chapter.manga.studio_id != current_user.id:
        flash("You cannot delete this chapter.", "danger")
        return redirect(url_for('studio.dashboard'))

    # Delete page files from static folder
    for page in chapter.pages:
        try:
            file_path = os.path.join(current_app.static_folder, page.image)
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            pass

    db.session.delete(chapter)
    db.session.commit()
    flash("Chapter deleted successfully!", "success")
    return redirect(url_for('studio.dashboard'))

# Manage pages (reorder + add pages) - ensure pages saved under static/uploads/...
@studio_bp.route('/chapter/<int:chapter_id>/manage_pages', methods=['POST'])
@login_required
@studio_required
def manage_pages(chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)
    if chapter.manga.studio_id != current_user.id:
        flash("You cannot manage pages for this chapter.", "danger")
        return redirect(url_for('studio.view_manga'))

    # Reorder existing pages
    for page in chapter.pages:
        new_order = request.form.get(f'page_order_{page.id}')
        if new_order and new_order.isdigit():
            page.page_number = int(new_order)

    # Add new pages if present
    new_files = request.files.getlist('new_pages')
    if new_files:
        folder = os.path.join(current_app.static_folder, 'uploads', str(chapter.manga_id), str(chapter.number))
        os.makedirs(folder, exist_ok=True)

        existing_numbers = [p.page_number for p in chapter.pages]
        next_page_number = max(existing_numbers, default=0) + 1

        for f in new_files:
            if not f or not f.filename:
                continue

            filename = secure_filename(f.filename)
            base, ext = os.path.splitext(filename)
            counter = 1
            unique_name = filename
            while os.path.exists(os.path.join(folder, unique_name)):
                unique_name = f"{base}_{counter}{ext}"
                counter += 1

            path = os.path.join(folder, unique_name)
            f.save(path)

            rel_path = os.path.join('uploads', str(chapter.manga_id), str(chapter.number), unique_name).replace('\\', '/')
            new_page = Page(
                chapter_id=chapter.id,
                image=rel_path,
                page_number=next_page_number
            )
            db.session.add(new_page)
            next_page_number += 1

    db.session.commit()
    flash("Pages updated successfully!", "success")
    return redirect(url_for('studio.edit_chapter', chapter_id=chapter.id))

#
# Delete single page (POST request) - remove file from static/uploads and model row
@studio_bp.route('/page/delete/<int:page_id>', methods=['POST'])
@login_required
@studio_required
def delete_page(page_id):
    page = Page.query.get_or_404(page_id)
    if page.chapter.manga.studio_id != current_user.id:
        flash("You cannot delete pages from another studio's manga.", "danger")
        return redirect(url_for('studio.view_manga'))

    # Remove file from static folder
    file_path = os.path.join(current_app.static_folder, page.image)
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception:
        pass

    db.session.delete(page)
    db.session.commit()
    flash("Page deleted.", "success")
    # For JS fetch style delete returning '', 204 is fine. But redirect also works.
    return ('', 204)
