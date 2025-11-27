from flask import Blueprint, render_template, abort
from ..extensions import db
from ..models import Product

product_bp = Blueprint("products", __name__, url_prefix="/products")

# PUBLIC PRODUCT LISTING (on index, so no login)
@product_bp.route("/<int:product_id>")
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template("product_detail.html", product=product)