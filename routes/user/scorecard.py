from flask import Blueprint, render_template, make_response
from flask_login import login_required, current_user
from utils.db import get_db_connection
from pymysql.cursors import DictCursor
import pdfkit  # only pdfkit, no WeasyPrint
from datetime import datetime

scorecard_bp = Blueprint("scorecard", __name__, url_prefix="/user")


@scorecard_bp.route("/scorecard")
@login_required
def scorecard():
    """
    Fetch all interview sessions for the logged-in user
    and render the scorecard page (HTML view).
    """
    user_id = current_user.id
    conn = get_db_connection()

    try:
        with conn.cursor(DictCursor) as cursor:
            cursor.execute(
                """
                SELECT 
                    isession.id AS session_id,
                    jr.name AS job_role,
                    isession.start_time,
                    isession.end_time,
                    isession.total_score,
                    (SELECT COUNT(*) 
                     FROM responses r 
                     WHERE r.session_id = isession.id) AS total_questions
                FROM interview_sessions isession
                JOIN job_roles jr ON jr.id = isession.job_role_id
                WHERE isession.user_id = %s
                ORDER BY isession.start_time DESC
                """,
                (user_id,),
            )
            sessions = cursor.fetchall()
    finally:
        conn.close()

    return render_template("user/interview_module/scorecard.html", sessions=sessions)


from datetime import datetime


@scorecard_bp.route("/scorecard/pdf")
@login_required
def scorecard_pdf():
    user_id = current_user.id
    conn = get_db_connection()

    try:
        with conn.cursor(DictCursor) as cursor:
            cursor.execute(
                """
                SELECT 
                    isession.id AS session_id,
                    jr.name AS job_role,
                    isession.start_time,
                    isession.end_time,
                    isession.total_score,
                    (SELECT COUNT(*) 
                     FROM responses r 
                     WHERE r.session_id = isession.id) AS total_questions
                FROM interview_sessions isession
                JOIN job_roles jr ON jr.id = isession.job_role_id
                WHERE isession.user_id = %s
                ORDER BY isession.start_time DESC
            """,
                (user_id,),
            )
            sessions = cursor.fetchall()
    finally:
        conn.close()

    rendered = render_template(
        "user/interview_module/scorecard_pdf.html",
        sessions=sessions,
        user=current_user,
        generated_on=datetime.now(),  # Pass time here
    )

    config = pdfkit.configuration(
        wkhtmltopdf=r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
    )

    pdf = pdfkit.from_string(rendered, False, configuration=config)

    response = make_response(pdf)
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = "inline; filename=scorecard.pdf"
    return response


@scorecard_bp.route("/scorecard/pdf/<int:session_id>")
@login_required
def scorecard_pdf_single(session_id):
    user_id = current_user.id
    conn = get_db_connection()

    try:
        with conn.cursor(DictCursor) as cursor:
            cursor.execute(
                """
                SELECT 
                    isession.id AS session_id,
                    jr.name AS job_role,
                    isession.start_time,
                    isession.end_time,
                    isession.total_score,
                    (SELECT COUNT(*) 
                     FROM responses r 
                     WHERE r.session_id = isession.id) AS total_questions
                FROM interview_sessions isession
                JOIN job_roles jr ON jr.id = isession.job_role_id
                WHERE isession.user_id = %s AND isession.id = %s
                """,
                (user_id, session_id),
            )
            session = cursor.fetchone()
    finally:
        conn.close()

    if not session:
        return "Session not found or unauthorized", 404

    rendered = render_template(
        "user/interview_module/pdf_scorecard.html",
        session=session,
        user=current_user,
        generated_on=datetime.now(),
    )

    config = pdfkit.configuration(
        wkhtmltopdf=r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
    )

    pdf = pdfkit.from_string(rendered, False, configuration=config)

    response = make_response(pdf)
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = (
        f"inline; filename=scorecard_session_{session_id}.pdf"
    )
    return response
