
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, FileField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Optional

class AddMangaForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[Optional()])
    cover_image = FileField('Cover image (optional)')
    submit = SubmitField('Create Manga')

class AddChapterForm(FlaskForm):
    number = IntegerField('Chapter number', validators=[DataRequired()])
    title = StringField('Chapter title (optional)', validators=[Optional()])
    pages = FileField('Pages (multiple images)')  # client should use <input multiple>
    submit = SubmitField('Add Chapter')
