# routes/user/upload_resume.py
import os
from datetime import datetime
from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from extensions import db

upload_resume_bp = Blueprint('upload_resume', __name__, url_prefix='/user')

# Upload folder configuration
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads', 'resumes')
ALLOWED_EXTENSIONS = {'pdf'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Helper: check allowed file extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@upload_resume_bp.route('/upload_resume', methods=['GET', 'POST'])
@login_required
def resume():
    if request.method == 'POST':
        # Check if file part exists
        if 'resume_pdf' not in request.files:
            return render_template(
                'user/user_dashboard.html',
                user=current_user,
                upload_error="No file part in request."
            )

        file = request.files['resume_pdf']

        # Check if file selected
        if file.filename == '':
            return render_template(
                'user/user_dashboard.html',
                user=current_user,
                upload_error="No file selected."
            )

        # Validate file type
        if file and allowed_file(file.filename):
            try:
                # Create unique filename
                timestamp = int(datetime.utcnow().timestamp())
                filename = secure_filename(f"{current_user.id}_{timestamp}_{file.filename}")
                save_path = os.path.join(UPLOAD_FOLDER, filename)

                # Save file
                file.save(save_path)

                # Update user's resume filename in DB
                current_user.resume_filename = filename
                db.session.commit()

                return render_template(
                    'user/dashboard/user_dashboard.html',
                    user=current_user,
                    upload_success="Resume uploaded successfully!"
                )

            except Exception as e:
                return render_template(
                    'user/dashboard/user_dashboard.html',
                    user=current_user,
                    upload_error=f"Upload failed: {e}"
                )

        else:
            return render_template(
                'user/dashboard/user_dashboard.html',
                user=current_user,
                upload_error="Invalid file format. Only PDFs allowed."
            )

    # GET request
    return render_template('user/dashboard/user_dashboard.html', user=current_user)
