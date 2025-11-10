from flask import (
    Blueprint, render_template, redirect, url_for, flash,
    request, current_app
)
from flask_login import (
    login_user, logout_user, current_user, login_required
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from app import db
from app.models import User, AuthorRequest, Bookmark, Manga
from app.forms.login_form import LoginForm
from app.forms.register_form import RegisterForm
from app.forms.user_form import ProfileForm, AuthorRequestForm
import os

users_bp = Blueprint('users', __name__)

# ------------------------
# LOGIN
# ------------------------
@users_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('public.index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter(
            (User.username == form.username.data) | (User.email == form.username.data)
        ).first()

        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            flash(f"Welcome back, {user.username}!", "success")

            next_page = request.args.get('next')
            return redirect(next_page or url_for('public.index'))
        flash("Invalid username/email or password", "danger")

    return render_template('login.html', form=form)


# ------------------------
# REGISTER
# ------------------------
@users_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        # Check if username or email already exists
        existing_user = User.query.filter(
            (User.username == form.username.data) | (User.email == form.email.data)
        ).first()

        if existing_user:
            flash('Username or Email already exists!', "danger")
        else:
            hashed_password = generate_password_hash(form.password.data)
            new_user = User(
                username=form.username.data,
                email=form.email.data,
                password=hashed_password
            )
            db.session.add(new_user)
            db.session.commit()

            flash(f"Account created for {form.username.data}! You can now log in.", "success")
            return redirect(url_for("users.login"))
    return render_template('register.html', form=form)


# ------------------------
# LOGOUT
# ------------------------
@users_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', "info")
    return redirect(url_for('public.index'))


# ------------------------
# PROFILE VIEW
# ------------------------
@users_bp.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)


# ------------------------
# EDIT PROFILE
# ------------------------
@users_bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = ProfileForm(obj=current_user)

    if form.validate_on_submit():
        # Update username
        current_user.username = form.username.data

        # Update password (only if entered)
        if form.password.data:
            current_user.password = generate_password_hash(form.password.data)

        # Update profile picture
        if form.profile_pic.data:
            pic_file = form.profile_pic.data
            filename = secure_filename(f"user_{current_user.id}_{pic_file.filename}")

            folder = current_app.config.get('PROFILE_PIC_FOLDER') or \
                     os.path.join(current_app.root_path, 'static', 'uploads', 'profile_pics')
            os.makedirs(folder, exist_ok=True)

            file_path = os.path.join(folder, filename)
            pic_file.save(file_path)

            # Save relative path (for easy template usage)
            current_user.profile_pic = os.path.relpath(file_path, current_app.root_path)

        db.session.commit()
        flash('Your profile has been updated!', 'success')
        return redirect(url_for('users.profile'))

    return render_template('edit_profile.html', form=form)

# ------------------------------------
#               REQUEST AUTHOR
# ------------------------------------

@users_bp.route('/request_author', methods=['GET', 'POST'])
@login_required
def request_author():
    if current_user.author_profile:
        flash('You are already an author!', 'info')
        return redirect(url_for('users.profile'))
    
    # If a request already exists
    existing_request = AuthorRequest.query.filter_by(user_id=current_user.id).first()
    if existing_request and existing_request.status == 'pending':
        flash('You already have a pending request.', 'info')
        return redirect(url_for('users.profile'))
    
    form = AuthorRequestForm()
    if form.validate_on_submit():
        new_request = AuthorRequest(
            user_id = current_user.id,
            message = form.message.data.strip(),
            status = 'pending'
        )
        db.session.add(new_request)
        db.session.commit()
        flash('Your author request has been submitted Successfully!', 'success')
        return redirect(url_for('users.profile'))
    return render_template('users/request_author.html', form=form)

# ---------------------------------
#               BOOKMARK
# ---------------------------------
@users_bp.route('/bookmark/<int:manga_id>', methods=['POST'])
@login_required
def toggle_bookmark(manga_id):
    manga = Manga.query.get_or_404(manga_id)
    bookmark = Bookmark.query.filter_by(user_id=current_user.id, manga_id=manga_id).first()

    action = None
    if bookmark:
        db.session.delete(bookmark)
        db.session.commit()
        action="Removed"
        
    else:
        new_bookmark = Bookmark(user_id=current_user.id, manga_id=manga_id)
        db.session.add(new_bookmark)
        db.session.commit()
        action="added"
    
    # Return JSON if AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return {"status": "success", "action": action, "manga_id": manga_id}
    # Fallback for normal form submissions
    flash(f"Manga Bookmark {action}", "info" )
    return redirect(request.referrer or url_for('public.index'))


# --------------------------------------
#               MY LIBRARY PAGE
# --------------------------------------
@users_bp.route('/my_library')
@login_required
def my_library():
    bookmarks = Bookmark.query.filter_by(user_id=current_user.id).order_by(Bookmark.created_at.desc()).all()
    return render_template('users/my_library.html', bookmarks=bookmarks)