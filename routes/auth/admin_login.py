# routes/admin/auth/admin_login.py

from flask import render_template, redirect, url_for, flash, session
from flask_login import current_user, login_user, UserMixin
from forms.admin_login_form import SimpleLoginForm
from models.model import db, User, Role
from extensions import bcrypt
from flask import Blueprint
from functools import wraps

admin_login_bp = Blueprint('admin_login', __name__, url_prefix='/admin')


# ---------------- Temporary AdminUser class ----------------
class AdminUser(UserMixin):
    """A temporary user object for Flask-Login sessions for admin users."""

    def __init__(self, id, name, email, role="Admin"):
        self.id = id
        self.name = name
        self.email = email
        self.role = role

    def get_id(self):
        return str(self.id)


# ---------------- Admin login decorator ----------------
def admin_login_required(f):
    """Protect admin-only routes using session check."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            flash('Admin login required.', 'error')
            return redirect(url_for('admin_login.login'))
        return f(*args, **kwargs)
    return decorated_function


# ---------------- Admin login route ----------------
@admin_login_bp.route('/login', methods=['GET', 'POST'])
def login():
    # Redirect if already logged in as Admin
    if current_user.is_authenticated and getattr(current_user, 'role', None) == "Admin":
        return redirect(url_for('admin_dashboard.dashboard'))

    form = SimpleLoginForm()

    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        # Fetch admin user via relationship
        admin = (
            db.session.query(User)
            .join(Role)
            .filter(User.email == email, Role.id == User.role_id, Role.role_name == 'Admin')
            .first()
        )

        if admin and bcrypt.check_password_hash(admin.password, password):
            # Create temporary Flask-Login session object
            admin_user = AdminUser(
                id=admin.id,
                name=admin.name,
                email=admin.email,
                role=admin.role_obj.role_name
            )

            login_user(admin_user, remember=True)
            session['admin_logged_in'] = True

            flash("Admin logged in successfully.", "success")
            return redirect(url_for('admin_dashboard.dashboard'))
        else:
            flash("Invalid admin credentials.", "danger")

    return render_template(
        'public/login/admin_login.html',
        form=form
    )
