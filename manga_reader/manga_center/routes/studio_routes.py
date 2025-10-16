from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from .. import db
from ..models import StudioRequest, User, Notification, Manga, Page, Chapter
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
            number = form.number.data,
            title = form.title.data,
            manga_id = manga_id
        )
        db.session.add(chapter)
        db.session.commit()
        flash('Chapter added', 'success')


        # Notify Bookmarked Users
        for bookmark in manga.bookmarked_by:
            notif = Notification(
                user_id = bookmark.user_id,
                message = f'New Chapter "{chapter.title}" added to "{manga.title}" '
            )
            db.session.add(notif)
        db.session.commit()

        return redirect(url_for('studio.view_mangas'))
    
    return render_template('studio/add_chapter.html', form=form , manga=manga)
