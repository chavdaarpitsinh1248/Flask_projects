
from flask import Blueprint

admin_bp = Blueprint('admin', __name__, template_folder='../../templates/admin', static_folder='../../static')

from . import routes  # noqa: F401
