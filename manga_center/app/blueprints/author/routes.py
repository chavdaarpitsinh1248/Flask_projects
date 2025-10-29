
import os
from flask import render_template, request, redirect, url_for, flash, current_app, abort
from flask_login import login_required, current_user
from . import author_bp
from .forms import AddChapterForm, AddMangaForm
from ...extensions import db
from ...models import Manga, Chapter, Page
from ...utils import (allowed_file, slugify, generate_unique_slug,
                      save_and_verify_images)
from werkzeug.utils import secure_filename

MAX_PAGES_PER_CHAPTER = 500  # safety cap

@author_bp.route('/manga/<int:manga_id>/add-chapter', methods=['GET', 'POST'])
@login_required
def add_chapter(manga_id):
    manga = Manga.query.get_or_404(manga_id)

    # permission check: must be author of that manga or admin
    if current_user.id != manga.author_id and not current_user.is_admin():
        abort(403)

    form = AddChapterForm()
    if request.method == 'POST':
        # files from the form input name="pages"
        files = request.files.getlist('pages')
        # form.number may be None if using request.form; prefer explicit parse
        chapter_number = request.form.get('number', type=int) or form.number.data
        chapter_title = request.form.get('title', '').strip() or form.title.data

        # basic validation:
        if not chapter_number:
            flash('Please provide a chapter number.', 'warning')
            return redirect(request.url)

        if not files or len(files) == 0:
            flash('Please upload at least one image for the chapter pages.', 'warning')
            return redirect(request.url)

        if len(files) > MAX_PAGES_PER_CHAPTER:
            flash(f'You can upload at most {MAX_PAGES_PER_CHAPTER} pages per chapter.', 'warning')
            return redirect(request.url)

        # ensure chapter number is unique for this manga
        existing = Chapter.query.filter_by(manga_id=manga.id, number=chapter_number).first()
        if existing:
            flash(f'Chapter number {chapter_number} already exists for this manga.', 'danger')
            return redirect(request.url)

        # create a chapter row (do not commit yet)
        chapter_slug_base = chapter_title or f"chapter-{chapter_number}"
        chapter_slug = slugify(chapter_slug_base)
        # if you want to ensure unique chapter slug per manga, you can append chapter.number or use db constraints
        chapter = Chapter(manga_id=manga.id, number=chapter_number, title=chapter_title, slug=chapter_slug)
        db.session.add(chapter)
        db.session.flush()  # get chapter.id if needed

        # build safe folder names
        # use manga.slug, author's username and manga.id to avoid collisions
        author_username = (manga.author.username if getattr(manga, 'author', None) else f'user{manga.author_id}')
        manga_dirname = secure_filename(f"{manga.slug}-{author_username}-{manga.id}")
        chapter_dirname = secure_filename(f"chapter_{chapter.number}_{chapter.slug or chapter.title or ''}")

        try:
            # use utils to save/verify images; returns list of relative paths and absolute final paths
            relative_paths, absolute_paths = save_and_verify_images(files, manga_dirname, chapter_dirname)

            # create Page rows in DB
            page_number = 1
            for rel in relative_paths:
                p = Page(chapter_id=chapter.id, page_number=page_number, image_path=rel)
                db.session.add(p)
                page_number += 1

            # commit everything
            db.session.commit()

            # optional: create notifications for bookmarks - TODO
            flash('Chapter uploaded successfully.', 'success')
            return redirect(url_for('manga.detail', slug=manga.slug))

        except Exception as e:
            # rollback DB and notify the user
            db.session.rollback()
            # cleanup: save_and_verify_images already attempts to remove partial files on failure
            current_app.logger.exception("Failed to upload chapter images")
            flash(f'Failed to upload chapter: {e}', 'danger')
            return redirect(request.url)

    # GET
    return render_template('author/add_chapter.html', form=form, manga=manga)
