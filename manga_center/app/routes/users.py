from flask import Blueprint, render_template, redirect, url_for, flash, request
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, current_user, login_required
from app.forms.login_form import LoginForm
from app.forms.register_form import RegisterForm
from app.models import User
from app import db

users_bp = Blueprint('users', __name__)

@users_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter(
            (User.username == form.username.data) | (User.email == form.username.data)
        ).first()

        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            flash(f"Welcome Back, {user.username}!", "success")

            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.home'))
        else:
            flash("Invalid username/email or password", "danger")

    return render_template('login.html', form=form)

@users_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        # Check if username or email already exist
        existing_user = User.query.filter(
            (User.username == form.username.data) | (User.email == form.email.data)
        ).first()

        if existing_user:
            flash('Username or Email already Exist!', "danger")
        else:
            hashed_password = generate_password_hash(form.password.data)
            new_user = User(
                username = form.username.data,
                email = form.email.data,
                password = hashed_password
            )
            db.session.add(new_user)
            db.session.commit()

            flash(f"Account created for {form.username.data}! You can now log in.", "success")
            return redirect(url_for("users.login"))
    return render_template('register.html', form=form)

@users_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', "info")
    return redirect(url_for('main.home'))