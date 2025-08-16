# routes/user/interview_preparation.py
from flask import Blueprint, render_template, request, redirect, session, flash, url_for
from flask_login import login_required, current_user
from datetime import datetime
from utils.db import get_db_connection as get_db
from utils.ai_questions import generate_mcq_questions
from utils.manual_evaluation import evaluate_answers
from utils.ai_evaluation import evaluate_answer_ai
from utils.activity import log_user_activity, log_interview_session

interview_bp = Blueprint("interview", __name__, url_prefix="/user")


# -------- Job roles route --------
@interview_bp.route("/job_roles")
@login_required
def job_roles():
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM job_roles")
            roles = cursor.fetchall()
    finally:
        conn.close()

    return render_template("user/interview_module/job_roles.html", roles=roles)


# -------- Start Interview --------
@interview_bp.route("/start", methods=["GET", "POST"])
@login_required
def start_interview():
    conn = get_db()
    try:
        if request.method == "POST":
            role_id = request.form["job_role"]
            mode = request.form["mode"]
            session["job_role"] = int(role_id)
            session["mode"] = mode
            questions = []

            # Log user activity
            log_user_activity(
                current_user.id, f"Started interview for role_id {role_id}"
            )

            with conn.cursor() as cursor:
                if mode == "ai":
                    # Get role name
                    cursor.execute(
                        "SELECT name FROM job_roles WHERE id = %s", (role_id,)
                    )
                    role_name_row = cursor.fetchone()
                    role_name = role_name_row["name"] if role_name_row else ""
                    mcqs = generate_mcq_questions(role_name)

                    for mcq in mcqs:
                        # Insert AI-generated questions into DB
                        cursor.execute(
                            """
                            INSERT INTO questions
                            (job_role_id, content, option_a, option_b, option_c, option_d, correct_option, source_type)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                            (
                                role_id,
                                mcq["question"],
                                mcq["option_a"],
                                mcq["option_b"],
                                mcq["option_c"],
                                mcq["option_d"],
                                mcq["correct_answer"],
                                "ai",
                            ),
                        )
                        questions.append(
                            {
                                "content": mcq["question"],
                                "option_a": mcq["option_a"],
                                "option_b": mcq["option_b"],
                                "option_c": mcq["option_c"],
                                "option_d": mcq["option_d"],
                                "correct_answer": mcq["correct_answer"],
                            }
                        )
                else:
                    cursor.execute(
                        """
                        SELECT content, option_a, option_b, option_c, option_d, correct_option
                        FROM questions
                        WHERE job_role_id = %s AND source_type = 'manual'
                    """,
                        (role_id,),
                    )
                    q_rows = cursor.fetchall()

                    questions = [
                        {
                            "content": q["content"],
                            "option_a": q["option_a"],
                            "option_b": q["option_b"],
                            "option_c": q["option_c"],
                            "option_d": q["option_d"],
                            "correct_answer": q["correct_option"],
                        }
                        for q in q_rows
                    ]

                conn.commit()
            session["questions"] = questions
            return redirect(url_for("interview.interview_session"))

        # GET request: load roles
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM job_roles")
            roles = cursor.fetchall()
    finally:
        conn.close()

    return render_template("user/interview_module/interview_start.html", roles=roles)


# -------- Interview Session --------
@interview_bp.route("/session", methods=["GET", "POST"])
@login_required
def interview_session():
    conn = get_db()
    try:
        if request.method == "POST":
            questions = session.get("questions", [])
            job_role = session.get("job_role")
            user_id = current_user.id

            with conn.cursor() as cursor:
                # Insert session
                cursor.execute(
                    "INSERT INTO interview_sessions (user_id, job_role_id, start_time) VALUES (%s, %s, %s)",
                    (user_id, job_role, datetime.now()),
                )
                session_id = cursor.lastrowid
                conn.commit()

                total_score = 0

                for i, q in enumerate(questions):
                    answer_key = f"answers{i + 1}"
                    selected_option = request.form.get(answer_key)
                    q_content = q["content"]
                    correct_option = q.get("correct_answer", None)

                    cursor.execute(
                        "SELECT id FROM questions WHERE content = %s", (q_content,)
                    )
                    q_row = cursor.fetchone()
                    q_id = q_row["id"] if q_row else None
                    if not q_id:
                        continue

                    if selected_option not in ("A", "B", "C", "D"):
                        selected_option = None

                    is_correct = evaluate_answers(
                        q_content, selected_option, correct_option
                    )
                    score = 2 if is_correct else 0
                    total_score += score

                    cursor.execute(
                        """
                        INSERT INTO responses (session_id, question_id, selected_option, correct_option, score, is_correct)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                        (
                            session_id,
                            q_id,
                            selected_option,
                            correct_option,
                            score,
                            int(is_correct),
                        ),
                    )

                # Update session end_time and total_score
                cursor.execute(
                    """
                    UPDATE interview_sessions SET total_score = %s, end_time = %s WHERE id = %s
                """,
                    (total_score, datetime.now(), session_id),
                )
                conn.commit()

            # Log interview session
            log_interview_session(
                user_id, job_role, datetime.now(), datetime.now(), total_score
            )

            # Prepare result messages
            if total_score > 20:
                session["result_message"] = "🎉 You are ready for the interview!"
                session["retake"] = False
            else:
                session["result_message"] = (
                    "⚠️ Try to improve your marks. Please retake the interview."
                )
                session["retake"] = True

            session["score"] = total_score
            session["session_id"] = session_id
            return redirect(url_for("interview.finalize_interview"))

        questions = session.get("questions", [])
    finally:
        conn.close()

    return render_template(
        "user/interview_module/interview_session.html", questions=questions
    )


# -------- Finalize --------
@interview_bp.route("/finalize")
@login_required
def finalize_interview():
    questions = session.get("questions", [])
    score = session.get("score", 0)
    total = len(questions) * 2
    accuracy = round((score / total) * 100, 2) if total else 0
    message = session.get("result_message", "")
    retake = session.get("retake", False)

    return render_template(
        "user/interview_module/finalize_interview.html",
        score=score,
        accuracy=accuracy,
        questions=questions,
        message=message,
        retake=retake,
        enumerate=enumerate,
    )


# -------- Feedback Route --------
@interview_bp.route("/send_feedback", methods=["POST"])
@login_required
def send_feedback():
    name = request.form.get("name")
    email = request.form.get("email")
    message_text = request.form.get("message")

    ratings = {}
    missing = []
    for i in range(1, 11):
        val = request.form.get(f"q{i}")
        if not val:
            missing.append(i)
        else:
            ratings[f"q{i}"] = int(val)

    if missing:
        flash(
            f"⚠ Please rate all questions. Missing: {', '.join(map(str, missing))}",
            "danger",
        )
        return render_template(
            "user/interview_module/finalize_interview.html",  # replace with your template filename
            name=name,
            email=email,
            message_text=message_text,
            ratings=ratings,
            missing=missing,
        )

    # Save to DB
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO user_ai_feedback
                (name, email, message, q1, q2, q3, q4, q5, q6, q7, q8, q9, q10, submitted_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    name,
                    email,
                    message_text,
                    ratings["q1"],
                    ratings["q2"],
                    ratings["q3"],
                    ratings["q4"],
                    ratings["q5"],
                    ratings["q6"],
                    ratings["q7"],
                    ratings["q8"],
                    ratings["q9"],
                    ratings["q10"],
                    datetime.utcnow(),
                ),
            )
            conn.commit()
    finally:
        conn.close()

    flash("Thank you for your feedback!", "success")
    return redirect(url_for("interview.thank_you"))


# -------- Thank You --------
@interview_bp.route("/thank_you")
@login_required
def thank_you():
    return render_template("user/interview_module/thank_you.html")
