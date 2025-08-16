import re
from wtforms.validators import ValidationError

def universal_email_validator(_, field):
    """
    Validates email addresses with the following rules:
    - Must be a valid format
    - Only allowed domains
    - Block disposable emails
    - Username cannot contain consecutive special characters or TLD-like patterns
    - Prevent starting/ending with special characters
    - Username cannot be numbers only
    """

    email = field.data.strip()

    # Allowed domains
    allowed_domains = [
        'gmail.com', 'yahoo.com', 'outlook.com', 'bvucoep.edu.in',
        'gov.in', 'ac.in', 'edu.in', 'org.in'
    ]

    # Disposable domains to block
    disposable_domains = [
        'tempmail.com', '10minutemail.com', 'mailinator.com',
        'guerrillamail.com', 'fakeinbox.com'
    ]

    # General email format regex
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        raise ValidationError('Enter a valid email address (e.g., johndoe@example.com).')

    # Extract username and domain
    try:
        username, domain_part = email.split('@')
    except ValueError:
        raise ValidationError('Invalid email structure.')

    domain_lower = domain_part.lower()

    # Check allowed domain
    if domain_lower not in allowed_domains:
        raise ValidationError(f'Only emails from {", ".join(allowed_domains)} are allowed.')

    # Check disposable domain
    if domain_lower in disposable_domains:
        raise ValidationError('Disposable email addresses are not allowed.')

    # Prevent invalid domain format
    if '..' in domain_lower or any(not part.isalnum() for part in domain_lower.split('.') if part):
        raise ValidationError('Email domain contains invalid characters or format.')

    # TLD check
    tld = domain_lower.split('.')[-1]
    if not tld.isalpha() or len(tld) < 2:
        raise ValidationError('Email domain extension is invalid (e.g., .com, .org, .in).')

    # Prevent TLD-like patterns in username
    forbidden_exts = ['.com', '.in', '.org', '.net', '.edu']
    if any(ext in username for ext in forbidden_exts):
        raise ValidationError('Email username cannot contain domain-like extensions (e.g., .com, .in).')

    # Consecutive special characters
    if '..' in username or '--' in username or '__' in username:
        raise ValidationError('Username cannot contain consecutive special characters.')

    # Start/end special character check
    if username[0] in '._-' or username[-1] in '._-':
        raise ValidationError('Username cannot start or end with special characters.')

    # Username numeric only
    if username.isdigit():
        raise ValidationError('Username cannot be numbers only.')

    # Length check
    if len(email) > 254 or len(username) < 3:
        raise ValidationError('Email is too long or username is too short.')
