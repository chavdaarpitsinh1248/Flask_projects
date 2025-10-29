
import os
import logging
from pathlib import Path
from werkzeug.utils import secure_filename
from flask import (
    render_template,
    request,
    redirect,
    url_for,
    flash,
    current_app,
    abort,
)
from flask_login import login_required, current_user

from . import author_bp
from .forms import AddMangaForm, AddChapterForm
from ...extensions import db
from ...models import Manga, Chapter, Page
from ...utils import (
    slugify,
    generate_unique_slug,
    allowed_file,
    save_and_verify_images,
    save_single_image,
)

logger = logging.getLogger(__name__)

# safety caps
MAX_PAGES_PER_CHAPTER = 500
ALLOWED_COVER_EXT = {'png', 'jpg', 'jpeg', 'webp', 'gif'}


def make_manga_dirname(manga: Manga) -> str:
    """
    Build a safe directory name for a manga using its slug, author username and id.
    Example: one-piece-arpit-12
    """
    author_username = getattr(manga.author, "username", f"user{manga.author_id}")
    name = f"{manga.slug}-{author_username}-{manga.id}"
    return secure_filename(name)


@author_bp.route("/manga/add", methods=["GET", "POST"])
@login_required
def add_manga():
    """Create a new manga. Only available to authors or admins."""
    if not current_user.is_author():
        abort(403)

    form = AddMangaForm()
    if form.validate_on_submit() or request.method == "POST":
        title = form.title.data or request.form.get("title", "")
        description = form.description.data or request.form.get("description", "")

        if not title:
            flash("Title is required.", "warning")
            return render_template("author/add_manga.html", form=form)

        # generate unique slug
        slug = generate_unique_slug(Manga, title, column="slug")

        # create manga row
        manga = Manga(title=title, slug=slug, description=description, author_id=current_user.id)
        db.session.add(manga)
        db.session.flush()  # get manga.id for directory naming

        # handle optional cover image
        cover_file = request.files.get("cover_image") or None
        if cover_file and cover_file.filename:
            try:
                # build final dir: static/uploads/mangas/{manga_dirname}/
                uploads_dir = current_app.config.get("UPLOADS_DIR", "uploads")
                manga_dirname = make_manga_dirname(manga)
                final_dir = Path(current_app.static_folder) / uploads_dir / "mangas" / manga_dirname

                # use save_single_image helper; name cover as 'cover'
                rel_path = save_single_image(cover_file, final_dir, "cover")
                manga.cover_image = rel_path
            except ValueError as ve:
                db.session.rollback()
                flash(str(ve), "danger")
                logger.exception("Cover image validation failed.")
                return render_template("author/add_manga.html", form=form)
            except Exception as e:
                db.session.rollback()
                flash("Failed to save cover image.", "danger")
                logger.exception("Unexpected error saving cover image.")
                return render_template("author/add_manga.html", form=form)

        # commit manga
        db.session.commit()
        flash("Manga created. You can now add chapters.", "success")
        return redirect(url_for("author.add_chapter", manga_id=manga.id))

    return render_template("author/add_manga.html", form=form)


@author_bp.route("/manga/<int:manga_id>/add-chapter", methods=["GET", "POST"])
@login_required
def add_chapter(manga_id):
    """Author adds a chapter with multiple image pages."""
    manga = Manga.query.get_or_404(manga_id)

    # permission: only the manga's author or admin
    if current_user.id != manga.author_id and not current_user.is_admin():
        abort(403)

    form = AddChapterForm()
    if request.method == "POST":
        # prefer explicit request.form values to ensure consistent behavior
        chapter_number = request.form.get("number", type=int) or form.number.data
        chapter_title = (request.form.get("title", "") or form.title.data or "").strip()

        files = request.files.getlist("pages")
        if not chapter_number:
            flash("Chapter number is required.", "warning")
            return redirect(request.url)

        if not files or len([f for f in files if f and f.filename]) == 0:
            flash("Please upload at least one page image.", "warning")
            return redirect(request.url)

        if len(files) > MAX_PAGES_PER_CHAPTER:
            flash(f"Maximum pages per chapter: {MAX_PAGES_PER_CHAPTER}", "warning")
            return redirect(request.url)

        # check uniqueness of chapter number for this manga
        if Chapter.query.filter_by(manga_id=manga.id, number=chapter_number).first():
            flash(f"Chapter {chapter_number} already exists for this manga.", "danger")
            return redirect(request.url)

        # prepare chapter db row
        chapter_slug_base = chapter_title or f"chapter-{chapter_number}"
        chapter_slug = slugify(chapter_slug_base)
        chapter = Chapter(manga_id=manga.id, number=chapter_number, title=chapter_title, slug=chapter_slug)

        db.session.add(chapter)
        db.session.flush()  # to ensure chapter.id exists if needed

        # build final folders using manga dir name (includes manga.id)
        uploads_dir = current_app.config.get("UPLOADS_DIR", "uploads")
        manga_dirname = make_manga_dirname(manga)
        # sanitize chapter_dirname; may be long - secure_filename will trim invalid chars
        chapter_dirname_raw = f"chapter_{chapter.number}_{chapter.slug or chapter.title or ''}"
        chapter_dirname = secure_filename(chapter_dirname_raw)

        try:
            # save_and_verify_images will create final_dir and return relative paths for DB
            relative_paths, _abs_paths = save_and_verify_images(files, manga_dirname, chapter_dirname)

            # create Page rows in order
            pnum = 1
            for rel in relative_paths:
                page = Page(chapter_id=chapter.id, page_number=pnum, image_path=rel)
                db.session.add(page)
                pnum += 1

            # commit all
            db.session.commit()

            # TODO: create Notification rows for users who bookmarked this manga
            flash("Chapter uploaded successfully.", "success")
            return redirect(url_for("manga.detail", slug=manga.slug))

        except Exception as e:
            db.session.rollback()
            logger.exception("Failed to upload chapter images")
            flash(f"Failed to upload chapter: {e}", "danger")
            return redirect(request.url)

    # GET
    return render_template("author/add_chapter.html", form=form, manga=manga)
