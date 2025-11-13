# app/forms/comment_form.py

from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField, HiddenField
from wtforms.validators import DataRequired, Length

class CommentForm(FlaskForm):
    chapter_id = HiddenField("Chapter ID")  # to store which chapter this comment belongs to
    content = TextAreaField(
        "Content",
        validators=[
            DataRequired(message="Please write a comment before submitting."),
            Length(min=1, max=500, message="Comment must be between 1 and 500 characters.")
        ]
    )
    submit = SubmitField("Post Comment")
