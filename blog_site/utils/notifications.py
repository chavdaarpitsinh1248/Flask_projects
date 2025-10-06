from models import Notification
from extensions import db



def create_notification(user, message, link=None):
    notif = Notification(user_id=user.id, message=message, link=link)
    db.session.add(notif)
    db.session.commit()
