from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FloatField, IntegerField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange

class AddProductForm(FlaskForm):
    name = StringField("Product Name", validators=[DataRequired(), Length(min=3, max=50)])
    description = TextAreaField("Description", validators=[DataRequired()])
    price = FloatField("Price", validators=[DataRequired(), NumberRange(min=1)])
    stock = IntegerField("Stock Quantity", validators=[DataRequired(), NumberRange(min=0)])
    submit = SubmitField("Add Product")