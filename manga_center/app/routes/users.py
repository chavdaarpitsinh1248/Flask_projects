from flask import Blueprint, render_template, redirect, url_for, flash
from app.forms.login_form import LoginForm
from app.forms.register_form import RegisterForm

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
        flash(f"Account created for {form.username.data}!", "success")
        return redirect(url_for("users.login"))
    return render_template('register.html')