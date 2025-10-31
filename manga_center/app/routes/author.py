from flask import flash, Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

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