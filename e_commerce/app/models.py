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
