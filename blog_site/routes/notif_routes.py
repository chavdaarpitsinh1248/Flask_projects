from flask import Blueprint, render_template, redirect, url_for, abort
from flask_login import login_required, current_user
from models import Notification
from extensions import db

notif_bp = Blueprint('notif', __name__, url_prefix='/notif')

@notif_bp.route('/notifications')
@login_required
def get_notifications():
    notifications = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).order_by(Notification.created_at.desc()).all()
    
    return render_template('notifications.html', notifications=notifications)

@notif_bp.route('/notifications/mark_read/<int:notif_id>')
@login_required
def mark_read(notif_id):
    notif = Notification.query.get_or_404(notif_id)
    if notif.user_id != current_user.id:
        abort(403)
    notif.is_read = True
    db.session.commit()
    return redirect(notif.link or url_for('main.index'))


@notif_bp.route('/notifications/mark_read', methods=['POST'])
@login_required
def mark_all_read():
    notifications = Notification.query.filter_by(user_id=current_user.id, is_read=False).all()
    for n in notifications:
        n.is_read = True
    db.session.commit()
    return redirect(url_for('notif.get_notifications'))
