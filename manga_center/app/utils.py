# app/utils.py
import re
import os
import uuid
import shutil
import tempfile
from unicodedata import normalize
from pathlib import Path
from typing import List, Tuple
from flask import current_app
from PIL import Image, UnidentifiedImageError
from werkzeug.utils import secure_filename

ALLOWED_IMAGE_EXT = {'png', 'jpg', 'jpeg', 'webp', 'gif'}

def slugify(text: str) -> str:
    """
    Simple slugify: normalize, remove non-alnum, replace spaces with hyphens.
    Keeps ASCII only.
    """
    if not text:
        return ''
    text = normalize('NFKD', text)
    text = text.encode('ascii', 'ignore').decode('ascii')  # drop non-ascii
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s-]+', '-', text).strip('-')
    return text or str(uuid.uuid4())[:8]

def generate_unique_slug(model, value: str, column='slug') -> str:
    """
    Generate a slug for `value` that does not collide in `model`.
    model: SQLAlchemy model class
    column: attribute name used for uniqueness (default 'slug')
    """
    base = slugify(value)
    slug = base
    counter = 1
    # query the DB to check existence
    q = {column: slug}
    while model.query.filter(getattr(model, column) == slug).first():
        slug = f"{base}-{counter}"
        counter += 1
    return slug

def allowed_file(filename: str) -> bool:
    if not filename:
        return False
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    return ext in ALLOWED_IMAGE_EXT

def save_and_verify_images(files: List, manga_dirname: str, chapter_dirname: str
                           ) -> Tuple[List[str], List[str]]:
    """
    Save uploaded files (werkzeug FileStorage) safely:
    - Save to a temp dir first
    - Verify each file is an image using Pillow (Image.verify)
    - Move to final dir under app.static_folder / UPLOADS_DIR / mangas / manga_dirname / chapter_dirname
    Returns (relative_paths, absolute_paths_saved) where relative_paths are paths to store in DB
    On failure, raises Exception (caller should handle cleanup).
    """
    app = current_app._get_current_object()
    uploads_dir = app.config.get('UPLOADS_DIR', 'uploads')
    final_dir = Path(app.static_folder) / uploads_dir / 'mangas' / manga_dirname / chapter_dirname
    final_dir.mkdir(parents=True, exist_ok=True)

    # create a temp dir
    tmp_dir = Path(tempfile.mkdtemp(prefix='manga_upload_'))
    saved_final_paths = []
    relative_paths = []

    try:
        page_index = 1
        for f in files:
            # f is FileStorage
            filename = f.filename
            if not filename or not allowed_file(filename):
                raise ValueError(f"Invalid file or extension: {filename}")

            # save to temp file
            ext = filename.rsplit('.', 1)[-1].lower()
            tmp_path = tmp_dir / f"{uuid.uuid4().hex}.{ext}"
            f.save(str(tmp_path))

            # verify image using Pillow
            try:
                with Image.open(tmp_path) as im:
                    im.verify()  # will raise if not image or corrupted
            except (UnidentifiedImageError, OSError) as e:
                raise ValueError(f"Uploaded file is not a valid image: {filename}") from e

            # Optionally re-open and save to standard format/strip metadata (re-open to avoid "verify" issues)
            try:
                with Image.open(tmp_path) as im:
                    # convert to RGB for formats without alpha if desired; keep original mode otherwise
                    # NOTE: avoid automatic format changes unless you want standardized output
                    out_ext = ext
                    final_name = f"{page_index:03d}.{out_ext}"
                    final_path = final_dir / final_name
                    # Save with Pillow to ensure clean image file
                    im.save(final_path)
            except Exception as e:
                raise RuntimeError(f"Failed to process image {filename}: {e}") from e

            # store relative path for DB (web-accessible via /static/)
            rel_path = os.path.join(uploads_dir, 'mangas', manga_dirname, chapter_dirname, final_name)
            relative_paths.append(rel_path.replace('\\', '/'))  # normalize windows paths
            saved_final_paths.append(str(final_path))

            page_index += 1

        # clean up temp dir
        shutil.rmtree(tmp_dir, ignore_errors=True)
        return relative_paths, saved_final_paths

    except Exception:
        # on any error, remove any final files that were saved and the tmp_dir
        for p in saved_final_paths:
            try:
                os.remove(p)
            except Exception:
                pass
        try:
            shutil.rmtree(tmp_dir, ignore_errors=True)
        except Exception:
            pass
        # if final_dir is empty, try removing it
        try:
            if final_dir.exists() and not any(final_dir.iterdir()):
                final_dir.rmdir()
        except Exception:
            pass
        raise  # re-raise to caller
