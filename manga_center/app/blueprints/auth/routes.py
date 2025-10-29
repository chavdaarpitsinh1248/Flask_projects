
from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.urls import url_parse
from . import auth_bp
from .forms import LoginForm, RegisterForm, ProfileForm
from ...extensions import db
from ...models import User
from ...utils import save_profile_picture

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('manga.index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            if not next_page or url_parse(next_page).netloc != '':
                next_page = url_for('manga.index')
            return redirect(next_page)
        flash('Invalid email or password', 'danger')
    return render_template('auth/login.html', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('manga.index'))
    form = RegisterForm()
    if form.validate_on_submit():
        # basic uniqueness checks
        existing = User.query.filter((User.username == form.username.data) | (User.email == form.email.data.lower())).first()
        if existing:
            flash('Username or email already taken.', 'warning')
            return render_template('auth/register.html', form=form)

        user = User(username=form.username.data, email=form.email.data.lower())
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Account created. Please log in.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('manga.index'))

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """
    Update username and optionally upload a profile picture.
    Uses save_profile_picture helper to store and verify the image.
    """
    form = ProfileForm(obj=current_user)
    if form.validate_on_submit():
        # change username (with uniqueness check)
        new_username = form.username.data.strip() if form.username.data else current_user.username
        if new_username != current_user.username:
            if User.query.filter_by(username=new_username).first():
                flash('Username already taken.', 'warning')
                return render_template('auth/profile.html', form=form)
            current_user.username = new_username

        # handle profile pic upload
        pic = request.files.get('profile_pic')
        if pic and getattr(pic, 'filename', None):
            try:
                rel_path = save_profile_picture(pic, current_user.username or f"user{current_user.id}")
                current_user.profile_pic = rel_path
            except ValueError as ve:
                flash(str(ve), 'danger')
                return render_template('auth/profile.html', form=form)
            except Exception as e:
                current_app.logger.exception("Failed to save profile picture")
                flash('Failed to save profile picture.', 'danger')
                return render_template('auth/profile.html', form=form)

        db.session.commit()
        flash('Profile updated.', 'success')
        return redirect(url_for('auth.profile'))

    return render_template('auth/profile.html', form=form)
