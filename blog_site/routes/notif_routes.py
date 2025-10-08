from flask import Blueprint, jsonify, abort
from flask_login import login_required, current_user
from models import Notification
from extensions import db

notif_bp = Blueprint('notif', __name__, url_prefix='/notif')

# Fetch unread notifications
@notif_bp.route('/notifications')
@login_required
def get_notifications():
    notifications = [
        {"id": n.id, "message": n.message, "link": n.link}
        for n in Notification.query.filter_by(user_id=current_user.id, is_read=False).all()
    ]
    return jsonify({"notifications": notifications})


# Mark all as read via AJAX
@notif_bp.route('/notifications/mark_read', methods=['POST'])
@login_required
def mark_all_read():
    notifications = Notification.query.filter_by(user_id=current_user.id, is_read=False).all()
    for n in notifications:
        n.is_read = True
    db.session.commit()
    return jsonify({"success": True})

# Optional: mark single notification as read
@notif_bp.route('/notifications/mark_read/<int:notif_id>', methods=['POST'])
@login_required
def mark_read_single(notif_id):
    notif = Notification.query.get_or_404(notif_id)
    if notif.user_id != current_user.id:
        abort(403)
    notif.is_read = True
    db.session.commit()
    return jsonify({"success": True})
