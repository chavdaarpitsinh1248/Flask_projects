from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from .. import db
from ..models import Notification

notif_bp = Blueprint('notifications', __name__)

@notif_bp.route('/')
@login_required
def notifications():
    # Get all notification for current user, lastest first
    notifs = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.timestamp.desc()).all()
    return render_template('notifications.html', notifications=notifs)


@notif_bp.route('/mark_read/<int:notif_id>')
@login_required
def mark_read(notif_id):
    notif = Notification.query.get_or_404(notif_id)
    if notif.user_id != current_user.id:
        return redirect(url_for('notifications.notifications'))
    notif.read = True
    db.session.commit()
    return redirect(url_for('notifications.notifications'))