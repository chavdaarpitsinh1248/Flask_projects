# app/blueprints/manga/__init__.py
from flask import Blueprint

manga_bp = Blueprint('manga', __name__, template_folder='../../templates/manga', static_folder='../../static')

from . import routes  # noqa: F401
