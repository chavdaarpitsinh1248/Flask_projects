import os

def ensure_manga_folder(app, manga):
    """
        Ensure that a dedicated folder exists for a specific manga to store its chapters.
        Path: static/uploads/manga/<manga_title>_<manga_id>_<author_id>/
    """
    base_folder = os.path.join(app.root_path, 'static', 'uploads', 'manga')
    folder_name = f"{manga.title}_{manga.id}_{manga.author_id}"
    manga_folder = os.path.join(base_folder, folder_name)

    if not os.path.exists(manga_folder):
        os.makedirs(manga_folder)

    return manga_folder