# routes/user/user_dashboard.py
from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from models.model import Role, JobRole, Notice, LearningResource

user_dashboard_bp = Blueprint("user_dashboard", __name__, url_prefix="/user")


@user_dashboard_bp.route("/dashboard", methods=["GET"])
@login_required
def dashboard():
    """
    User Dashboard:
    - Ensures only users with role 'user' can access.
    - Displays job roles, notices, and learning resources filtered by selected role.
    """
    # Fetch current user's role
    user_role = Role.query.get(current_user.role_id)
    if not user_role or user_role.role_name.lower() != "user":
        flash("Access denied! Only users can access the dashboard.", "danger")
        return redirect(url_for("user_login.login"))

    # Fetch all job roles, ordered alphabetically
    job_roles = JobRole.query.order_by(JobRole.name).all()

    # Fetch all notices, latest first
    notices = Notice.query.order_by(Notice.created_at.desc()).all()

    # Get selected role from query parameters (optional)
    selected_role_id = request.args.get("role_id", type=int)
    selected_role_name = None
    resources = []

    if selected_role_id:
        role = JobRole.query.get(selected_role_id)
        if role:
            selected_role_name = role.name
            # Fetch resources for the selected job role, latest first
            resources = (
                LearningResource.query.filter_by(job_role_id=selected_role_id)
                .order_by(LearningResource.created_at.desc())
                .all()
            )

    # Optional upload messages from query string
    upload_success = request.args.get("upload_success")
    upload_error = request.args.get("upload_error")

    return render_template(
        "user/dashboard/user_dashboard.html",
        user=current_user,
        user_role=user_role,
        job_roles=job_roles,
        selected_role_id=selected_role_id,
        selected_role_name=selected_role_name,
        resources=resources,
        notices=notices,
        upload_success=upload_success,
        upload_error=upload_error,
    )
