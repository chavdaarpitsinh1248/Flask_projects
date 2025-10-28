from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from datetime import datetime
from .. import db
from ..models import Comment, Chapter, Manga

comment_bp = Blueprint("comment", __name__)

# -----------------------------------------------------------
# ADD COMMENT (attached to a chapter; stores manga_id in Comment)
# -----------------------------------------------------------
@comment_bp.route("/chapter/<int:chapter_id>/comment", methods=["POST"])
@login_required
def add_comment(chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)
    content = request.form.get("content", "").strip()
    parent_id = request.form.get("parent_id")  # optional reply to another comment

    if not content:
        flash("Comment cannot be empty.", "warning")
        return redirect(url_for("manga.read_chapter", manga_id=chapter.manga_id, chapter_id=chapter.id))

    comment = Comment(
        content=content,
        user_id=current_user.id,
        manga_id=chapter.manga_id,
        parent_id=int(parent_id) if parent_id and parent_id.isdigit() else None,
        timestamp=datetime.utcnow(),
    )
    db.session.add(comment)
    db.session.commit()

    flash("Comment added successfully!", "success")
    return redirect(url_for("manga.read_chapter", manga_id=chapter.manga_id, chapter_id=chapter.id))

# -----------------------------------------------------------
# DELETE COMMENT (only owner or admin)
# -----------------------------------------------------------
@comment_bp.route("/comment/<int:comment_id>/delete", methods=["POST"])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)

    # Allow delete only for owner or admin
    if comment.user_id != current_user.id and not current_user.is_admin():
        abort(403)

    # Attempt to get chapter_id from form or redirect to manga page if unavailable
    chapter_id = request.form.get('chapter_id') or request.args.get('chapter_id')
    if chapter_id and str(chapter_id).isdigit():
        chapter_id = int(chapter_id)
        manga_id = Chapter.query.get(chapter_id).manga_id if Chapter.query.get(chapter_id) else comment.manga_id
    else:
        manga_id = comment.manga_id
        chapter_id = None

    db.session.delete(comment)
    db.session.commit()

    flash("Comment deleted.", "info")
    if chapter_id:
        return redirect(url_for("manga.read_chapter", manga_id=manga_id, chapter_id=chapter_id))
    return redirect(url_for("manga.view_manga", manga_id=manga_id))
