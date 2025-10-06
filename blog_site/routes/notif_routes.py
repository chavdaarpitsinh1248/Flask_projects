from flask import Blueprint, render_template
from flask_login import login_required, current_user
from models import Notification

notif_bp = Blueprint('notif', __name__)

@notif_bp.route('/notifications')
@login_required
def notifications():
    notifs = Notification.query.filter_by(user_id=current_user.id)\
                               .order_by(Notification.created_at.desc())\
                               .all()
    return render_template('notifications/list.html', notifications=notifs)