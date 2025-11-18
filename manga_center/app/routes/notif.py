from flask import Blueprint, jsonify, request, render_template
from flask_login import login_required, current_user
from app import db
from app.models import Notification

notif_bp = Blueprint('notifications', __name__, url_prefix='/notifications')

# -----------------------------
# Get all notifications (JSON or HTML)
# -----------------------------
@notif_bp.route('/', methods=['GET'])
@login_required
def get_notifications():
    """Return all notifications for the logged-in user."""
    notifications = (
        Notification.query.filter_by(user_id=current_user.id)
        .order_by(Notification.created_at.desc())
        .all()
    )

    # AJAX request → return JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.args.get('ajax') == '1':
        return jsonify([
            {
                'id': n.id,
                'message': n.message,
                'link': n.link,
                'is_read': n.is_read,
                'created_at': n.created_at.strftime('%Y-%m-%d %H:%M'),
            }
            for n in notifications
        ])

    # Normal request → render HTML template
    return render_template('all_notifications.html', notifications=notifications)


# -----------------------------
# Mark a single notification as read
# -----------------------------
@notif_bp.route('/<int:notif_id>/mark_read', methods=['POST'])
@login_required
def mark_notification_read(notif_id):
    notif = Notification.query.get_or_404(notif_id)
    if notif.user_id != current_user.id:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    notif.is_read = True
    db.session.commit()
    return jsonify({'success': True, 'notif_id': notif_id})


# -----------------------------
# Mark all notifications as read
# -----------------------------
@notif_bp.route('/mark_all_read', methods=['POST'])
@login_required
def mark_all_notifications_read():
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({'is_read': True})
    db.session.commit()
    return jsonify({'success': True})


# -----------------------------
# Delete a notification
# -----------------------------
@notif_bp.route('/<int:notif_id>/delete', methods=['POST'])
@login_required
def delete_notification(notif_id):
    notif = Notification.query.get_or_404(notif_id)
    if notif.user_id != current_user.id:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    db.session.delete(notif)
    db.session.commit()
    return jsonify({'success': True, 'notif_id': notif_id})

