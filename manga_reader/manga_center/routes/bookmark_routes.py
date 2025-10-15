from flask import Blueprint, redirect, url_for, flash
from flask_login import login_required, current_user
from .. import db
from ..models import User, Bookmark, Notification, Manga

bookmark_bp = Blueprint('bookmark', __name__)

# Add or Remove Bookmark(toggle)
@bookmark_bp.route('/toggle/<int:manga_id>')
@login_required
def toggle_bookmark(manga_id):
    manga = Manga.query.get_or_404(manga_id)
    bookmark = Bookmark.query.filter_by(user_id=current_user.id, manga_id=manga_id).first()

    if bookmark:
        # Remove Bookmark
        db.session.delete(bookmark)
        db.session.commit()
        flash(f'Removed { manga.title } from bookmarks.', 'info')

    else:
        # Add Bookmark
        new_bookmark = Bookmark(user_id=current_user.id, manga_id=manga_id)
        db.session.add(new_bookmark)
        db.session.commit()
        flash(f'Bookmarked { manga.title }.', 'success')

    return redirect(url_for('manga.view_manga', manga_id=manga_id))