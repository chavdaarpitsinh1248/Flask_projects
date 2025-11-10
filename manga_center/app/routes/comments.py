from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app import db
from app.models import Comment, Manga, Chapter

comment_bp = Blueprint('comments',__name__)

@comment_bp.route('/<int:chapter_id>')
def get_comments(chapter_id):
    comments = Comment.query.filter_by(chapter_id=chapter_id, parent_id=None).order_by(Comment.created_at.desc()).all()

    def serialize_comment(c):
        return {
            "id": c.id,
            "user_id": c.user_id,
            "username": c.user.username,
            "pen_name": getattr(c.user.author_profile, "pen_name", None),
            "is_author": (c.user.author_profile and c.user.author_profile.mangas and 
                          any(chapter_id == ch.id for m in c.user.author_profile.mangas for ch in m.chapters)),
            "content": c.content,
            "created_at": c.created_at.strftime("%Y-%m-%d %H:%M"),
            "replies": [serialize_comment(r) for r in c.replies]
        }
    return jsonify([serialize_comment(c) for c in comments])


@comment_bp.route('/add', methods=['POST'])
@login_required
def add_comment():
    data = request.get_json()
    content = data.get('content')
    chapter_id = data.get('chapter_id')
    parent_id = data.get('parent_id')

    if not content or not chapter_id:
        return jsonify({"error" : "Missing content or chapter" }), 400
    
    comment = Comment(
        content=content.strip(),
        user_id=current_user.id,
        chapter_id=chapter_id,
        manga_id=Chapter.query.get(chapter_id).manga_id,
        parent_id=parent_id
    )
    db.session.add(comment)
    db.session.commit()

    return jsonify({
        "status": "success",
        "message": "Comment Added",
        "comment": {
            "id": comment.id,
            "user": current_user.username,
            "pen_name": getattr(current_user.author_profile, "pen_name", None),
            "content": comment.content,
            "created_at": comment.created_at.strftime("%Y-%m-%d %H:%M"),
        }
    })