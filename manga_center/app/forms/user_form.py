from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FileField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError
from flask_login import current_user
from app.models import User

class ProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=50)])
    password = PasswordField('New Password')
    confirm_password = PasswordField('Confirm Password', validators=[EqualTo('password', message='Passwords must match')])
    profile_pic = FileField('Profile Picture')
    submit = SubmitField('Update Profile')

    def validate_username(self, username):
        if username.data != current_user.username:
            existing_user = User.query.filter_by(username=username.data).first()
            if existing_user:
                raise ValidationError('This username is already taken. Please choose another one.')


class AuthorRequestForm(FlaskForm):
    message = StringField('Why do you want to be an Author?', validators=[Length(max=500)])
    submit = SubmitField('Submit Request')