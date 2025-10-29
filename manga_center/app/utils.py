
import re
import os
import uuid
import shutil
import tempfile
from unicodedata import normalize
from pathlib import Path
from typing import List, Tuple, Union
from flask import current_app
from PIL import Image, UnidentifiedImageError
from werkzeug.utils import secure_filename

# Allowed image extensions
ALLOWED_IMAGE_EXT = {'png', 'jpg', 'jpeg', 'webp', 'gif'}


def slugify(text: str) -> str:
    """
    Simple slugify: normalize, remove non-alnum, replace spaces with hyphens.
    Keeps ASCII only. Returns a short uuid-based slug if result is empty.
    """
    if not text:
        return str(uuid.uuid4())[:8]
    text = normalize('NFKD', text)
    text = text.encode('ascii', 'ignore').decode('ascii')  # drop non-ascii
    text = text.lower().strip()
    # remove invalid chars
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    # collapse whitespace/hyphens
    text = re.sub(r'[\s-]+', '-', text).strip('-')
    return text or str(uuid.uuid4())[:8]


def generate_unique_slug(model, value: str, column: str = 'slug') -> str:
    """
    Generate a slug for `value` that does not collide in `model`.
    model: SQLAlchemy model class
    column: attribute name used for uniqueness (default 'slug')
    """
    base = slugify(value)
    slug = base
    counter = 1
    while model.query.filter(getattr(model, column) == slug).first():
        slug = f"{base}-{counter}"
        counter += 1
    return slug


def allowed_file(filename: str) -> bool:
    """Return True if filename has an allowed image extension."""
    if not filename:
        return False
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    return ext in ALLOWED_IMAGE_EXT


def _get_uploads_base() -> Path:
    """
    Return the absolute Path to the uploads folder inside the app's static folder.
    Default uploads dir is 'uploads' (config UPLOADS_DIR).
    """
    app = current_app._get_current_object()
    uploads_dir = app.config.get('UPLOADS_DIR', 'uploads')
    base = Path(app.static_folder) / uploads_dir
    return base


def save_single_image(file_storage,
                      target_dir: Union[str, Path],
                      filename_base: str) -> str:
    """
    Save and verify a single uploaded image safely.

    Parameters:
    - file_storage: werkzeug FileStorage (the uploaded file)
    - target_dir: Path or str - absolute or relative Path to directory where file should be placed.
                  Prefer an absolute Path under app.static_folder (function will create dir if needed).
    - filename_base: base filename (without extension) to use (e.g. 'cover' or 'avatar').

    Returns:
    - relative path (string) to store in DB (e.g. 'uploads/mangas/<manga_dir>/<cover>.jpg')

    Raises:
    - ValueError on invalid file or verification failure
    - RuntimeError for unexpected IO issues
    """
    if not file_storage or not getattr(file_storage, 'filename', None):
        raise ValueError("No file provided.")

    filename = file_storage.filename
    if not allowed_file(filename):
        raise ValueError("Invalid file extension.")

    # Resolve target_dir to Path
    if isinstance(target_dir, (str,)):
        target_dir = Path(target_dir)
    target_dir = target_dir if target_dir.is_absolute() else Path(target_dir)

    # Ensure directory exists
    target_dir.mkdir(parents=True, exist_ok=True)

    # determine extension and safe filename
    ext = filename.rsplit('.', 1)[-1].lower()
    safe_base = secure_filename(filename_base) or uuid.uuid4().hex
    safe_name = f"{safe_base}.{ext}"

    # temp file path inside same directory to avoid cross-device move issues
    tmp_path = target_dir / f".tmp_{uuid.uuid4().hex}.{ext}"
    # final absolute path
    final_path = target_dir / safe_name

    try:
        # save upload to temp path
        file_storage.save(str(tmp_path))

        # verify image using Pillow
        try:
            with Image.open(tmp_path) as im:
                im.verify()  # will raise if file is not a valid image
        except (UnidentifiedImageError, OSError) as e:
            # cleanup tmp
            try:
                tmp_path.unlink()
            except Exception:
                pass
            raise ValueError("Uploaded file is not a valid image.") from e

        # re-open and save to final path to normalize and strip metadata
        try:
            with Image.open(tmp_path) as im:
                im.save(final_path)
        except Exception as e:
            # cleanup tmp + final
            try:
                tmp_path.unlink()
            except Exception:
                pass
            try:
                if final_path.exists():
                    final_path.unlink()
            except Exception:
                pass
            raise RuntimeError(f"Failed to process image: {e}") from e

        # remove temp file
        try:
            if tmp_path.exists():
                tmp_path.unlink()
        except Exception:
            pass

        # build and return relative path for DB (relative to /static)
        app = current_app._get_current_object()
        uploads_dir = app.config.get('UPLOADS_DIR', 'uploads')

        # We expect target_dir to be like: <app.static_folder>/<uploads_dir>/mangas/<manga_dir> (or similar)
        # To compute relative path, find the path segments after app.static_folder
        try:
            rel = final_path.relative_to(Path(app.static_folder))
            rel_str = str(rel).replace("\\", "/")  # normalize windows path separators
        except Exception:
            # fallback to building from uploads_dir and last parts
            rel_str = os.path.join(uploads_dir, target_dir.name, safe_name).replace("\\", "/")

        return rel_str

    except Exception:
        # cleanup anything partial
        try:
            if tmp_path.exists():
                tmp_path.unlink()
        except Exception:
            pass
        try:
            if final_path.exists():
                final_path.unlink()
        except Exception:
            pass
        raise


def save_and_verify_images(files: List,
                           manga_dirname: str,
                           chapter_dirname: str) -> Tuple[List[str], List[str]]:
    """
    Save uploaded files (werkzeug FileStorage) safely:
    - Save to a temp dir first
    - Verify each file is an image using Pillow (Image.verify)
    - Move/save to final dir under app.static_folder / UPLOADS_DIR / mangas / manga_dirname / chapter_dirname

    Returns:
    - relative_paths: list of relative paths to store in DB (e.g. 'uploads/mangas/.../001.jpg')
    - absolute_paths: list of absolute final file paths (for debugging/cleanup if needed)

    On failure, raises Exception (caller should handle cleanup). This function attempts cleanup
    of partial files on error.
    """
    app = current_app._get_current_object()
    uploads_dir = app.config.get('UPLOADS_DIR', 'uploads')
    final_dir = Path(app.static_folder) / uploads_dir / 'mangas' / manga_dirname / chapter_dirname
    final_dir.mkdir(parents=True, exist_ok=True)

    tmp_dir = Path(tempfile.mkdtemp(prefix='manga_upload_'))
    saved_final_paths: List[str] = []
    relative_paths: List[str] = []

    try:
        page_index = 1
        for f in files:
            filename = getattr(f, 'filename', None)
            if not filename or not allowed_file(filename):
                raise ValueError(f"Invalid file or extension: {filename}")

            ext = filename.rsplit('.', 1)[-1].lower()
            tmp_path = tmp_dir / f"{uuid.uuid4().hex}.{ext}"
            f.save(str(tmp_path))

            # verify using Pillow
            try:
                with Image.open(tmp_path) as im:
                    im.verify()
            except (UnidentifiedImageError, OSError) as e:
                raise ValueError(f"Uploaded file is not a valid image: {filename}") from e

            # re-open and save to final to normalize
            final_name = f"{page_index:03d}.{ext}"
            final_path = final_dir / final_name
            try:
                with Image.open(tmp_path) as im:
                    im.save(final_path)
            except Exception as e:
                raise RuntimeError(f"Failed to save processed image {filename}: {e}") from e

            rel_path = os.path.join(uploads_dir, 'mangas', manga_dirname, chapter_dirname, final_name)
            relative_paths.append(rel_path.replace("\\", "/"))
            saved_final_paths.append(str(final_path))
            page_index += 1

        # cleanup tmp dir
        shutil.rmtree(tmp_dir, ignore_errors=True)
        return relative_paths, saved_final_paths

    except Exception:
        # remove any final files saved so far
        for p in saved_final_paths:
            try:
                os.remove(p)
            except Exception:
                pass
        # remove temp dir
        try:
            shutil.rmtree(tmp_dir, ignore_errors=True)
        except Exception:
            pass
        # if final_dir exists and is empty try remove it (best-effort)
        try:
            if final_dir.exists() and not any(final_dir.iterdir()):
                final_dir.rmdir()
        except Exception:
            pass
        # re-raise so caller can decide what to do
        raise


def save_profile_picture(file_storage, username: str) -> str:
    """
    Save and verify a user's profile picture.

    - file_storage: werkzeug FileStorage object
    - username: desired username (used for filename). Will be sanitized.

    Returns: relative path to saved profile picture (e.g. 'uploads/profile_pic/arpit.png')
    Raises: ValueError or RuntimeError on errors.
    """
    if not file_storage or not getattr(file_storage, 'filename', None):
        raise ValueError("No profile picture provided.")

    # determine uploads base and profile dir
    app = current_app._get_current_object()
    uploads_dir = app.config.get('UPLOADS_DIR', 'uploads')
    profile_subdir = app.config.get('PROFILE_PICS_DIR', os.path.join(uploads_dir, 'profile_pic'))
    # profile_subdir may be relative (uploads/profile_pic) - make absolute under static_folder
    if os.path.isabs(profile_subdir):
        target_dir = Path(profile_subdir)
    else:
        target_dir = Path(app.static_folder) / profile_subdir

    # ensure sanitized base filename uses username (fallback to uuid)
    safe_base = secure_filename(username) or uuid.uuid4().hex

    rel_path = save_single_image(file_storage, target_dir, safe_base)
    # save_single_image returns a path relative to static folder (or fallback construction)
    return rel_path
