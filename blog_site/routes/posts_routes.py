from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from models import Post, Comment
from forms import PostForm, CommentForm
from extensions import db

post_bp = Blueprint('post', __name__)

@post_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data, content=form.content.data, user_id=current_user.id)
        db.session.add(post)
        db.session.commit()
        flash('Post created successfully!', 'success')
        return redirect(url_for('main.index'))
    return render_template('create_post.html', form=form, edit=False)

@post_bp.route('/post/<int:post_id>')
def view_post(post_id):
    post = Post.query.get_or_404(post_id)
    form = CommentForm()

    # Only top-level comments
    comments = post.comments.filter_by(parent_id=None).order_by(Comment.created_at.asc()).all()

    return render_template('view_post.html', post=post, form=form, comments=comments)

@post_bp.route('/edit/<int:post_id>', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)

    if post.author != current_user:
        abort(403)
    
    form = PostForm(obj=post)
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash('Post updated successfully!', 'success')
        return redirect(url_for('main.index'))

    #pre-fill form with existing post data
    form.title.data = post.title
    form.content.data = post.content
    return render_template('create_post.html', form=form, edit=True)

#Delete Post
@post_bp.route('/delete/<int:post_id>', methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)

    if post.author != current_user:
        abort(403)
    
    db.session.delete(post)
    db.session.commit()
    flash('Post deleted successfully!', 'success')
    return redirect(url_for('main.index'))

@post_bp.route('/my_posts')
@login_required
def my_posts():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    posts = Post.query.filter_by(user_id=current_user.id).order_by(Post.created_at.desc()).paginate(page=page,per_page=per_page)
    return render_template('my_posts.html', posts=posts)


from utils.notifications import create_notification

@post_bp.route('/post/<int:post_id>/comment', methods=['POST'])
@login_required
def add_comment(post_id):
    post = Post.query.get_or_404(post_id)
    form = CommentForm()

    if form.validate_on_submit():
        comment = Comment(
            content=form.content.data,
            user_id=current_user.id,
            post_id=post.id
        )
        db.session.add(comment)
        db.session.commit()

        # Notify the post author (but not if they comment on their own post)
        try:
            if post.author != current_user:
                create_notification(
                user=post.author,
                message=f"{current_user.username} commented on your post",
                link=url_for('post.view_post', post_id=post.id)
                )
        except Exception as e:
            print("Notification error:", e)

        flash("Comment added!", "success")
    return redirect(url_for('post.view_post', post_id=post.id))
