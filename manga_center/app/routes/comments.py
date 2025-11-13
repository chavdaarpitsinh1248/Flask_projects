from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app import db
from app.models import Comment, Chapter
from datetime import datetime

comment_bp = Blueprint('comments', __name__, url_prefix='/comments')


def fmt_dt(dt):
    """Format datetime for front-end display."""
    return dt.strftime("%Y-%m-%d %H:%M") if dt else ''


# -------------------------------
# ADD COMMENT or REPLY
# -------------------------------
@comment_bp.route('/<int:chapter_id>/add', methods=['POST'])
@login_required
def add_comment(chapter_id):
    chapter = Chapter.query.get(chapter_id)
    if not chapter:
        return jsonify(success=False, error='Chapter not found'), 404

    data = request.get_json() or {}
    content = (data.get('content') or '').strip()
    parent_id = data.get('parent_id')

    if not content:
        return jsonify(success=False, error='Comment cannot be empty'), 400

    parent = None
    if parent_id:
        parent = Comment.query.get(parent_id)
        if not parent:
            return jsonify(success=False, error='Parent comment not found'), 404
        # Optional: ensure same manga/chapter
        if parent.chapter_id != chapter.id:
            return jsonify(success=False, error='Invalid reply target'), 400

    new_comment = Comment(
        content=content,
        user_id=current_user.id,
        manga_id=chapter.manga_id,
        chapter_id=chapter.id,
        parent_id=parent.id if parent else None,
        created_at=datetime.utcnow()
    )

    db.session.add(new_comment)
    db.session.commit()

    return jsonify(
        success=True,
        comment_id=new_comment.id,
        username=current_user.username,
        content=new_comment.content,
        created_at=fmt_dt(new_comment.created_at),
        parent_id=new_comment.parent_id
    ), 201


# -------------------------------
# EDIT COMMENT
# -------------------------------
@comment_bp.route('/<int:comment_id>/edit', methods=['POST'])
@login_required
def edit_comment(comment_id):
    comment = Comment.query.get(comment_id)
    if not comment:
        return jsonify(success=False, error='Comment not found'), 404

    if comment.user_id != current_user.id:
        return jsonify(success=False, error='Unauthorized'), 403

    data = request.get_json() or {}
    new_content = (data.get('content') or '').strip()

    if not new_content:
        return jsonify(success=False, error='Comment cannot be empty'), 400

    comment.content = new_content
    db.session.commit()

    return jsonify(
        success=True,
        comment_id=comment.id,
        content=comment.content,
        updated_at=fmt_dt(datetime.utcnow())
    )


# -------------------------------
# DELETE COMMENT (+ replies)
# -------------------------------
@comment_bp.route('/<int:comment_id>/delete', methods=['POST'])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get(comment_id)
    if not comment:
        return jsonify(success=False, error='Comment not found'), 404

    if comment.user_id != current_user.id:
        return jsonify(success=False, error='Unauthorized'), 403

    # Delete all replies (recursive optional)
    def delete_with_replies(cmt):
        replies = Comment.query.filter_by(parent_id=cmt.id).all()
        for r in replies:
            delete_with_replies(r)
            db.session.delete(r)

    delete_with_replies(comment)
    db.session.delete(comment)
    db.session.commit()

    return jsonify(success=True, comment_id=comment_id)
