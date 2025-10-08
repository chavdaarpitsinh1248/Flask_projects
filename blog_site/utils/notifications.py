from models import Notification
from extensions import db

def create_notification(user, message, link=None):
    print(f"DEBUG: creating notification for {user.username}")
    notif = Notification(user_id=user.id, message=message, link=link)
    db.session.add(notif)
    db.session.commit()
    print(f"DEBUG: notification committed with id={notif.id}")
    return notif
