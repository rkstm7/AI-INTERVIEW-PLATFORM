# routes/admin/manage_questions.py
from flask import Blueprint, request, render_template, redirect, url_for, flash
from flask_login import login_required
from models.model import db, Question, JobRole

manage_questions_bp = Blueprint('manage_questions', __name__, url_prefix='/admin')

# -------------------- Manage Questions --------------------
@manage_questions_bp.route('/questions')
def questions():
    manual_questions = Question.query.filter_by(source_type='manual').all()
    ai_questions = Question.query.filter_by(source_type='ai').all()

    return render_template(
        'admin/resources/manage_questions.html',
        manual_questions=manual_questions,
        ai_questions=ai_questions
    )

# -------------------- Add Question --------------------
@manage_questions_bp.route('/questions/add', methods=['GET', 'POST'])
@login_required
def add_question():
    job_roles = JobRole.query.with_entities(JobRole.id, JobRole.name).all()

    if request.method == 'POST':
        job_role_id = request.form.get('job_role_id')
        content = request.form.get('content')
        option_a = request.form.get('option_a')
        option_b = request.form.get('option_b')
        option_c = request.form.get('option_c')
        option_d = request.form.get('option_d')
        correct_option = request.form.get('correct_option')
        source_type = 'manual'

        if not all([job_role_id, content, option_a, option_b, option_c, option_d, correct_option]):
            flash("Please fill all fields", "warning")
            return render_template('admin/resources/add_question.html', job_roles=job_roles)

        new_question = Question(
            job_role_id=job_role_id,
            content=content,
            option_a=option_a,
            option_b=option_b,
            option_c=option_c,
            option_d=option_d,
            correct_option=correct_option,
            source_type=source_type
        )
        db.session.add(new_question)
        db.session.commit()

        flash("Question added successfully!", "success")
        return redirect(url_for('manage_questions.questions'))

    return render_template('admin/resources/add_question.html', job_roles=job_roles)

# -------------------- Edit Question --------------------
@manage_questions_bp.route('/questions/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_question(id):
    question = Question.query.get(id)
    job_roles = JobRole.query.with_entities(JobRole.id, JobRole.name).all()

    if not question:
        flash("Question not found!", "danger")
        return redirect(url_for('manage_questions.questions'))

    if request.method == 'POST':
        job_role_id = request.form.get('job_role_id')
        content = request.form.get('content')
        option_a = request.form.get('option_a')
        option_b = request.form.get('option_b')
        option_c = request.form.get('option_c')
        option_d = request.form.get('option_d')
        correct_option = request.form.get('correct_option')

        if not all([job_role_id, content, option_a, option_b, option_c, option_d, correct_option]):
            flash("Please fill all fields", "warning")
            return render_template('admin/resources/edit_question.html', question=question, job_roles=job_roles)

        question.job_role_id = job_role_id
        question.content = content
        question.option_a = option_a
        question.option_b = option_b
        question.option_c = option_c
        question.option_d = option_d
        question.correct_option = correct_option

        db.session.commit()

        flash("Question updated successfully!", "success")
        return redirect(url_for('manage_questions.questions'))

    return render_template('admin/resources/edit_question.html', question=question, job_roles=job_roles)

# -------------------- Delete Question --------------------
@manage_questions_bp.route('/questions/delete/<int:id>', methods=['POST'])
@login_required
def delete_question(id):
    question = Question.query.get(id)
    if question:
        db.session.delete(question)
        db.session.commit()
        flash("Question deleted successfully!", "success")
    else:
        flash("Question not found!", "danger")

    return redirect(url_for('manage_questions.questions'))

# -------------------- Delete All Questions by Source --------------------
@manage_questions_bp.route('/delete_all_questions/<source_type>', methods=['POST'])
@login_required
def delete_all_questions(source_type):
    Question.query.filter_by(source_type=source_type).delete()
    db.session.commit()
    flash(f"All {source_type.upper()} questions deleted successfully!", "success")
    return redirect(url_for('manage_questions.questions'))
