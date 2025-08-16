from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from utils.db import get_db_connection  # ✅ Using raw DB connection

# Blueprint
user_profile_bp = Blueprint("user_profile", __name__, url_prefix="/user")


# 📌 View Profile
@user_profile_bp.route("/view_profile")
@login_required
def view_profile():
    return render_template("user/profile/view_profile.html", user=current_user)


# 📌 Edit Profile
@user_profile_bp.route("/edit_profile", methods=["GET"])
@login_required
def edit_profile():
    return render_template("user/profile/edit_profile.html", user=current_user)


# 📌 Update Profile
@user_profile_bp.route("/update_profile", methods=["POST"])
@login_required
def update_profile():
    name = request.form.get("name")
    phone = request.form.get("phone")  # ✅ matches DB column
    address = request.form.get("address")
    password = request.form.get("password")

    conn = get_db_connection()
    cursor = conn.cursor()

    if password and password.strip():
        hashed_password = generate_password_hash(password)
        cursor.execute(
            """
            UPDATE users
            SET name=%s, phone=%s, address=%s, password=%s, show_password=%s
            WHERE id=%s
        """,
            (name, phone, address, hashed_password, password, current_user.id),
        )
    else:
        cursor.execute(
            """
            UPDATE users
            SET name=%s, phone=%s, address=%s
            WHERE id=%s
        """,
            (name, phone, address, current_user.id),
        )

    conn.commit()
    cursor.close()
    conn.close()

    flash("✅ Profile updated successfully!", "success")
    return redirect(url_for("user_profile.view_profile"))
