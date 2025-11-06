import os
from werkzeug.utils import secure_filename

def generate_manga_cover_filename(manga_title, manga_id, author_id, author_name, original_filename):
    """Generate unique cover filename to prevent conflicts."""
    ext = os.path.splitext(original_filename)[1]
    safe_title = secure_filename(manga_title).replace(" ", "_")
    safe_author = secure_filename(author_name).replace(" ", "_")
    filename = f"{safe_title}_{manga_id}_{author_id}_{safe_author}{ext}"
    return filename

def get_manga_folder_path(manga_title, manga_id, author_id):
    """Return the full folder path for this manga, and create it if needed."""
    safe_title = secure_filename(manga_title).replace(" ", "_")
    folder_name = f"{safe_title}_{manga_id}_{author_id}"
    from flask import current_app
    folder_path = os.path.join(current_app.config['MANGA_FOLDER'], folder_name)
    os.makedirs(folder_path, exist_ok=True)
    return folder_path