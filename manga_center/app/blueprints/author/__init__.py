
from flask import Blueprint

# Point the author blueprint to the 'templates/manga' folder.
# Author-specific templates will live under templates/manga/author/
author_bp = Blueprint('author', __name__, template_folder='../../templates/manga', static_folder='../../static')

from . import routes  # noqa: F401
