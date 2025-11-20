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
    password_hash = db.Column(db.string(256), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    role = db.Column(db.Enum(RoleEnum), default=RoleEnum.CUSTOMER, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Supplier -> products
    products = db.relationship("Product", backref="supplier", lazy="dynamic")

    # Customer -> orders
    orders = db.relationship("Order", backref="customer", lazy="dynamic")

    def __repr__(self):
        return f"<User {self.id} {self.email} {self.role}>"

