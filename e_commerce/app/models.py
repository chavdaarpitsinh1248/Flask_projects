from datetime import datetime
from enum import Enum 
from flask_login import UserMixin
from sqlalchemy.orm import relationship
from .extensions import db
from decimal import Decimal 



# ---------------------------------------------------
# ROLE ENUM
# ---------------------------------------------------
class RoleEnum(str, Enum):
    ADMIN = "admin"
    CUSTOMER = "customer"
    SUPPILER = "supplier"
    IN_STAFF = "in_staff"       # warehouse guy
    DRIVER = "driver"           # delivery guy



# ---------------------------------------------------
# USER MODEL
# ---------------------------------------------------
class User(db.Model, UserMixin):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    role = db.Column(db.Enum(RoleEnum), default=RoleEnum.CUSTOMER, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Supplier -> products
    products = db.relationship("Product", backref="supplier", lazy="dynamic")

    # Customer -> orders
    orders = db.relationship("Order", backref="customer", lazy="dynamic")

    def __repr__(self):
        return f"<User {self.id} {self.email} {self.role}>"


# ---------------------------------------------------
# PRODUCT MODEL
# ---------------------------------------------------
class Product(db.Model):
    __tablename__ = "product"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    discount_percent = db.Column(db.Integer, default=0)
    stock = db.Column(db.Integer, default=0)

    supplier_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Product -> order items
    order_items = db.relationship("OrderItem", backref="product", lazy="dynamic")

    # Product -> customer questions
    questions = db.relationship("Question", backref="product", lazy="dynamic")

    def discounted_price(self):
        """Price after discount"""
        return Decimal(self.price) * (1 - (self.discount_percent or 0)/ 100)

    def __repr__(self):
        return f"<Product {self.id} {self.title}>"


# ---------------------------------------------------
# DELIVERY ADDRESS
# ---------------------------------------------------
class Address(db.Model):
    __tablename__ = "address"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    name = db.Column(db.String(120))
    street = db.Column(db.String(255))
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    postal_code = db.Column(db.String(50))
    country = db.Column(db.String(120))
    phone = db.Column(db.String(50))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref="addresses")

    def full_address(self):
        """Helper to print full address cleanly"""
        return f"{self.street}, {self.city}, {self.state}, {self.country} - {self.postal_code}"
    
    def __repr__(self):
        return f"<Address {self.id} User={self.user_id}>"


# ---------------------------------------------------
# ORDER MODEL
# ---------------------------------------------------
class Order(db.Model):
    __tablename__ = "order"

    id = db.Column(db.Integer, primary_key=True)

    customer_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    address_id = db.Column(db.Integer, db.ForeignKey("address.id"), nullable=False)

    # delivery assignment (for drivers)
    driver_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)

    # status flow
    status = db.Column(
        db.String(50),
        default="pending" 
        # possible values: pending, paid, processing, shipped, delivered, cancelled
    )

    # price
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    paid_at = db.Column(db.DateTime, nullable=True)

    # invoice number
    invoice_number = db.Column(db.String(64), unique=True, nullable=True)

    # Relationship
    items = db.relationship("OrderItem", backref="order", lazy="dynamic")
    address = db.relationship("Address")

    # driver relation
    driver = db.relationship("User", foreign_keys=[driver_id])

    def __repr__(self):
        return f"<Order {self.id} Customer={self.customer_id} Status={self.status}>"


# ---------------------------------------------------
# ORDER ITEM MODEL
# ---------------------------------------------------
class OrderItem(db.Model):
    __tablename__ = "order_item"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("order.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)

    quantity = db.Column(db.Integer,default=1)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)  # price at purchase time

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def subtotal(self):
        return Decimal(self.unit_price) * self.quantity
    
    def __repr__(self):
        return f"<OrderItem {self.id} Product={self.product_id}>"


# ---------------------------------------------------
# PRODUCT QUESTIONS & ANSWER
# ---------------------------------------------------
class Question(db.Model):
    __tablename__ = "question"

    id = db.Column(db.Integer, primary_key=True)

    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    question_text = db.Column(db.Text, nullable=False)
    answer_text = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    answered_at = db.Column(db.DateTime, nullable=True)

    user = db.relationship("User")

    def __repr__(self):
        return f"<question {self.id} Product={self.product_id} User={self.user_id}>"
