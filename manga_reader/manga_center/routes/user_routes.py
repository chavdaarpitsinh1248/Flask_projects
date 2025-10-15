from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime
from .. import db
from ..models import StudioRequest, Notification, User

user_bp = Blueprint('user', __name__)

@user_bp.route('/request_studio')
@login_required
def request_studio():
    #prevent admins/studio from requesting
    if current_user.is_studio() or current_user.is_admin():
        flash('You already have studio/admin prevoledges.', 'info')
        return redirect(url_for('main.index'))
    
    # check if pending request already exist
    existing = StudioRequest.query.filter_by(user_id=current_user.id, status='pending').first()
    if existing:
        flash("you already have a pending request.", "warning")
        return redirect(url_for('main.index'))
    
    # check 30 days rejection cooldown
    last_rejected = StudioRequest.query.filter_by(user_id=current_user.id, status='rejected').order_by(StudioRequest.requested_at.desc()).first()
    if last_rejected and last_rejected.rejected_until and datetime.utcnow() < last_rejected.rejected_until :
        remaining_days = (last_rejected.rejected_until - datetime.utcnow()).days
        flash(f"Your last request was rejected. You can requery again in { remaining_days } days.", "danger")
        return redirect(url_for('main.index'))
    
    #create studio request
    studio_req = StudioRequest(user_id=current_user.id, status="pending")
    db.session.add(studio_req)
    db.session.commit()

    #Notify all admins
    admins = User.query.filter_by(role='admin').all()
    for admin in admins:
        notif = Notification(
            user_id=admin.id,
            message = f"{current_user.username} has request to become a studio."
        )
        db.session.add(notif)

    db.session.commit()

    flash("Your request to become a studio has been sent to admins", "success")
    return redirect(url_for('main.Index'))
