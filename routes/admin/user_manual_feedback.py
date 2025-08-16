# routes/admin/manual_feedback.py
from flask import Blueprint, render_template
from flask_login import login_required
from models.model import Feedback

manual_feedback_bp = Blueprint("manual_feedback", __name__, url_prefix="/admin")


@manual_feedback_bp.route("/manual-feedback")
@login_required
def manual_feedback():
    feedbacks = Feedback.query.order_by(Feedback.submitted_at.desc()).all()
    return render_template("admin/feedback/admin_feedback.html", feedbacks=feedbacks)
