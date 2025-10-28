from flask import url_for
import os

def chapter_page_urls(chapter):
    """
    Given a Chapter model instance, return a list of page URL strings
    suitable for putting directly into <img src="{{ page }}">.
    Expects Page.image to be either:
      - an absolute URL (http/https) -> returned as-is
      - or a path relative to static/ (e.g. "uploads/5/1/1.jpg" or "/uploads/...")
    """
    pages = []
    # ensure pages are ordered by page_number
    ordered = sorted(getattr(chapter, 'pages', []) or [], key=lambda p: (p.page_number or 0))
    for p in ordered:
        if not getattr(p, 'image', None):
            continue
        img = p.image
        if img.startswith('http://') or img.startswith('https://'):
            pages.append(img)
            continue
        # normalize relative path (remove leading slash/backslash)
        rel = img.lstrip('/\\')
        pages.append(url_for('static', filename=rel))
    return pages
