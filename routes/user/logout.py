# routes/user/logout.py
from flask import Blueprint, redirect, url_for, flash
from flask_login import logout_user, login_required

user_logout_bp = Blueprint('user_logout', __name__, url_prefix='/user')

@user_logout_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You have been logged out successfully.", "success")
    return redirect(url_for('public_dashboard.dashboard'))  # redirect to public dashboard
