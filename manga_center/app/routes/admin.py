from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import Admin, User, Author, AuthorRequest
from app.forms.admin_forms import AddAuthorForm
from werkzeug.security import generate_password_hash

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(func):
    """Simple decorator to restrict routes to admins only."""
    from functools import wraps
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash("Your must be an admin to access this page.", "danger")
            return redirect(url_for('public.index'))
        return func(*args, **kwargs)
    return wrapper

@admin_bp.before_request
@login_required
def restrict_to_admins():
    #Only allows Admins
    if not current_user.admin_profile:
        flash('Access denied! Admins only.', "danger")
        return redirect(url_for('main.home'))

@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    return render_template('admin/dashboard.html')

@admin_bp.route('/users')
@login_required
@admin_required
def view_users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@admin_bp.route('/make_author/<int:user_id>')
@login_required
@admin_required
def make_author(user_id):
    user = User.query.get_or_404(user_id)

    #Check if already author
    if user.author_profile:
        flash(f"{user.username} is already an author.", "info")
        return redirect(url_for('admin.view_users'))
    
    #create author entry
    new_author = Author(user_id=user.id, pen_name=user.username)
    db.session.add(new_author)
    db.session.commit()

    flash(f"{user.username} has been promated to Author!", "success")
    return redirect(url_for('admin.view_users'))

#
#
#

@admin_bp.route('/authors')
@login_required
@admin_required
def view_authors():
    authors = Author.query.all()
    return render_template('admin/authors.html', authors=authors)

@admin_bp.route('/remove_author/<int:author_id>')
@login_required
@admin_required
def remove_author(author_id):
    author = Author.query.get_or_404(author_id)
    username = author.user.username

    db.session.delete(author)
    db.session.commit()

    flash(f"{username} is no longer an author.", "warning")
    return redirect(url_for('admin.view_authors'))

#
#
#

@admin_bp.route('/add_author', methods=["GET", "POST"])
@login_required
@admin_required
def add_author():
    form = AddAuthorForm()
    if form.validate_on_submit():
        #Check if username or Email already exists
        existing_user = User.query.filter(
            (User.username == form.username.data) | (User.email == form.email.data)
        ).first()

        if existing_user:
            flash("Username or Email already exists. Use another.", "danger")
            return redirect(url_for('admin.add_author'))
        
        # Create User account for author
        user = User(
            username = form.username.data,
            email = form.email.data,
            password = generate_password_hash("default123")  # Default password
        )

        db.session.add(user)
        db.session.commit()

        # Create author profile
        new_author = Author(
            user_id = user.id,
            pen_name = form.pen_name.data,
            bio = form.bio.data
        )

        db.session.add(new_author)
        db.session.commit()

        flash(f"Author '{form.pen_name.data}' added successfully!", "success")
        return redirect(url_for('admin.view_authors'))
    
    return render_template('admin/add_author.html', form=form)

#
#   View all Requests
#
@admin_bp.route('/author_requests')
@login_required
@admin_required
def author_requests():
    requests = AuthorRequest.query.order_by(AuthorRequest.created_at.desc()).all()
    return render_template('admin/author_requests.html', requests=requests)

#
#   Approve Request
#
@admin_bp.route('/approve_author/<int:request_id>')
@login_required
@admin_required
def approve_author(request_id):
    req = AuthorRequest.query.get_or_404(request_id)
    user = req.user

    # Create Author Profile if not exists
    if not user.author_profile:
        new_author = Author(user_id=user.id, pen_name=user.username)
        db.session.add(new_author)

    req.status = 'approved'
    db.session.commit()
    flash(f"Approved author request from {user.username}.", "success")
    return redirect(url_for('admin.author_requests'))

#
#   Reject Request
#
@admin_bp.route('/reject_author/<int:request_id>')
@login_required
@admin_required
def reject_author(request_id):
    req = AuthorRequest.query.get_or_404(request_id)
    req.status = 'rejected'
    db.session.commit()
    flash(f'Rejected author request from {req.user.username}.', 'warning')
    return redirect(url_for('admin.author_requests'))