from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FloatField, SelectField, DateField, TextAreaField
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


# -----------------------------
#   Expense Form
# -----------------------------
class ExpenseForm(FlaskForm):
    amount = FloatField("Amount", validators=[DataRequired()])
    category = SelectField(
        "Category",
        choices=[
            ("food", "Food"),
            ("travel", "Travel"),
            ("shopping", "Shopping"),
            ("bills", "Bills"),
            ("health", "Health"),
            ("other", "Other"),
        ],
        validators=[DataRequired()],
    )
    date = DateField("Date", validators=[DataRequired()])
    note = TextAreaField("Note")
    submit = SubmitField("Save")