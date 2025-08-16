# run.py
import os
from flask import Flask, redirect, url_for, request
from configs.config import DevelopmentConfig
from extensions import db, login_manager
from models.model import User, Role
from dotenv import load_dotenv
from flask_login import LoginManager
from datetime import datetime
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()


def create_app():
    # Load .env first
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

    app = Flask(__name__)
    app.secret_key = os.getenv("SECRET_KEY")
    app.config.from_object(DevelopmentConfig)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "user_login.login"

    @login_manager.unauthorized_handler
    def unauthorized_callback():
        if request.path.startswith("/admin"):
            return redirect(url_for("admin_login.login"))
        return redirect(url_for("user_login.login"))

    with app.app_context():
        # Create all tables
        db.create_all()

        # -------- Auto-create admin from .env --------
        admin_email = os.getenv("ADMIN_EMAIL")
        admin_password = os.getenv("ADMIN_PASSWORD")
        admin_username = os.getenv("ADMIN_USERNAME", "admin")  # fallback username
        admin_phone = os.getenv("ADMIN_PHONE", "9999999999")
        admin_address = os.getenv("ADMIN_ADDRESS", "Admin Address")

        if not admin_email or not admin_password:
            raise ValueError("ADMIN_EMAIL or ADMIN_PASSWORD not set in .env")

        # 1️⃣ Check if 'Admin' role exists, create if not
        admin_role = Role.query.filter_by(role_name="Admin").first()
        if not admin_role:
            admin_role = Role(role_name="Admin", status="Active")
            db.session.add(admin_role)
            db.session.commit()

        # 2️⃣ Check if admin user exists
        existing_admin = (
            User.query.join(Role)
            .filter(User.email == admin_email, Role.role_name == "Admin")
            .first()
        )

        if not existing_admin:
            # ✅ Hash the password
            hashed_pw = bcrypt.generate_password_hash(admin_password).decode("utf-8")

            new_admin = User(
                name="Admin",
                username=admin_username,
                email=admin_email,
                phone=admin_phone,
                address=admin_address,
                password=hashed_pw,
                show_password=admin_password,  # remove in production
                status="Active",
                last_active=datetime.utcnow(),
                created_at=datetime.utcnow(),
                deleted_at=None,
                role_obj=admin_role,  # pass the Role object
            )
            db.session.add(new_admin)
            db.session.commit()
            print(f"✅ Admin '{admin_email}' created successfully.")
        else:
            print(f"ℹ️ Admin '{admin_email}' already exists.")

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # -------- Register Blueprints --------
    # Public
    from routes.auth.register import register_bp
    from routes.auth.admin_login import admin_login_bp
    from routes.auth.user_login import user_login_bp

    # User
    from routes.user.logout import user_logout_bp
    from routes.public.public_dashboard import public_dashboard_bp
    from routes.user.contact import contact_bp
    from routes.user.user_dashboard import user_dashboard_bp
    from routes.user.resources import user_resources_bp
    from routes.user.interview_preparation import interview_bp
    from routes.user.scorecard import scorecard_bp
    from routes.user.legal_pages import legal_bp
    from routes.user.manual_feedback import feedback_bp
    from routes.user.notice import notice_bp
    from routes.user.upload_resume import upload_resume_bp
    from routes.user.view_profile import user_profile_bp

    # Admin
    from routes.admin.admin_dashboard import admin_dashboard_bp
    from routes.admin.admin_logout import admin_logout_bp
    from routes.admin.manage_role import manage_role_bp
    from routes.admin.manage_job_role import manage_job_role_bp
    from routes.admin.monitor_activity import monitor_activity_bp
    from routes.admin.user_ai_feedback import user_ai_feedback_bp
    from routes.admin.user_manual_feedback import manual_feedback_bp
    from routes.admin.user_scorecard import user_scorecard_bp
    from routes.admin.manage_notice import manage_notice_bp
    from routes.admin.manage_questions import manage_questions_bp
    from routes.admin.manage_resources import manage_resources_bp
    from routes.admin.manage_roles import roles_bp

    # Register Blueprints
    app.register_blueprint(register_bp)
    app.register_blueprint(admin_login_bp)
    app.register_blueprint(user_login_bp)

    app.register_blueprint(user_logout_bp)
    app.register_blueprint(public_dashboard_bp)
    app.register_blueprint(contact_bp)
    app.register_blueprint(user_dashboard_bp)
    app.register_blueprint(user_resources_bp)
    app.register_blueprint(interview_bp)
    app.register_blueprint(scorecard_bp)
    app.register_blueprint(legal_bp)
    app.register_blueprint(feedback_bp)
    app.register_blueprint(notice_bp)
    app.register_blueprint(upload_resume_bp)
    app.register_blueprint(user_profile_bp)

    # Admin
    app.register_blueprint(admin_dashboard_bp)
    app.register_blueprint(admin_logout_bp)
    app.register_blueprint(manage_role_bp)
    app.register_blueprint(manage_job_role_bp)
    app.register_blueprint(monitor_activity_bp)
    app.register_blueprint(user_ai_feedback_bp)
    app.register_blueprint(manual_feedback_bp)
    app.register_blueprint(user_scorecard_bp)
    app.register_blueprint(manage_notice_bp)
    app.register_blueprint(manage_questions_bp)
    app.register_blueprint(manage_resources_bp)
    app.register_blueprint(roles_bp)

    return app


# Expose app for Gunicorn
app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
