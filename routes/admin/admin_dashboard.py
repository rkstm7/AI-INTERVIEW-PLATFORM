from flask import Blueprint, render_template, flash, redirect, url_for
from flask_login import login_required, current_user
from utils.db import get_db_connection as get_db
from datetime import datetime, timedelta

admin_dashboard_bp = Blueprint('admin_dashboard', __name__, url_prefix='/admin')


@admin_dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    # Only Admin can access
    if not getattr(current_user, 'role_obj', None) or current_user.role_obj.role_name != "Admin":
        flash("Access denied!", "danger")
        return redirect(url_for('admin_login.login'))

    conn = get_db()
    try:
        with conn.cursor() as cursor:
            # Total users
            cursor.execute("SELECT COUNT(*) AS total FROM users")
            total_users_row = cursor.fetchone()
            total_users = total_users_row['total'] if total_users_row else 0

            # Active users: last_active within last 10 minutes
            ten_minutes_ago = datetime.utcnow() - timedelta(minutes=10)
            ten_minutes_ago_str = ten_minutes_ago.strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute(
                "SELECT COUNT(*) AS active FROM users WHERE last_active >= %s", 
                (ten_minutes_ago_str,)
            )
            active_users_row = cursor.fetchone()
            active_users = active_users_row['active'] if active_users_row else 0

            active_sessions = active_users
            offline_users = total_users - active_users

            # Total job roles
            cursor.execute("SELECT COUNT(*) AS total FROM job_roles")
            total_job_roles_row = cursor.fetchone()
            total_job_roles = total_job_roles_row['total'] if total_job_roles_row else 0

    finally:
        conn.close()

    return render_template(
        'admin/dashboard/admin_dashboard.html',
        total_users=total_users,
        active_users=active_users,
        active_sessions=active_sessions,
        offline_users=offline_users,
        total_job_roles=total_job_roles,
        user=current_user
    )
