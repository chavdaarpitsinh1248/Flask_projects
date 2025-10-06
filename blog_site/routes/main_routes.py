from flask import Blueprint, render_template, request
from models import Post, User, Comment
from flask_login import login_required

main_bp = Blueprint('main', __name__)

#Home
@main_bp.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    posts = Post.query.order_by(Post.created_at.desc()).paginate(page=page,per_page=per_page)
    return render_template('index.html', posts=posts)

#Dashboard
@main_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

#User profile
@main_bp.route('/user/<int:user_id>')
def user_profile(user_id):
    user = User.query.get_or_404(user_id)
    posts = Post.query.filter_by(user_id=user.id).order_by(Post.created_at.desc()).all()
    return render_template('user_profile.html', user=user, posts=posts)
