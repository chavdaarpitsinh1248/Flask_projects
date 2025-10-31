from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FileField, SubmitField
from wtforms.validators import DataRequired, Length

class MangaForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(min=5, max=150)])
    description = TextAreaField('Description', validators=[Length(max=1000)])
    cover_image = FileField('Cover Image (optional)')
    submit = SubmitField('Add Manga')
