from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired, EqualTo, ValidationError, Regexp
from utils.db import get_db_connection  # DB connection helper
from .email_validation import universal_email_validator  # custom email validator
from forms.password_validation import strong_password  # custom password validator


class RegisterForm(FlaskForm):
    """
    User Registration Form with validation for:
    - Required fields
    - Unique username & email
    - Strong password
    - Valid phone format
    - Role selection
    """

    name = StringField(
        "Full Name", validators=[DataRequired(message="Full name is required.")]
    )

    username = StringField(
        "Username", validators=[DataRequired(message="Username is required.")]
    )

    email = StringField(
        "Email",
        validators=[
            DataRequired(message="Email is required."),
            universal_email_validator,
        ],
    )

    phone = StringField(
        "Phone",
        validators=[
            DataRequired(message="Phone number is required."),
            Regexp(r"^[6-9]\d{9}$", message="Enter a valid 10-digit phone number."),
        ],
    )

    address = StringField(
        "Address", validators=[DataRequired(message="Address is required.")]
    )

    password = PasswordField(
        "Password",
        validators=[
            DataRequired(message="Password is required."),
            strong_password,
        ],
    )

    verify_password = PasswordField(
        "Verify Password",
        validators=[
            DataRequired(message="Please confirm your password."),
            EqualTo("password", message="Passwords must match."),
        ],
    )

    submit = SubmitField("Register")

    def validate_email(self, field):
        """
        Checks if the email already exists (case-insensitive).
        """
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT 1 FROM users WHERE LOWER(email) = LOWER(%s)", (field.data,)
            )
            if cursor.fetchone():
                raise ValidationError("Email already registered.")
        finally:
            conn.close()

    def validate_username(self, field):
        """
        Checks if the username already exists (case-insensitive).
        """
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT 1 FROM users WHERE LOWER(username) = LOWER(%s)", (field.data,)
            )
            if cursor.fetchone():
                raise ValidationError("Username already taken.")
        finally:
            conn.close()
