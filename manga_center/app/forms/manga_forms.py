from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FileField, SubmitField, IntegerField, MultipleFileField
from wtforms.validators import DataRequired, Length, NumberRange

class MangaForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(min=5, max=150)])
    description = TextAreaField('Description', validators=[Length(max=1000)])
    cover_image = FileField('Cover Image (optional)')
    submit = SubmitField('Add Manga')

class ChapterForm(FlaskForm):
    title = StringField("Chapter Title", validators=[DataRequired()])
    number = IntegerField("Chapter Number", validators=[DataRequired(), NumberRange(min=1)])
    content = MultipleFileField("Upload Chapter (ZIP or Images)", validators=[DataRequired()])
    submit = SubmitField("Add Chapter")