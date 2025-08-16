# utils/activity.py
from extensions import db
from datetime import datetime

def log_user_activity(user_id, activity_type, ip_address=None, user_agent=None, description=None):
    # Lazy import to avoid circular import
    from models.model import UserActivity

    activity = UserActivity(
        user_id=user_id,
        activity_type=activity_type,
        description=description,
        ip_address=ip_address,
        user_agent=user_agent,
        timestamp=datetime.utcnow()
    )
    db.session.add(activity)
    db.session.commit()


def log_interview_session(user_id, job_role_id, start_time, end_time, total_score):
    # Lazy import to avoid circular import
    from models.model import InterviewSession

    session = InterviewSession(
        user_id=user_id,
        job_role_id=job_role_id,
        start_time=start_time,
        end_time=end_time,
        total_score=total_score
    )
    db.session.add(session)
    db.session.commit()
