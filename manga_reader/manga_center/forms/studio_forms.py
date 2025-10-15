from flask_wtf import FlaskForm
from wtforms import SubmitField

class StudioRequestForm(FlaskForm):
    submit = SubmitField("Request Studio Role")