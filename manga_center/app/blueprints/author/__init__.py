
from flask import Blueprint

author_bp = Blueprint('author', __name__, template_folder='../../templates/author', static_folder='../../static')

from . import routes  # noqa: F401
