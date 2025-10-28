
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from datetime import datetime
from .. import db
from ..models import Comment, Chapter, Manga

comment_bp = Blueprint("comment", __name__)

# -----------------------------------------------------------
# ADD COMMENT
# -----------------------------------------------------------
@comment_bp.route("/chapter/<int:chapter_id>/comment", methods=["POST"])
@login_required
def add_comment(chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)
    content = request.form.get("content", "").strip()

    if not content:
        flash("Comment cannot be empty.", "warning")
        return redirect(url_for("manga.read_chapter", manga_id=chapter.manga_id, chapter_id=chapter.id))

    comment = Comment(
        content=content,
        user_id=current_user.id,
        chapter_id=chapter.id,
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
    if comment.user_id != current_user.id and not getattr(current_user, "is_admin", False):
        abort(403)

    chapter_id = comment.chapter_id
    manga_id = comment.chapter.manga_id

    db.session.delete(comment)
    db.session.commit()

    flash("Comment deleted.", "info")
    return redirect(url_for("manga.read_chapter", manga_id=manga_id, chapter_id=chapter_id))
