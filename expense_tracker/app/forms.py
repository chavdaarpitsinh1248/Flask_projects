from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo

# -----------------------------
#   Signup Form
# -----------------------------
class SignupForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(min=3, max=50)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[
        DataRequired(),
        Length(min=5, message="Password must be at least 5 characters."),
        EqualTo("confirm", message="Passwords must match.")
    ])
    confirm = PasswordField("Confirm Password")
    submit = SubmitField("Create Account")


# -----------------------------
#   Login Form
# -----------------------------
class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")