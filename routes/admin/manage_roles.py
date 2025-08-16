from flask import Blueprint, render_template, request, redirect, url_for, flash
from models.model import db, Role
from flask_login import login_required

roles_bp = Blueprint("roles", __name__, url_prefix="/admin/manage_roles")


# List roles
@roles_bp.route("/", methods=["GET"])
@login_required
def roles():
    all_roles = Role.query.order_by(Role.id.asc()).all()
    return render_template("admin/roles/manage_roles.html", roles=all_roles)


# Add role
@roles_bp.route("/add", methods=["POST"])
@login_required
def add_role():
    name = request.form.get("name", "").strip()
    if not name:
        flash("Role name is required.", "danger")
        return redirect(url_for("roles.roles"))

    if Role.query.filter_by(role_name=name).first():
        flash("Role already exists.", "danger")
        return redirect(url_for("roles.roles"))

    new_role = Role(role_name=name, status="Active")
    db.session.add(new_role)
    db.session.commit()
    flash("Role added successfully!", "success")
    return redirect(url_for("roles.roles"))


# Edit role name or toggle status
@roles_bp.route("/edit/<int:role_id>", methods=["POST"])
@login_required
def edit_role(role_id):
    role = Role.query.get_or_404(role_id)
    name = request.form.get("name", role.role_name).strip()
    status = request.form.get("status", role.status)

    # Prevent duplicate names
    if Role.query.filter(Role.role_name == name, Role.id != role_id).first():
        flash("Role name already exists.", "danger")
        return redirect(url_for("roles.roles"))

    role.role_name = name
    role.status = status
    db.session.commit()
    flash("Role updated successfully!", "success")
    return redirect(url_for("roles.roles"))


# Delete role
@roles_bp.route("/delete/<int:role_id>", methods=["POST"])
@login_required
def delete_role(role_id):
    role = Role.query.get_or_404(role_id)
    db.session.delete(role)
    db.session.commit()
    flash("Role deleted successfully!", "success")
    return redirect(url_for("roles.roles"))
