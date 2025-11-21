from flask import render_template, redirect, url_for, flash
from flask_login import login_required
from app.extensions import db
from app.models import User
from . import admin_bp
from .utils import admin_reqired


@admin_bp.route('/')
@login_required
@admin_reqired
def dashboard():
    total_users = User.query.count()
    customers = User.query.filter_by(role='customer').count()
    suppliers = User.query.filter_by(role='supplier').count()
    staff = User.query.filter_by(role='in_staff').count()
    drivers = User.query.filter_by(role='driver').count()

    return render_template('admin/dashboard.html',
                            total_users=total_users,
                            customers=customers,
                            suppliers=suppliers,
                            staff=staff,
                            drivers=drivers)



@admin_bp.route('/users')
@login_required
@admin_reqired
def users():
    all_users = User.query.all()
    return render_template('admin/users.html', users=all_users)



@admin_bp.route('/users/<role>')
@login_required
@admin_reqired
def users_by_role(role):
    valid_roles = ['customer', 'supplier', 'in_staff', 'driver', 'admin']
    if role not in valid_roles:
        flash("Invalid role.", "danger")
        return redirect(url_for('admin.users'))

    users = User.query.filter_by(role=role).all()
    return render_template('admin/users_by_role.html', users=users, role=role)



@admin_bp.route('/delete/<int:user_id>')
@login_required
@admin_reqired
def delete_user(user_id):
    user = User.query.get_or_404(user_id)

    # Prevent admin from deleting themselves
    if user.id == user_id and user.role == "admin":
        flash("You cannot delete the main account.", "warning")
        return redirect(url_for('admin.users'))
    
    db.session.delete(user)
    db.session.commit()
    flash("User deleted successfully.", "success")
    return redirect(url_for('admin.users'))