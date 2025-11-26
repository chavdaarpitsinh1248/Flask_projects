from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Product, User
from . import supplier_bp
from .utils import supplier_required
from .forms import AddProductForm

@supplier_bp.route('/')
@login_required
@supplier_required
def dashboard():
    total_products = Product.query.filter_by(supplier_id=current_user.id).count()
    total_stock = db.session.query(db.func.sum(Product.stock)).filter(Product.supplier_id == current_user.id).scalar() or 0
    total_sales = db.session.query(db.func.sum(Product.sold)).filter(Product.supplier_id == current_user.id).scalar() or 0

    return render_template('supplier/dashboard.html',
                            total_products=total_products,
                            total_stock=total_stock,
                            total_sales=total_sales)


@supplier_bp.route('/add', methods=["GET", "POST"])
@login_required
@supplier_required
def add_product():
    form = AddProductForm()
    if form.validate_on_submit():
        product = Product(
            supplier_id=current_user.id,
            name=form.name.data,
            description=form.description.data,
            price=form.price.data,
            stock=form.stock.data
        )
        db.session.add(product)
        db.session.commit()

        flash("Product added successfully!", "success")
        return redirect(url_for('supplier.my_products'))

    return render_template('supplier/add_product.html', form=form)


@supplier_bp.route('/my-products')
@login_required
@supplier_required
def my_products():
    products = Product.query.filter_by(supplier_id=current_user.id).all()
    return render_template('supplier/my_products.html', products=products)


@supplier_bp.route('/edit/<int:product_id>', methods=['GET', 'POST'])
@login_required
@supplier_required
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)

    if product.supplier_id != current_user.id:
        abort(403)
    
    form = AddProductForm(
        name=product.name,
        description=product.description,
        price=product.price,
        stock=product.stock
    )

    if request.method == "POST" and form.validate_on_submit():
        product.name = form.name.data
        product.description = form.description.data
        product.price = form.price.data
        product.stock = form.stock.data

        db.session.commit()
        flash("Product updated!", "success")
        return redirect(url_for('supplier.my_products'))
    
    return render_template('supplier/edit_product.html', form=form, product=product)


@supplier_bp.route('/stock')
@login_required
@supplier_required
def stock():
    products = Product.queery.filter_by(supplier_id=current_user.id).all()
    return render_template('supplier/stock.html', products=products)


@supplier_bp.route('/sales')
@login_required
@supplier_required
def sales():
    products = Product.queery.filter_by(supplier_id=current_user.id).all()
    return render_template('supplier/sales.html', products=products)