from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    jsonify,
)
from flask_login import login_user
from datetime import datetime, timedelta
import random
import smtplib
from email.mime.text import MIMEText
from werkzeug.security import generate_password_hash
from forms.register_form import RegisterForm
from models.model import db, Role, User
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

register_bp = Blueprint("register", __name__, url_prefix="/auth")


# ---------------- Utility Functions ----------------
def generate_otp(length=6):
    return "".join(str(random.randint(0, 9)) for _ in range(length))


def send_otp_email(to_email, otp):
    try:
        smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", 587))
        sender_email = os.getenv("SMTP_EMAIL")
        sender_password = os.getenv("SMTP_PASSWORD")

        if not sender_email or not sender_password:
            print("SMTP credentials not set in .env")
            return False

        msg = MIMEText(f"Your OTP for registration is: {otp}")
        msg["Subject"] = "Email Verification OTP"
        msg["From"] = sender_email
        msg["To"] = to_email

        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print("OTP email error:", e)
        return False


@register_bp.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()

    if request.method == "GET":
        return render_template("public/register/register.html", form=form)

    if request.method == "POST":
        # OTP must be verified before submitting
        if not session.get("otp_verified"):
            flash("Please verify your OTP before submitting.", "danger")
            return render_template("public/register/register.html", form=form)

        # Validate the form
        if not form.validate_on_submit():
            print("Form errors:", form.errors)  # Debug: shows which fields failed
            flash("Please correct the errors in the form", "danger")
            return render_template("public/register/register.html", form=form)

        # Get or create the "User" role
        role = Role.query.filter_by(role_name="User").first()
        if not role:
            role = Role(role_name="User", status="Active")
            db.session.add(role)
            db.session.commit()  # commit to get the role.id

        # Hash password correctly
        from extensions import bcrypt

        hashed_password = bcrypt.generate_password_hash(form.password.data).decode(
            "utf-8"
        )
        show_password_value = form.password.data

        # Create a new user instance
        new_user = User(
            name=form.name.data,
            username=form.username.data,
            email=form.email.data,
            phone=form.phone.data,
            address=form.address.data,
            password=hashed_password,
            show_password=show_password_value,  # <-- must provide this
            role_id=role.id,
            status="Active",
            last_active=datetime.utcnow(),
            created_at=datetime.utcnow(),
        )

        # Commit the new user
        db.session.add(new_user)
        db.session.commit()

        # Clear OTP session data
        session.pop("otp_code", None)
        session.pop("otp_expiry", None)
        session.pop("otp_verified", None)

        flash("Registration successful! You can now log in.", "success")
        return redirect(url_for("user_login.login"))


# ---------- Route: Send OTP ----------
@register_bp.route("/send-otp", methods=["POST"])
def send_otp():
    data = request.get_json()
    email = data.get("email")

    if not email:
        return jsonify({"success": False, "message": "Email is required"})

    # Generate OTP & expiry
    otp = str(random.randint(100000, 999999))
    expiry_time = datetime.utcnow() + timedelta(minutes=5)

    # Save OTP in session
    session["otp_code"] = otp
    session["otp_expiry"] = expiry_time.isoformat()
    session["otp_verified"] = False

    if send_otp_email(email, otp):
        return jsonify(
            {
                "success": True,
                "message": "OTP sent to your email.",
                "expiry": 300,  # seconds
            }
        )
    else:
        return jsonify({"success": False, "message": "Failed to send OTP"})


# ---------- Route: Verify OTP ----------
@register_bp.route("/verify-otp", methods=["POST"])
def verify_otp():
    data = request.get_json()
    otp_entered = data.get("otp")

    otp_saved = session.get("otp_code")
    otp_expiry = session.get("otp_expiry")

    if not otp_saved or not otp_expiry:
        return jsonify({"success": False, "message": "No OTP session found."})

    if datetime.utcnow() > datetime.fromisoformat(otp_expiry):
        return jsonify({"success": False, "message": "OTP expired."})

    if otp_entered == otp_saved:
        session["otp_verified"] = True
        return jsonify({"success": True, "message": "OTP verified."})
    else:
        return jsonify({"success": False, "message": "Invalid OTP"})
