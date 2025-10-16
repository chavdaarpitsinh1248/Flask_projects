from flask import Blueprint, render_template, url_for, redirect, flash
from flask_login import current_user, login_required
from .. import db
from ..models import StudioRequest, User, Notification
from .decorators import admin_required
from datetime import datetime, timedelta

admin_bp = Blueprint('admin', __name__)

#Admin dashboard
@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    pending_requests = StudioRequest.query.filter_by(status="pending").all()
    all_users = User.query.filter(User.role != 'admin').all()
    return render_template('admin_dashboard.html', pending_requests=pending_requests, all_users=all_users)


#Accept Studio Request
@admin_bp.route('/studio_request/accept/<int:req_id>')
@login_required
@admin_required
def accept_studio_request(req_id):
    req = StudioRequest.query.get_or_404(req_id)
    user = User.query.get(req.user_id)
    user.role = 'studio'
    req.status = 'accepted'
    req.rejected_until = None

    # Notify user
    notif = Notification(
        user_id = user.id,
        message="Your request to become a studio has been approved!"
    )
    db.session.add(notif)
    db.session.commit()

    flash(f'{user.username} is now a studio!', 'success')
    return redirect(url_for('admin.dashboard'))

#Reject Studio Request
@admin_bp.route('/studio_request/reject/<int:req_id>')
@login_required
@admin_required
def reject_studio_request(req_id):
    req = StudioRequest.query.get_or_404(req_id)
    user = User.query.get(req.user_id)
    req.status = 'rejected'
    req.rejected_until = datetime.utcnow() + timedelta(days=30)

    # Notify user
    notif = Notification(
        user_id = user.id,
        message = "Your request to become a studio has been rejected. You can try again after 30 days."
    )
    db.session.add(notif)
    db.session.commit()

    flash(f'{user.username} studio request rejected.', 'warning')
    return redirect(url_for('admin.dashboard'))

# Promote any user into to studio directly
@admin_bp.route('/promote_to_studio/<int:user_id>')
@login_required
@admin_required
def promote_to_studio(user_id):
    user = User.query.get_or_404(user_id)
    if user.is_studio():
        flash(f'{user.username} is already a studio.', 'info')
        return redirect(url_for('admin.dashboard'))
    
    user.role = 'studio'

    #create notification
    notif = Notification(
        user_id=user.id,
        message="You have been Promoted to Studio by Admin!"
    )
    db.session.add(notif)
    db.session.commit()

    flash(f'{user.username} has been promoted to studio!', 'success')
    return redirect(url_for('admin.dashboard'))