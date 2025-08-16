from utils.db import get_db_connection as get_db

def evaluate_answers(question_text, user_answer, correct_answer=None):
    db = get_db()

    if correct_answer is not None:
        return user_answer.strip().lower() == correct_answer.strip().lower()

    row = db.execute(
        "SELECT correct_option FROM questions WHERE content = %s", (question_text,)
    ).fetchone()

    if row and row["correct_option"]:
        return user_answer.strip().lower() == row["correct_option"].strip().lower()

    return False
