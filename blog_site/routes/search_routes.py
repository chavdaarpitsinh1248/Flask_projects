from flask import Blueprint, render_template, request
from forms import SearchForm
from models import Post

search_bp = Blueprint('search', __name__)

@search_bp.route('/search', methods=['GET', 'POST'])
def search():
    form = SearchForm()
    q = ''
    page = request.args.get('page', 1, type=int)

    if form.validate_on_submit():  # POST
        q = form.query.data
    elif request.method == 'GET':  # GET with page navigation
        q = request.args.get('query', '')

    posts = []
    if q:
        posts = Post.query.filter(
            (Post.title.ilike(f"%{q}%")) | (Post.content.ilike(f"%{q}%"))
        ).order_by(Post.created_at.desc()).paginate(page=page, per_page=10)

    return render_template('search.html', form=form, posts=posts, query=q)
