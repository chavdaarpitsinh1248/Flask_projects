from flask import Blueprint, jsonify, request, url_for
from flask_login import login_required, current_user
from models import Post, Comment, Like
from extensions import db
from utils.notifications import create_notification

ajax_bp = Blueprint('ajax', __name__)

# ------------------
# Add Comment via AJAX
# ------------------

@ajax_bp.route('/post/<int:post_id>/ajax_comment', methods=['POST'])
@login_required
def ajax_comment(post_id):
    data = request.get_json()
    content = data.get('content', '').strip()
    parent_id = data.get('parent_id')

    if not content:
        return jsonify({'success': False, 'error': 'Comment cannot be empty.'})
    
    post = Post.query.get_or_404(post_id)
    comment = Comment(content=content, user_id=current_user.id, post_id=post.id, parent_id=parent_id)
    db.session.add(comment)
    db.session.commit()

    print(f"DEBUG: AJAX Comment added for post_id={post.id} by user_id={current_user.id}")

    # Create notification
    if post.author and post.author.id != current_user.id:
        notif = create_notification(
            user=post.author,
            message=f"{current_user.username} commented on your post '{post.title}'",
            link=url_for('post.view_post', post_id=post.id)
        )
        print(f"DEBUG: AJAX Notification created: {notif.message}")

    return jsonify({
        'success': True,
        'comment_id': comment.id,
        'content': comment.content,
        'username': current_user.username,
        'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M'),
        'parent_id': parent_id
    })


# ------------------
# Edit Comment via AJAX
# ------------------

@ajax_bp.route('/comment/<int:comment_id>/ajax_edit', methods=['POST'])
@login_required
def ajax_edit_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    if comment.user != current_user:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    data = request.get_json()
    content = data.get('content', '').strip()
    if not content:
        return jsonify({'success': False, 'error': 'Comment cannot be empty.'})
    
    comment.content = content
    db.session.commit()

    return jsonify({'success': True, 'content': comment.content, 'comment_id': comment.id})


# ------------------
# Delete Comment via AJAX
# ------------------

@ajax_bp.route('/comment/<int:comment_id>/ajax_delete', methods=['POST'])
@login_required
def ajax_delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    if comment.user != current_user:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    db.session.delete(comment)
    db.session.commit()

    return jsonify({'success': True, 'comment_id': comment_id})

# ------------------
# Like via AJAX
# ------------------

@ajax_bp.route('/post/<int:post_id>/ajax_like', methods=['POST'])
@login_required
def ajax_like(post_id):
    post = Post.query.get_or_404(post_id)

    # Check if user already liked the post
    existing_like = Like.query.filter_by(user_id=current_user.id, post_id=post.id).first()
    liked = False

    if existing_like:
        # If already liked, remove like (toggle behavior)
        db.session.delete(existing_like)
    else:
        # Add new like
        like = Like(user_id=current_user.id, post_id=post.id)
        db.session.add(like)
        liked = True

        # Notification for post author
        if post.author and post.author.id != current_user.id:
            create_notification(
                user=post.author,
                message=f"{current_user.username} liked your post '{post.title}'",
                link=url_for('post.view_post', post_id=post.id)
            )

    db.session.commit()

    return jsonify({
        'success': True,
        'liked': liked,
        'like_count': post.likes.count()
    })