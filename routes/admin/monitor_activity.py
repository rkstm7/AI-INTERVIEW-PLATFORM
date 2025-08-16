# routes/admin/monitor_activity.py
from flask import Blueprint, render_template, flash, redirect, url_for, request
from flask_login import login_required, current_user
from models.model import UserActivity, User, Role
from datetime import datetime

monitor_activity_bp = Blueprint("monitor_activity", __name__, url_prefix="/admin")


@monitor_activity_bp.route("/activity")
@login_required
def activity():
    # Restrict access to Admin role
    user_role = (
        Role.query.join(User, User.role_id == Role.id)
        .filter(User.id == current_user.id)
        .with_entities(Role.role_name)
        .scalar()
    )

    if not user_role or user_role.lower() != "admin":
        flash("Access denied! Admins only.", "danger")
        return redirect(url_for("index"))

    # Get search filters
    search_user_id = request.args.get("user_id", "").strip()
    search_name = request.args.get("name", "").strip()

    # Base query
    query = UserActivity.query.join(User, UserActivity.user_id == User.id).add_columns(
        UserActivity.user_id,
        User.name,
        UserActivity.activity_type,
        UserActivity.timestamp,
        UserActivity.ip_address,
        UserActivity.user_agent,
    )

    # Apply filters if provided
    if search_user_id:
        query = query.filter(UserActivity.user_id.like(f"%{search_user_id}%"))
    if search_name:
        query = query.filter(User.name.ilike(f"%{search_name}%"))

    raw_activities = query.order_by(UserActivity.timestamp.desc()).all()

    # Format data for template
    activities = []
    for a in raw_activities:
        ts = a[4]  # timestamp is at index 4 in raw_activities
        if isinstance(ts, datetime):
            ts_str = ts.strftime("%d-%m-%Y %I:%M %p")
        else:
            ts_str = str(ts) if ts else ""

        activities.append(
            (
                a[1],  # user_id
                a[2],  # name
                a[3],  # activity
                ts_str,  # formatted timestamp
                a[5],  # IP address
                a[6],  # User agent
            )
        )

    return render_template(
        "admin/activity/monitor_activity.html", activities=activities
    )
