from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash
from models.model import db, User, Role
from datetime import datetime

manage_role_bp = Blueprint("manage_role", __name__, url_prefix="/admin")


# -------------------------------------------------
# Manage Users (List + Search)
# -------------------------------------------------
@manage_role_bp.route("/manage_users", methods=["GET"])
def users():
    query = User.query

    # ---------- SEARCH ----------
    name = request.args.get("name", "").strip()
    email = request.args.get("email", "").strip()
    contact = request.args.get("contact", "").strip()
    start_date = request.args.get("start_date", "").strip()
    end_date = request.args.get("end_date", "").strip()

    if name:
        query = query.filter(User.name.ilike(f"%{name}%"))
    if email:
        query = query.filter(User.email.ilike(f"%{email}%"))
    if contact:
        query = query.filter(User.phone.ilike(f"%{contact}%"))
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            query = query.filter(User.created_at >= start_dt)
        except ValueError:
            pass
    if end_date:
        try:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            query = query.filter(User.created_at <= end_dt)
        except ValueError:
            pass

    all_users = query.order_by(User.created_at.desc()).all()
    return render_template("admin/users/manage_users.html", users=all_users)


# -------------------------------------------------
# Add User
# -------------------------------------------------
@manage_role_bp.route("/users/add", methods=["GET", "POST"])
def add_user():
    roles = Role.query.all()

    if request.method == "POST":
        name = request.form.get("full_name")
        username = request.form.get("username")
        email = request.form.get("email")
        phone = request.form.get("phone")
        address = request.form.get("address")
        password = request.form.get("password")
        role_id = request.form.get("role_id")
        status = request.form.get("status", "Active")

        # Validation
        if not (name and username and email and password and role_id):
            flash("Please fill in all required fields.", "danger")
            return redirect(url_for("manage_role.add_user"))

        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "danger")
            return redirect(url_for("manage_role.add_user"))

        if User.query.filter_by(username=username).first():
            flash("Username already taken.", "danger")
            return redirect(url_for("manage_role.add_user"))

        hashed_password = generate_password_hash(password)

        new_user = User(
            name=name,
            username=username,
            email=email,
            phone=phone,
            address=address,
            password=hashed_password,
            show_password=password,
            role_id=role_id,
            status=status,
        )

        db.session.add(new_user)
        db.session.commit()
        flash("User added successfully.", "success")
        return redirect(url_for("manage_role.users"))

    return render_template("admin/users/add_user.html", roles=roles)


# -------------------------------------------------
# Edit User
# -------------------------------------------------
@manage_role_bp.route("/users/edit/<int:user_id>", methods=["GET", "POST"])
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    roles = Role.query.all()

    if request.method == "POST":
        user.name = request.form.get("full_name")
        user.username = request.form.get("username")
        user.email = request.form.get("email")
        user.phone = request.form.get("phone")
        user.address = request.form.get("address")
        user.role_id = request.form.get("role_id")
        user.status = request.form.get("status")

        password = request.form.get("password")
        if password:
            user.password = generate_password_hash(password)
            user.show_password = password

        db.session.commit()
        flash("User updated successfully.", "success")
        return redirect(url_for("manage_role.users"))

    return render_template("admin/users/edit_user.html", user=user, roles=roles)


@manage_role_bp.route("/users/toggle_status/<int:user_id>", methods=["POST"])
def toggle_status(user_id):
    user = User.query.get_or_404(user_id)

    # Toggle between Active / Inactive
    user.status = "Inactive" if user.status == "Active" else "Active"
    db.session.commit()

    flash(f"User status updated to {user.status}.", "success")
    return redirect(url_for("manage_role.users"))


# -------------------------------------------------
# Delete User
# -------------------------------------------------
@manage_role_bp.route("/users/delete/<int:user_id>", methods=["POST"])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash("User deleted successfully.", "success")
    return redirect(url_for("manage_role.users"))
