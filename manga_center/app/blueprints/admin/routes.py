
from flask import render_template, redirect, url_for, flash, abort, request
from flask_login import login_required, current_user
from . import admin_bp
from ...extensions import db
from ...models import User, Manga, Chapter, Page, Comment

def admin_required():
    if not (current_user.is_authenticated and current_user.is_admin()):
        abort(403)

@admin_bp.route('/')
@login_required
def dashboard():
    if not current_user.is_admin():
        abort(403)
    # minimal dashboard: counts
    user_count = User.query.count()
    manga_count = Manga.query.count()
    comment_count = Comment.query.count()
    return render_template('admin/dashboard.html', users=user_count, mangas=manga_count, comments=comment_count)

@admin_bp.route('/user/<int:user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    if not current_user.is_admin():
        abort(403)
    user = User.query.get_or_404(user_id)
    # Be careful — consider soft-delete in production
    db.session.delete(user)
    db.session.commit()
    flash('User deleted.', 'info')
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/manga/<int:manga_id>/delete', methods=['POST'])
@login_required
def delete_manga(manga_id):
    if not current_user.is_admin():
        abort(403)
    manga = Manga.query.get_or_404(manga_id)
    db.session.delete(manga)
    db.session.commit()
    flash('Manga deleted.', 'info')
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/comment/<int:comment_id>/delete', methods=['POST'])
@login_required
def delete_comment(comment_id):
    if not current_user.is_admin():
        abort(403)
    comment = Comment.query.get_or_404(comment_id)
    db.session.delete(comment)
    db.session.commit()
    flash('Comment deleted.', 'info')
    return redirect(request.referrer or url_for('admin.dashboard'))
