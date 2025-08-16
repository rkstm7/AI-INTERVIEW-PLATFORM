import re
from wtforms.validators import ValidationError

def strong_password(form, field):
    """
    Validates that the password contains at least:
    - 8 characters
    - 1 uppercase
    - 1 lowercase
    - 1 digit
    - 1 special character
    """
    password = field.data

    if len(password) < 8:
        raise ValidationError("Password must be at least 8 characters long.")

    if not re.search(r"[A-Z]", password):
        raise ValidationError("Password must contain at least one uppercase letter.")

    if not re.search(r"[a-z]", password):
        raise ValidationError("Password must contain at least one lowercase letter.")

    if not re.search(r"[0-9]", password):
        raise ValidationError("Password must contain at least one number.")

    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        raise ValidationError("Password must contain at least one special character.")
