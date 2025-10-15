import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user, logout_user
from werkzeug.utils import secure_filename
from .. import db
from ..models import User, History, Bookmark

profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/')
@login_required
def profile_home():
    return redirect(url_for('profile.my_account'))

# My Account
@profile_bp.route('/my_account', methods=["GET", "POST"])
@login_required
def my_account():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        new_password = request.form.get('new_password')

        # profile_pic 
        if 'image_file' in request.files:
            image = request.files['image_file']
            if image.filename != '':
                filename = secure_filename(image.filename)
                image_path = os.path.join(current_app.root_path, 'static/profile_pics', filename)
                image.save(image_path)
                current_user.image_file = filename

        # Update user info
        current_user.username = username
        current_user.email = email
        if new_password:
            current_user.set_password(new_password)
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile.my_account'))
    
    return render_template('profile/my_account.html')


# Delete Account
@profile_bp.route('/delete_account', methods=['POST'])
@login_required
def delete_account():
    password = request.form.get('password')
    if not current_user.check_password(password):
        flash('Incorrect password.', 'danger')
        return redirect(url_for('profile.my_account'))
    
    user_id=current_user.id
    logout_user()
    User.query.filter_by(id=user_id).delete()
    db.session.commit()
    flash('Account deleted successfully.', 'success')
    return redirect(url_for('auth.login'))


# History
@profile_bp.route('/history')
@login_required
def history():
    # Fetch all history entries for current users, latest first
    history_entries = (
        History.query.filter_by(user_id = current_user.id)
        .order_by(History.last_viewed.desc())
        .all(0)
    )
    return render_template('profile/history.html', history_entries=history_entries)

@profile_bp.route('/history/clear', methods=["POST"])
@login_required
def clear_history():
    History.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    flash("History cleared successfully!", "success")
    return redirect(url_for('profile.history'))


#Bookmark
@profile_bp.route('/bookmarks')
@login_required
def bookmarks():
    bookmarks = Bookmark.query.filter_by(user_id=current_user.id).order_by(Bookmark.timestamp.desc()).all()
    return render_template('profile/bookmarks.html', bookmarks=bookmarks)