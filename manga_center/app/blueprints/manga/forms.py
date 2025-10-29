
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, SelectMultipleField
from wtforms.validators import DataRequired, Optional

class MangaSearchForm(FlaskForm):
    q = StringField('Search', validators=[Optional()])
    submit = SubmitField('Search')

class MangaForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[Optional()])
    genres = SelectMultipleField('Genres', coerce=int, validators=[Optional()])
    tags = StringField('Tags (comma separated)', validators=[Optional()])
    submit = SubmitField('Save')
