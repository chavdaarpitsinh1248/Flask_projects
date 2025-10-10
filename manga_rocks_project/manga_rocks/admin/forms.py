import os
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FileField, SelectMultipleField, IntegerField, SubmitField
from wtforms.validators import DataRequired, Length, Optional
from werkzeug.utils import secure_filename

class AddMangaForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=150)])
    author = StringField("Author", validators=[Optional(), Length(max=100)])
    description = TextAreaField("Description", validators=[Optional()])
    cover_image = FileField("Cover Image (optional)")
    genres = SelectMultipleField("Genres (Ctrl + Click to select multiple)", coerce=int)
    submit = SubmitField("Add Manga")

class AddChapterForm(FlaskForm):
    manga_id = IntegerField("Manga ID", validators=[DataRequired()])
    number = IntegerField("Chapter Number", validators=[DataRequired()])
    title = StringField("Chapter Title", validators=[Optional(), Length(max=150)])
    submit = SubmitField("Add Chapter")

class UploadPagesForm(FlaskForm):
    chapter_id = IntegerField("Chapter ID", validators=[DataRequired()])
    pages = FileField("Upload Pages (multiple)", render_kw={"multiple":True})
    submit = SubmitField("Upload Pages")