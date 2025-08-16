# routes/admin/user_scorecard.py
from flask import Blueprint, render_template
from flask_login import login_required
from models.model import InterviewSession, JobRole  # Import your SQLAlchemy models

user_scorecard_bp = Blueprint(
    'user_scorecard', __name__,
    url_prefix='/admin'
)

@user_scorecard_bp.route('/scorecard')
@login_required
def scorecard():
    # Query with join to get job role name
    scores = (
        InterviewSession.query
        .join(JobRole, InterviewSession.job_role_id == JobRole.id, isouter=True)
        .order_by(InterviewSession.start_time.desc())
        .all()
    )

    return render_template(
        'admin/scorecard/admin_view_score.html',
        scores=scores
    )
