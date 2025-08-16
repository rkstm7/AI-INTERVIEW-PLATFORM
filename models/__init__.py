# models/__init__.py
from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy
db = SQLAlchemy()

def init_db(app):
    """
    Initialize SQLAlchemy with the Flask app
    and create all tables in the database.
    """
    db.init_app(app)
    
    with app.app_context():
        # Import all models here to register them with SQLAlchemy
        from .model import (
            User, Role, JobRole, Feedback, Question, InterviewSession, Response,
            UserFeedback, Scorecard, Contact, UserActivity, LearningResource, Notice
        )

        # Create all tables in the database if they don't exist
        db.create_all()
