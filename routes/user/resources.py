from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from utils.db import get_db_connection

user_resources_bp = Blueprint("user_resources", __name__, url_prefix="/user")


@user_resources_bp.route("/resources")
@login_required
def resources():
    conn = get_db_connection()
    cursor = (
        conn.cursor()
    )  # no 'dictionary=True', assume get_db_connection returns dict cursor
    job_roles = []

    try:
        # Fetch all active job roles
        cursor.execute(
            "SELECT id, name FROM job_roles WHERE status='Active' ORDER BY name"
        )
        job_roles = cursor.fetchall()  # list of dicts: {'id': 1, 'name': 'Developer'}

        selected_role_id = request.args.get("role_id", type=int)
        action = request.args.get("action", default="resources")
        selected_role_name = None
        resources = []

        if selected_role_id:
            # Get role name
            cursor.execute(
                "SELECT name FROM job_roles WHERE id = %s", (selected_role_id,)
            )
            role = cursor.fetchone()
            if role:
                selected_role_name = role["name"]  # use dict key

                if action == "resources":
                    # Fetch all resources for this role
                    cursor.execute(
                        """
                        SELECT title, description, url, created_at
                        FROM learning_resources
                        WHERE job_role_id = %s
                        ORDER BY created_at DESC
                    """,
                        (selected_role_id,),
                    )
                    resources = cursor.fetchall()  # list of dicts

                elif action == "qa":
                    return redirect(
                        url_for("user_resources.ques_ans", role_id=selected_role_id)
                    )
            else:
                flash("Selected job role not found.", "warning")

    finally:
        conn.close()

    return render_template(
        "user/resources/resources.html",
        job_roles=job_roles,
        resources=resources,
        selected_role_id=selected_role_id,
        selected_role_name=selected_role_name,
        action=action,
    )


@user_resources_bp.route("/ques_ans")
@login_required
def ques_ans():
    selected_role_id = request.args.get("role_id", type=int)
    if not selected_role_id:
        flash("No job role selected.", "warning")
        return redirect(url_for("user_dashboard.dashboard"))

    conn = get_db_connection()
    cursor = conn.cursor()
    resources = []

    try:
        # Get role name
        cursor.execute("SELECT name FROM job_roles WHERE id = %s", (selected_role_id,))
        role = cursor.fetchone()
        selected_role_name = role["name"] if role else "Unknown Role"

        # Fetch resources for reference in Q&A page
        cursor.execute(
            """
            SELECT title, description, url, created_at
            FROM learning_resources
            WHERE job_role_id = %s
            ORDER BY created_at DESC
        """,
            (selected_role_id,),
        )
        resources = cursor.fetchall()

    finally:
        conn.close()

    return render_template(
        "user/resources/ques_ans.html",
        selected_role_id=selected_role_id,
        selected_role_name=selected_role_name,
        resources=resources,
    )
