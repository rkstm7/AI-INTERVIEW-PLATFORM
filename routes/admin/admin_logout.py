# routes/admin/auth/admin_logout.py
from flask import Blueprint, redirect, url_for, flash
from flask_login import logout_user, login_required

admin_logout_bp = Blueprint('admin_logout', __name__, url_prefix='/admin')

@admin_logout_bp.route('/logout', methods=['GET'])
@login_required
def logout():
    """Logs out the currently logged-in admin user."""
    logout_user()
    flash("You have been logged out successfully.", "success")
    return redirect(url_for('public_dashboard.dashboard'))
