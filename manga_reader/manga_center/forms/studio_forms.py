from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField, TextAreaField, FileField, IntegerField
from wtforms.validators import DataRequired

class StudioRequestForm(FlaskForm):
    submit = SubmitField("Request Studio Role")

class MangaForm(FlaskForm):
    title = StringField('Manga Title', validators=[DataRequired()])
    description = TextAreaField('Description')
    cover_image = FileField('Cover Image')
    submit = SubmitField('Create Manga')

class ChapterForm(FlaskForm):
    number = IntegerField('Chapter Number', validators=[DataRequired()])
    title = StringField('Chapter Title')
    submit = SubmitField('Add Chapter')