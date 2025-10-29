
import os
from flask import render_template, request, redirect, url_for, flash, current_app, abort
from werkzeug.utils import secure_filename
from flask_login import login_required, current_user
from . import author_bp
from .forms import AddMangaForm, AddChapterForm
from ...extensions import db
from ...models import Manga, Chapter, Page

ALLOWED_EXT = {'png', 'jpg', 'jpeg', 'webp', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXT

@author_bp.route('/manga/add', methods=['GET', 'POST'])
@login_required
def add_manga():
    # only authors or admins can create manga
    if not current_user.is_author():
        abort(403)
    form = AddMangaForm()
    if form.validate_on_submit():
        slug = secure_filename(form.title.data).lower().replace(' ', '-')
        manga = Manga(title=form.title.data, slug=slug, description=form.description.data, author_id=current_user.id)
        db.session.add(manga)
        db.session.commit()
        flash('Manga created. Now add chapters.', 'success')
        return redirect(url_for('author.add_chapter', manga_id=manga.id))
    return render_template('author/add_manga.html', form=form)

@author_bp.route('/manga/<int:manga_id>/add-chapter', methods=['GET', 'POST'])
@login_required
def add_chapter(manga_id):
    # authors can add chapters only for their own mangas (or admins)
    manga = Manga.query.get_or_404(manga_id)
    if current_user.id != manga.author_id and not current_user.is_admin():
        abort(403)

    form = AddChapterForm()
    if request.method == 'POST':
        # files should be in request.files.getlist('pages')
        files = request.files.getlist('pages')
        chapter_number = request.form.get('number', type=int) or form.number.data
        title = request.form.get('title') or form.title.data

        if not chapter_number:
            flash('Chapter number is required', 'warning')
            return redirect(request.url)

        # create chapter
        chapter = Chapter(manga_id=manga.id, number=chapter_number, title=title)
        db.session.add(chapter)
        db.session.flush()  # get chapter.id

        # build folders under app.static/uploads/mangas/{manga_slug}-{author_username}/chapter_{number}_{chapter_slug}
        manga_dir = secure_filename(f"{manga.slug}-{manga.author.username}")
        chapter_slug = secure_filename(title) if title else ''
        chapter_dir = secure_filename(f"chapter_{chapter.number}_{chapter_slug}")

        base_dir = os.path.join(current_app.static_folder, current_app.config.get('UPLOADS_DIR', 'uploads'),
                                'mangas', manga_dir, chapter_dir)
        os.makedirs(base_dir, exist_ok=True)

        page_index = 1
        for f in files:
            if f and allowed_file(f.filename):
                ext = f.filename.rsplit('.', 1)[1].lower()
                new_name = f"{page_index:03d}.{ext}"
                save_path = os.path.join(base_dir, new_name)
                f.save(save_path)
                rel_path = os.path.join(current_app.config.get('UPLOADS_DIR', 'uploads'),
                                        'mangas', manga_dir, chapter_dir, new_name)
                page = Page(chapter_id=chapter.id, page_number=page_index, image_path=rel_path)
                db.session.add(page)
                page_index += 1

        db.session.commit()
        flash('Chapter added successfully.', 'success')
        return redirect(url_for('manga.detail', slug=manga.slug))

    return render_template('author/add_chapter.html', form=form, manga=manga)
