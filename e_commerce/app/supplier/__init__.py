from flask import Blueprint

supplier_bp = Blueprint("supplier", __name__, url_prefix="/supplier")

from . import routes