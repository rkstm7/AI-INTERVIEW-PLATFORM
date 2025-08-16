from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email
from forms.email_validation import universal_email_validator
from forms.password_validation import strong_password 


class SimpleLoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email(), universal_email_validator])
    password = PasswordField("Password", validators=[DataRequired(), strong_password])
    submit = SubmitField("Login")
