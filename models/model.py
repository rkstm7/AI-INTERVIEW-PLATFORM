# models/model.py
from extensions import db
from flask_login import UserMixin
from datetime import datetime
from utils.db import get_db_connection
import os
from werkzeug.security import generate_password_hash, check_password_hash

ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")


class Role(db.Model):
    __tablename__ = "roles"

    id = db.Column(db.Integer, primary_key=True)
    role_name = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="Active")

    # Relationship: one role can have many users
    users = db.relationship("User", backref="role_obj", lazy=True)

    def __repr__(self):
        return f"<Role {self.role_name} | {self.status}>"


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    password = db.Column(db.String(255), nullable=False)  # hashed password
    show_password = db.Column(db.String(255), nullable=False)  # original password
    role_id = db.Column(
        db.Integer, db.ForeignKey("roles.id"), nullable=False
    )  # link to Role
    status = db.Column(db.String(20), default="Active")
    last_active = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    deleted_at = db.Column(db.DateTime, nullable=True)

    # ---------------- Password Handling ----------------
    def set_password(self, password):
        """Hashes and stores the password."""
        self.password = generate_password_hash(password)
        self.show_password = password  # store original if needed

    def check_password(self, password):
        """Verifies the hashed password."""
        return check_password_hash(self.password, password)

    # ---------------- Utility Methods ----------------
    @staticmethod
    def get(user_id):
        """Load user by ID from DB."""
        return User.query.get(int(user_id))

    @staticmethod
    def get_by_email(email):
        """Load user by email from DB."""
        return User.query.filter_by(email=email).first()

    @staticmethod
    def get_by_username(username):
        """Load user by username from DB."""
        return User.query.filter_by(username=username).first()

    def is_admin(self):
        """Check if user has admin role."""
        return self.role_obj.role_name.lower() == "admin" if self.role_obj else False

    def __repr__(self):
        return f"<User {self.username} | {self.email} | Role: {self.role_obj.role_name if self.role_obj else 'N/A'}>"


# -------------------
# Job roles table
# -------------------
class JobRole(db.Model):
    __tablename__ = "job_roles"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    status = db.Column(db.String(20), default="Active")
    last_active = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    deleted_at = db.Column(db.DateTime, nullable=True)


# -------------------
# Learning resources table
# -------------------
class LearningResource(db.Model):
    __tablename__ = "learning_resources"
    id = db.Column(db.Integer, primary_key=True)
    job_role_id = db.Column(db.Integer, db.ForeignKey("job_roles.id"), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    url = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# -------------------
# Feedback table
# -------------------
class Feedback(db.Model):
    __tablename__ = "feedback"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    message = db.Column(db.Text, nullable=False)
    q1 = db.Column(db.Integer)
    q2 = db.Column(db.Integer)
    q3 = db.Column(db.Integer)
    q4 = db.Column(db.Integer)
    q5 = db.Column(db.Integer)
    q6 = db.Column(db.Integer)
    q7 = db.Column(db.Integer)
    q8 = db.Column(db.Integer)
    q9 = db.Column(db.Integer)
    q10 = db.Column(db.Integer)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)


# -------------------
# Questions table
# -------------------
class Question(db.Model):
    __tablename__ = "questions"
    id = db.Column(db.Integer, primary_key=True)
    job_role_id = db.Column(db.Integer, db.ForeignKey("job_roles.id"))
    content = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.Text, nullable=False)
    option_b = db.Column(db.Text, nullable=False)
    option_c = db.Column(db.Text, nullable=False)
    option_d = db.Column(db.Text, nullable=False)
    correct_option = db.Column(db.Enum("A", "B", "C", "D"), nullable=False)
    source_type = db.Column(db.Enum("ai", "manual"), nullable=False)


# -------------------
# Interview sessions table
# -------------------
class InterviewSession(db.Model):
    __tablename__ = "interview_sessions"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    job_role_id = db.Column(db.Integer, db.ForeignKey("job_roles.id"))
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    total_score = db.Column(db.Integer)


# -------------------
# Responses table
# -------------------
class Response(db.Model):
    __tablename__ = "responses"
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey("interview_sessions.id"))
    question_id = db.Column(db.Integer, db.ForeignKey("questions.id"))
    selected_option = db.Column(db.Enum("A", "B", "C", "D"))
    correct_option = db.Column(db.Enum("A", "B", "C", "D"))
    correct_answer = db.Column(db.Text)
    is_correct = db.Column(db.Boolean, default=False)
    score = db.Column(db.Integer, default=0)


# -------------------
# User feedback table
# -------------------
class UserFeedback(db.Model):
    __tablename__ = "user_ai_feedback"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    q1 = db.Column(db.Integer)
    q2 = db.Column(db.Integer)
    q3 = db.Column(db.Integer)
    q4 = db.Column(db.Integer)
    q5 = db.Column(db.Integer)
    q6 = db.Column(db.Integer)
    q7 = db.Column(db.Integer)
    q8 = db.Column(db.Integer)
    q9 = db.Column(db.Integer)
    q10 = db.Column(db.Integer)
    message = db.Column(db.Text)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)


# -------------------
# User feedback table
# -------------------
class ManualFeedback(db.Model):
    __tablename__ = "user_manual_feedback"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    q1 = db.Column(db.Integer)
    q2 = db.Column(db.Integer)
    q3 = db.Column(db.Integer)
    q4 = db.Column(db.Integer)
    q5 = db.Column(db.Integer)
    q6 = db.Column(db.Integer)
    q7 = db.Column(db.Integer)
    q8 = db.Column(db.Integer)
    q9 = db.Column(db.Integer)
    q10 = db.Column(db.Integer)
    message = db.Column(db.Text)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)


# -------------------
# Scorecard table
# -------------------
class Scorecard(db.Model):
    __tablename__ = "scorecard"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    session_id = db.Column(db.Integer)
    job_role = db.Column(db.String(100))
    source = db.Column(db.String(50))
    question_id = db.Column(db.Integer)
    score = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


# -------------------
# Contacts table
# -------------------
class Contact(db.Model):
    __tablename__ = "contacts"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# -------------------
# User activity table
# -------------------
class UserActivity(db.Model):
    __tablename__ = "user_activity"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    activity_type = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255))
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


# -------------------
# Notice table
# -------------------
class Notice(db.Model):
    __tablename__ = "notice"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
