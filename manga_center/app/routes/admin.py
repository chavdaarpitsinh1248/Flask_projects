from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import Admin

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.before_request
@login_required
def restrict_to_admins():
    #Only allows Admins
    if not current_user.admin_profile:
        flash('Access denied! Admins only.', "danger")
        return redirect(url_for('main.home'))

@admin_bp.route('/')
def dashboard():
    return render_template('admin/dashboard.html')