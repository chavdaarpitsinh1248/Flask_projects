from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from .. import db
from ..models import StudioRequest, User
from ..forms.studio_forms import StudioRequestForm
from datetime import datetime, timedelta

studio_bp = Blueprint('studio', __name__)

@studio_bp.route('/request', methods=['GET', 'POST'])
@login_required
def request_studio():
    form = StudioRequestForm()

    #check if user already has pending request
    pending = StudioRequest.query.filter_by(user_id=current_user.id, status="pending").first()
    if pending:
        flash("You already have a pending request.", "warning")
        return redirect(url_for('manga.index'))
    
    #check if user was rejected recently
    last_rejected = StudioRequest.query.filter_by(user_id=current_user.id, status='rejected').order_by(StudioRequest.rejected_until.desc()).first()
    if last_rejected and last_rejected.rejected_until and datetime.utcnow() < last_rejected.rejected_until:
        days_left = (last_rejected.rejected_until - datetime.utcnow()).days
        flash(f'Your Previous studio request was rejected. You can request again in {days_left} days.', 'warning')
        return redirect(url_for('manga.index'))
    
    if form.validate_on_submit():
        req = StudioRequest(user_id=current_user.id)
        db.session.add(req)
        db.session.commit()
        flash('Studio request submitted. Admin will review it.', 'success')
        return redirect(url_for('manga.index'))
    
    return render_template('studio_request.html', form=form)

## After adding new chapter
#bookmarked_users = [b.user for b in manga.bookmarked_by]
#for user in bookmarked_users:
#    notif = Notification(
#        user_id=user.id,
#        message=f'New chapter "{chapter.title}" added to "{manga.title}"'
#    )
#    db.session.add(notif)
#db.session.commit()
