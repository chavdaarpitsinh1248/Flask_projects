from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime
from .. import db
from ..models import StudioRequest, Notification, User

user_bp = Blueprint('user', __name__)

