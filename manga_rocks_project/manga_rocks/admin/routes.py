from flask import Blueprint

admin_bp = Blueprint("admin", __name__)

@admin_bp.route("/")
def admin_index():
    return "Admin_index -- step 4"