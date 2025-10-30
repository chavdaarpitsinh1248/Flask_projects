from flask import Blueprint, render_template, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from app.forms.login_form import LoginForm
from app.forms.register_form import RegisterForm
from app.models import User
from app import db

users_bp = Blueprint('users', __name__)

@users_bp.route('/login')
def login():
    form = LoginForm()
    if form.validate_on_submit():
        flash(f"Logged in as {form.username.data}", "success")
        return redirect(url_for('main.home'))
    return render_template('login.html', form=form)

@users_bp.route('/register')
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
            hashed_password = generate_password_hash(form.passowrd.data)
            new_user = User(
                username = form.username.data,
                email = form.email.data,
                passowrd = hashed_password
            )
            db.session.add(new_user)
            db.session.commit()

        flash(f"Account created for {form.username.data}! You can now log in.", "success")
        return redirect(url_for("users.login"))
    return render_template('register.html', form=form)