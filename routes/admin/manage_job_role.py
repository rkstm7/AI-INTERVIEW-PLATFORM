from flask import Blueprint, request, render_template, redirect, url_for, flash
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from extensions import db
from models.model import JobRole
from datetime import datetime

manage_job_role_bp = Blueprint("manage_job_roles", __name__, url_prefix="/admin")


@manage_job_role_bp.route("/job_roles", methods=["GET", "POST"])
def job_roles():
    # ---------------- POST REQUESTS ----------------
    if request.method == "POST":
        # Add new role
        if "add_role" in request.form:
            role_name = request.form.get("role_name", "").strip()
            if role_name:
                existing_role = JobRole.query.filter(
                    func.lower(JobRole.name) == role_name.lower()
                ).first()
                if existing_role:
                    flash(f'Role "{role_name}" already exists.', "danger")
                else:
                    new_role = JobRole(name=role_name)
                    db.session.add(new_role)
                    try:
                        db.session.commit()
                        flash(f'Role "{role_name}" added successfully!', "success")
                    except IntegrityError:
                        db.session.rollback()
                        flash(f'Role "{role_name}" already exists.', "danger")
            else:
                flash("Role name cannot be empty.", "warning")

        # Save edited role
        elif "save_edit" in request.form:
            role_id = request.form.get("role_id")
            updated_name = request.form.get("updated_name", "").strip()
            if role_id and updated_name:
                role = JobRole.query.get(role_id)
                if role:
                    existing_role = JobRole.query.filter(
                        func.lower(JobRole.name) == updated_name.lower(),
                        JobRole.id != role.id,
                    ).first()
                    if existing_role:
                        flash(f'Role "{updated_name}" already exists.', "danger")
                    else:
                        role.name = updated_name
                        try:
                            db.session.commit()
                            flash("Role updated successfully.", "success")
                        except IntegrityError:
                            db.session.rollback()
                            flash("Database error while updating role.", "danger")
                else:
                    flash("Role not found.", "warning")
            else:
                flash("Invalid data for update.", "warning")

        # Delete role
        elif "delete_role" in request.form:
            role_id = request.form.get("role_id")
            if role_id:
                role = JobRole.query.get(role_id)
                if role:
                    db.session.delete(role)
                    db.session.commit()
                    flash("Role deleted successfully.", "success")
                else:
                    flash("Role not found.", "warning")
            else:
                flash("Invalid role ID for deletion.", "warning")

        return redirect(url_for("manage_job_roles.job_roles"))

    # ---------------- GET REQUESTS ----------------
    search_name = request.args.get("search_name", "").strip()
    search_date = request.args.get("search_date", "").strip()
    show_add_form = request.args.get("show_add_form") == "1"
    edit_role_id = request.args.get("edit_role_id", type=int)

    # Base query
    query = JobRole.query

    # Filter by name
    if search_name:
        query = query.filter(JobRole.name.ilike(f"%{search_name}%"))

    # Filter by date (created_at date only)
    if search_date:
        try:
            date_obj = datetime.strptime(search_date, "%Y-%m-%d").date()
            query = query.filter(func.date(JobRole.created_at) == date_obj)
        except ValueError:
            flash("Invalid date format.", "warning")

    # Fetch results
    job_roles_list = query.order_by(JobRole.id).all()

    return render_template(
        "admin/job_roles/manage_job_roles.html",
        job_roles=job_roles_list,
        show_add_form=show_add_form,
        edit_role_id=edit_role_id,
    )
