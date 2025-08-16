# routes/user/manual_feedback.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from utils.db import get_db_connection
from pymysql.cursors import DictCursor
from datetime import datetime

feedback_bp = Blueprint("feedback", __name__, url_prefix="/user")


@feedback_bp.route("/manual_feedback", methods=["GET", "POST"])
def manual_feedback():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        message = request.form.get("message")

        # Collect responses to the rating questions
        feedback_responses = {}
        for i in range(1, 11):
            feedback_responses[f"q{i}"] = int(request.form.get(f"q{i}", 0))

        # Store feedback in DB
        conn = get_db_connection()
        try:
            with conn.cursor(DictCursor) as cursor:
                cursor.execute(
                    """
                    INSERT INTO feedback
                    (name, email, message, q1, q2, q3, q4, q5, q6, q7, q8, q9, q10, submitted_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                    (
                        name,
                        email,
                        message,
                        feedback_responses["q1"],
                        feedback_responses["q2"],
                        feedback_responses["q3"],
                        feedback_responses["q4"],
                        feedback_responses["q5"],
                        feedback_responses["q6"],
                        feedback_responses["q7"],
                        feedback_responses["q8"],
                        feedback_responses["q9"],
                        feedback_responses["q10"],
                        datetime.utcnow(),
                    ),
                )
                conn.commit()
        finally:
            conn.close()

        flash("Thanks for your feedback!", "success")
        return redirect(url_for("feedback.thank_you_feedback"))

    return render_template("user/feedback/manual_feedback.html")


# -------- Thank You --------
@feedback_bp.route("/thank_you_feedback")
@login_required
def thank_you_feedback():
    return render_template("user/interview_module/thank_you.html")
