from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user

from app.forms import SignupForm, LoginForm
from app.models import User
from app.extensions import db

auth_bp = Blueprint("auth", __name__, template_folder="../templates/auth")


# ----------------------------------------
#   Signup
# ----------------------------------------
@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for(expense.list_expenses))
    
    form = SignupForm()

    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data
        )
        user.password = form.password.data # hashed automatically

        db.session.add(user)
        db.session.commit()

        flash("Account created successfully! You may login now.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/signup.html", form=form)


# ----------------------------------------
#   Login
# ----------------------------------------
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("expenses.list_expenses"))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if user and user.verify_password(form.password.data):
            login_user(user)
            return redirect(url_for("expenses.list_expenses"))

        flash("Invalid credentials. Try again.", "danger")
    
    return render_template("auth/login.html", form=form)


# ----------------------------------------
#   Logout
# ----------------------------------------
@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))