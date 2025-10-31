from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, EmailField
from wtforms.validators import DataRequired, Email, Length

class AddAuthorForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(min=5, max=25)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    pen_name = StringField("Pen Name", validators=[DataRequired(), Length(min=5, max=25)])
    bio = TextAreaField("Bio", validators=[Length(max=300)])
    submit = SubmitField("Add Author")