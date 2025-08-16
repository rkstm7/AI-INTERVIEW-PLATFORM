# routes/user/notice.py
from flask import Blueprint, render_template
from flask_login import login_required
from utils.db import get_db_connection as get_db
from datetime import datetime

notice_bp = Blueprint('notice', __name__, url_prefix='/user')


# Template filter to format datetime
@notice_bp.app_template_filter('format_datetime')
def format_datetime(value, format='%b %d, %Y'):
    if value is None:
        return ""
    if isinstance(value, str):
        try:
            dt = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')  # adjust to your DB format
            return dt.strftime(format)
        except Exception:
            return value  # fallback if parsing fails
    elif hasattr(value, 'strftime'):
        return value.strftime(format)
    return value


# Route: View Notices
@notice_bp.route('/notice')
@login_required
def user_notice():
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM notice ORDER BY created_at DESC")
            notices = cursor.fetchall()
    finally:
        conn.close()

    return render_template('user/notice/notice.html', notices=notices)
