# routes/admin/user_ai_feedback.py
from flask import Blueprint, render_template
from flask_login import login_required
from models.model import UserFeedback  # Import your SQLAlchemy model

user_ai_feedback_bp = Blueprint("ai_feedback", __name__, url_prefix="/admin")


@user_ai_feedback_bp.route("/ai-feedback")
@login_required
def ai_feedback():
    # Fetch all feedbacks ordered by submitted_at (latest first)
    feedbacks = UserFeedback.query.order_by(UserFeedback.submitted_at.desc()).all()

    return render_template("admin/feedback/view_feedback.html", feedbacks=feedbacks)
