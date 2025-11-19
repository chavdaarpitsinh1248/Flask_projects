from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, current_app, jsonify
from flask_login import login_required, current_user
from models import Post, Comment, Like
from forms import PostForm, CommentForm
from extensions import db
from utils.notifications import create_notification
from utils.ai_helpers import generate_title, generate_summary

post_bp = Blueprint('post', __name__)

# ------------------
# Post CRUD Routes
# ------------------

#//////////////////////////////////////////////////////////////////////////////

# ------------------
#   CREATE POST
# ------------------

@post_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_post():
    form = PostForm()
    if form.validate_on_submit():
        content = form.content.data or ""
        user_title = (form.title.data or "").strip()

        # Default values (used if AI fails)
        title_to_use = user_title or "Untitled post"
        summary_to_use = ""

        # If user left title empty, try to generate one
        if not user_title:
            try:
                title_to_use = generate_title(content)
            except Exception as e:
                # Log and fallback
                current_app.logger.exception("AI title generation failed:")
                # keep the default 'Untitled post' or you could set to first 60 chars:
                if content:
                    title_to_use = (content.strip().replace("\n", " ")[:60] + "...")

        # Generate a summary (you can skip this if you prefer)
        try:
            summary_to_use = generate_summary(content)
        except Exception as e:
            current_app.logger.exception("AI summary generation failed:")
            # fallback: use first 120 chars as a simple summary
            summary_to_use = (content.strip().replace("\n", " ")[:120] + "...") if content else ""

        # Create and save the Post (includes summary)
        post = Post(title=title_to_use, content=content, summary=summary_to_use, user_id=current_user.id)
        db.session.add(post)
        db.session.commit()

        flash('Post created successfully!', 'success')
        return redirect(url_for('main.index'))

    return render_template('create_post.html', form=form, edit=False)
#
#
#    

@post_bp.route('/post/<int:post_id>')
@login_required  
def view_post(post_id):
    post = Post.query.get_or_404(post_id)
    comments = post.comments.order_by(Comment.created_at.asc()).all()

    liked_by_user = False
    if current_user.is_authenticated:
        liked_by_user = post.likes.filter_by(user_id=current_user.id).first() is not None

    comment_form = None
    if current_user.is_authenticated:
        comment_form = CommentForm()  # create the form instance

    return render_template(
        "view_post.html",
        post=post,
        comments=comments,
        liked_by_user=liked_by_user,
        form=comment_form
    )


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

    form.title.data = post.title
    form.content.data = post.content
    return render_template('create_post.html', form=form, edit=True)


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
    posts = Post.query.filter_by(user_id=current_user.id)\
                      .order_by(Post.created_at.desc())\
                      .paginate(page=page, per_page=per_page)
    return render_template('my_posts.html', posts=posts)


# ------------------
# Comment Route
# ------------------

@post_bp.route('/post/<int:post_id>/comment', methods=['POST'])
@login_required
def add_comment(post_id):
    post = Post.query.get_or_404(post_id)
    form = CommentForm()

    if form.validate_on_submit():
        # Add comment
        comment = Comment(
            content=form.content.data,
            user_id=current_user.id,
            post_id=post.id
        )
        db.session.add(comment)
        db.session.commit()  # commit to ensure comment exists

        print(f"DEBUG: Comment added for post_id={post.id} by user_id={current_user.id}")

        # Create notification if commenter is not author
        if post.author and post.author.id != current_user.id:
            notif = create_notification(
                user=post.author,
                message=f"{current_user.username} commented on your post '{post.title}'",
                link=url_for('post.view_post', post_id=post.id)
            )
            print(f"DEBUG: Notification created: {notif.message}")

        flash('Comment added successfully!', 'success')

    return redirect(url_for('post.view_post', post_id=post.id))

# ------------------
# Like Route
# ------------------

@post_bp.route('/like/<int:post_id>', methods=['POST'])
@login_required
def like_post(post_id):
    post = Post.query.get_or_404(post_id)
    
    # Prevent multiple likes
    if Like.query.filter_by(user_id=current_user.id, post_id=post.id).first():
        flash("You already liked this post!", "warning")
        return redirect(url_for('post.view_post', post_id=post.id))
    
    # Create like
    like = Like(user_id=current_user.id, post_id=post.id)
    db.session.add(like)

    # Create notification for post author if not yourself
    if post.author and post.author.id != current_user.id:
        create_notification(
            user=post.author,
            message=f"{current_user.username} liked your post '{post.title}'",
            link=url_for('post.view_post', post_id=post.id)
        )
    
    db.session.commit()
    flash("Post liked!", "success")
    return redirect(url_for('post.view_post', post_id=post.id))

#
#
#
@post_bp.route('/_generate_gemini_title', methods=['POST'])
@login_required
def generate_gemini_title():
    from utils.gemini_client import client
    data = request.get_json()
    content = data.get("content", "")

    if not content.strip():
        return jsonify({"error": "Content is empty"}), 400

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=f"Generate exactly ONE short, attractive blog title for "
                "the following content. Do NOT list multiple titles. "
                "Do NOT explain anything. Return ONLY the title.\n\n"
                f"{content}"
        )

        title = response.text.strip()
        return jsonify({"title": title})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


#
#
#
@post_bp.route('/_generate_gemini_summary', methods=['POST'])
@login_required
def generate_gemini_summary():
    from utils.gemini_client import client
    data = request.get_json()
    content = data.get("content", "")

    if not content.strip():
        return jsonify({"error": "Content is empty"}), 400

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=f"Write a concise summary for this blog post:\n\n{content}"
        )

        summary = response.text.strip()
        return jsonify({"summary": summary})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
