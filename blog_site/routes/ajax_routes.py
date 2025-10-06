from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from models import Post, Comment
from extensions import db

ajax_bp = Blueprint('ajax', __name__)

#-------------
#Comments AJAX
#-------------

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

    return jsonify({
    'success': True,
    'comment_id': comment.id,  
    'content': comment.content,
    'username': current_user.username,
    'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M'),
    'parent_id': parent_id
})


#AJAX Edit Comment
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

    return jsonify({
        'success': True,
        'content': comment.content,
        'comment_id': comment.id
    })

#AJAX Delete Comment
@ajax_bp.route('/comment/<int:comment_id>/ajax_delete', methods=['POST'])
@login_required
def ajax_delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    if comment.user != current_user:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    db.session.delete(comment)
    db.session.commit()

    return jsonify({'success': True, 'comment_id': comment_id})

#-------------
#Like/Unlike Post
#-------------

@ajax_bp.route('/like/<int:post_id>', methods=['POST'])
@login_required
def like_post(post_id):
    post = Post.query.get_or_404(post_id)
    if current_user in post.likes:
        # Unlike
        post.likes.remove(current_user)
        db.session.commit()
        liked=False

    else:
        # Like
        post.likes.append(current_user)
        db.session.commit()
        liked=True
    return jsonify({'liked': liked, 'total_likes': len(post.likes)})
