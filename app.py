from flask import Flask, abort, render_template, redirect, url_for, session, flash, request
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, ValidationError
from werkzeug.security import generate_password_hash
import sqlite3
import bcrypt
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from datetime import datetime
import openai
import os, g
openai.api_key = os.getenv("OPENAI_API_KEY")

from flask import Flask , session
from flask_session import Session      # Session flask_session से


app = Flask(__name__)


# Secret key for session security
app.secret_key = '\x9c\xa4\xa6)\xa89 \xf9(\x0c/!\xd7\x1e\xb2\xfa^\xa9b\x98&0\xcf\x86'  # इसे strong और secret रखो

# Configure session to use filesystem (instead of signed cookies)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False

# Initialize the session
sess = Session(app)

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'user_login'  # default login redirect for @login_required

# DB filename
DB_NAME = 'users.db'


# Logging user activity
def log_user_activity(user_id, activity, ip_address, user_agent):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO user_activity (user_id, activity, timestamp, ip_address, user_agent)
        VALUES (?, ?, CURRENT_TIMESTAMP, ?, ?)
    """, (user_id, activity, ip_address, user_agent))
    conn.commit() # ✅ Always close the connection to avoid leaks


#getting rolles from database
def get_all_roles():
    with sqlite3.connect('users.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT job_role FROM questions")
        roles = [row[0] for row in cursor.fetchall()]
    return roles



#database initialization here
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Users table (merged with resume_filename)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL,
        resume_filename TEXT,
        last_active TIMESTAMP
    )
''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS admin (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )''')

    # Job roles table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS job_roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    ''')

    # Feedback table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            message TEXT NOT NULL,
            q1 INTEGER, q2 INTEGER, q3 INTEGER, q4 INTEGER, q5 INTEGER,
            q6 INTEGER, q7 INTEGER, q8 INTEGER, q9 INTEGER, q10 INTEGER,
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_role_id INTEGER,
        content TEXT NOT NULL,
        option_a TEXT NOT NULL,
        option_b TEXT NOT NULL,
        option_c TEXT NOT NULL,
        option_d TEXT NOT NULL,
        correct_option TEXT CHECK(correct_option IN ('A', 'B', 'C', 'D')) NOT NULL,
        source_type TEXT CHECK(source_type IN ('ai', 'manual')) NOT NULL,
        FOREIGN KEY (job_role_id) REFERENCES job_roles(id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS interview_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        job_role_id INTEGER,
        start_time TIMESTAMP,
        end_time TIMESTAMP,
        total_score INTEGER,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (job_role_id) REFERENCES job_roles(id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS responses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER,
        question_id INTEGER,
        selected_option TEXT CHECK(selected_option IN ('A', 'B', 'C', 'D')),
        correct_option TEXT CHECK(correct_option IN ('A', 'B', 'C', 'D')),
        correct_answer TEXT,
        is_correct INTEGER DEFAULT 0,
        score INTEGER DEFAULT 0,
        FOREIGN KEY (session_id) REFERENCES interview_sessions(id),
        FOREIGN KEY (question_id) REFERENCES questions(id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_feedback (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    q1 INTEGER,
    q2 INTEGER,
    q3 INTEGER,
    q4 INTEGER,
    q5 INTEGER,
    q6 INTEGER,
    q7 INTEGER,
    q8 INTEGER,
    q9 INTEGER,
    q10 INTEGER,
    message TEXT,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS scorecard (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,               
    session_id TEXT,              
    job_role TEXT,                 
    source TEXT,                 
    question_id INTEGER,          
    score INTEGER,                 
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
                   ''')

    # Insert default admin if not exists
    cursor.execute("INSERT OR IGNORE INTO admin (username, password) VALUES (?, ?)",
                   ("", ""))

    # Contacts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # User activity logging table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_activity (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            activity TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            ip_address TEXT,
            user_agent TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Learning resources table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS learning_resources (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_role_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        url TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (job_role_id) REFERENCES job_roles(id)
    )
''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS notice (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        url TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
''')
    
    conn.commit()
    conn.close()


        
def add_last_active_column():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Check if 'last_active' column exists
    cursor.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in cursor.fetchall()]
    if "last_active" not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN last_active TIMESTAMP")
        conn.commit()
        print("Added 'last_active' column to users table.")
    else:
        print("'last_active' column already exists.")

    conn.close()
    
    

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, id_, name, email, role):
        self.id = id_
        self.name = name
        self.email = email
        self.role = role

    @staticmethod
    def get(user_id):
        # For admin user with id=0 (hardcoded), return User directly
        if user_id == '0':
            return User(0, "Admin", ADMIN_EMAIL, "Admin")
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        if user:
            return User(user[0], user[1], user[2], user[4])
        return None

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)


        
# Forms
class RegisterForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Register")

    def validate_email(self, field):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (field.data,))
        user = cursor.fetchone()
        if user:
            raise ValidationError('Email already registered.')

class SimpleLoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")


@app.context_processor
def inject_current_year():
    # Makes current_year available globally in templates
    return {'current_year': datetime.now().year}


# Routes
@app.route('/')
def index():
    return render_template('index.html')

# User registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        # redirect based on role
        if current_user.role == "Admin":
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('user_dashboard'))

    form = RegisterForm()
    if form.validate_on_submit():
        name = form.name.data
        email = form.email.data
        password = form.password.data

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
                       (name, email, hashed_password.decode('utf-8'), 'User'))
        conn.commit()

        flash('Registration successful. Please login.')
        return redirect(url_for('user_login'))

    return render_template('auth/register.html', form=form)



@app.route('/user_login', methods=['GET', 'POST'])
def user_login():
    if current_user.is_authenticated:
        if current_user.role.lower() == "user":
            return redirect(url_for('dashboard'))
        else:
            return redirect(url_for('dashboard'))

    form = SimpleLoginForm()

    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()

        if user and bcrypt.checkpw(password.encode('utf-8'), user[3].encode('utf-8')):
            actual_role = user[4]
            if actual_role.lower() != "user":
                flash("This is User Login. You don't have User role.", "warning")
                return redirect(url_for('user_login'))

            user_obj = User(user[0], user[1], user[2], actual_role)
            login_user(user_obj)

            # ✅ Log user login activity with IP address and user agent
            ip_address = request.remote_addr
            user_agent = request.headers.get('User-Agent')
            log_user_activity(user_obj.id, "Logged in", ip_address, user_agent)

            flash("User logged in successfully.", "success")
            return redirect(url_for('dashboard'))

        else:
            flash("Login failed. Check your credentials.", "danger")
            return redirect(url_for('user_login'))

    return render_template('auth/user_login.html', form=form)





# User dashboard
@app.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    if current_user.role.lower() != "user":
        flash("Access denied! Only user can access the dashboard.", "danger")
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch all job roles
    cursor.execute("SELECT id, name FROM job_roles ORDER BY name")
    job_roles = cursor.fetchall()

    # Fetch all notices
    cursor.execute("""
        SELECT id, title, description, url, created_at
        FROM notice
        ORDER BY created_at DESC
    """)
    notices = cursor.fetchall()

    # Get selected role from query string
    selected_role_id = request.args.get('role_id', type=int)
    selected_role_name = None
    resources = []

    if selected_role_id:
        # Fetch selected role name
        cursor.execute("SELECT name FROM job_roles WHERE id = ?", (selected_role_id,))
        role = cursor.fetchone()
        if role:
            selected_role_name = role['name']

            # Fetch learning resources for the selected role
            cursor.execute("""
                SELECT title, description, url, created_at
                FROM learning_resources
                WHERE job_role_id = ?
                ORDER BY created_at DESC
            """, (selected_role_id,))
            resources = cursor.fetchall()

    upload_success = request.args.get('upload_success')
    upload_error = request.args.get('upload_error')

    conn.close()

    return render_template(
        'user/user_dashboard.html',
        user=current_user,
        job_roles=job_roles,
        selected_role_id=selected_role_id,
        selected_role_name=selected_role_name,
        resources=resources,
        notices=notices,  # ✅ FIX: previously it was "notice"
        upload_success=upload_success,
        upload_error=upload_error
    )


    
# ---- DB Connection ----
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DB_NAME)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_connection(exception):
    db = g.pop('db', None)
    if db:
        db.close()



import openai
import re
import time

def generate_mcq_questions(role_name, desired_count=15, max_attempts=3):
    all_questions = []

    for attempt in range(max_attempts):
        prompt = f"""
        Generate {desired_count} multiple choice questions for the job role "{role_name}". 
        Provide each question with 4 options labeled A, B, C, D and specify the correct answer.
        Format the output exactly like this:

        Q1: Question text?
        A) option1
        B) option2
        C) option3
        D) option4
        Answer: B
        """

        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.7
            )

            text = response.choices[0].message.content

            # Extract questions
            pattern = re.compile(
                r"Q\d+:\s*(.+?)\n"
                r"A\)\s*(.+?)\n"
                r"B\)\s*(.+?)\n"
                r"C\)\s*(.+?)\n"
                r"D\)\s*(.+?)\n"
                r"Answer:\s*([ABCD])",
                re.DOTALL
            )

            matches = pattern.findall(text)

            for match in matches:
                all_questions.append({
                    "question": match[0].strip(),
                    "option_a": match[1].strip(),
                    "option_b": match[2].strip(),
                    "option_c": match[3].strip(),
                    "option_d": match[4].strip(),
                    "correct_answer": match[5].strip()
                })

            if len(all_questions) >= desired_count:
                return all_questions[:desired_count]

            # Wait before retrying (avoid rate limit)
            time.sleep(2)

        except Exception as e:
            print(f"[Error] GPT request failed on attempt {attempt+1}: {e}")
            time.sleep(2)

    # Final fallback if all attempts fail
    return all_questions[:desired_count]


# ---- Evaluate answers helper ----
def evaluate_answers(question_text, user_answer, correct_answer=None):
    db = get_db()

    if correct_answer is not None:
        return user_answer.strip().lower() == correct_answer.strip().lower()

    # For manual questions with no correct_answer passed, try to look it up
    row = db.execute(
        "SELECT correct_option FROM questions WHERE content = ?", (question_text,)
    ).fetchone()

    if row and row["correct_option"]:
        return user_answer.strip().lower() == row["correct_option"].strip().lower()

    return False


# ---- Routes ----

# @app.route('/')
# def home():
#     return render_template("home.html")


def log_user_activity(user_id, activity, ip_address, user_agent):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO user_activity (user_id, activity, timestamp, ip_address, user_agent)
        VALUES (?, ?, CURRENT_TIMESTAMP, ?, ?)
    """, (user_id, activity, ip_address, user_agent))
    conn.commit()

@app.route('/job_roles')
def job_roles():
    db = get_db()
    roles = db.execute("SELECT * FROM job_roles").fetchall()
    return render_template("job_roles.html", roles=roles)



@app.route('/interview/start', methods=['GET', 'POST'])
def start_interview():
    db = get_db()
    if request.method == 'POST':
        role_id = request.form['job_role']
        mode = request.form['mode']
        session['job_role'] = int(role_id)
        session['mode'] = mode
        questions = []

        if mode == "ai":
            role_name = db.execute("SELECT name FROM job_roles WHERE id = ?", (role_id,)).fetchone()['name']
            mcqs = generate_mcq_questions(role_name)

            for mcq in mcqs:
                # Insert AI generated questions into DB
                db.execute("""
                    INSERT INTO questions
                    (job_role_id, content, option_a, option_b, option_c, option_d, correct_option, source_type)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    role_id,
                    mcq['question'],
                    mcq['option_a'],
                    mcq['option_b'],
                    mcq['option_c'],
                    mcq['option_d'],
                    mcq['correct_answer'],
                    "ai"
                ))
                questions.append({
                    "content": mcq['question'],
                    "option_a": mcq['option_a'],
                    "option_b": mcq['option_b'],
                    "option_c": mcq['option_c'],
                    "option_d": mcq['option_d'],
                    "correct_answer": mcq['correct_answer']
                })

        else:
            q_rows = db.execute("""
                SELECT content, option_a, option_b, option_c, option_d, correct_option
                FROM questions
                WHERE job_role_id = ? AND source_type = 'manual'
            """, (role_id,)).fetchall()

            questions = [
                {
                    "content": q['content'],
                    "option_a": q['option_a'],
                    "option_b": q['option_b'],
                    "option_c": q['option_c'],
                    "option_d": q['option_d'],
                    "correct_answer": q['correct_option']
                }
                for q in q_rows
            ]

        db.commit()
        session['questions'] = questions
        return redirect('/interview/session')

    roles = db.execute("SELECT * FROM job_roles").fetchall()
    return render_template("interview_start.html", roles=roles)


@app.route('/interview/session', methods=['GET', 'POST'])
def interview_session():
    db = get_db()

    if request.method == 'POST':
        questions = session.get('questions', [])
        job_role = session.get('job_role')
        user_id = 1  # Replace with actual logged-in user ID

        cur = db.execute(
            "INSERT INTO interview_sessions (user_id, job_role_id, start_time) VALUES (?, ?, ?)",
            (user_id, job_role, datetime.now())
        )
        session_id = cur.lastrowid
        db.commit()

        total_score = 0

        for i, q in enumerate(questions):
            answer_key = f'answers{i + 1}'
            selected_option = request.form.get(answer_key)
            q_content = q['content']
            correct_option = q.get('correct_answer', None)

            q_row = db.execute("SELECT id FROM questions WHERE content = ?", (q_content,)).fetchone()
            q_id = q_row['id'] if q_row else None
            if not q_id:
                continue

            if selected_option not in ('A', 'B', 'C', 'D'):
                selected_option = None

            is_correct = selected_option == correct_option if selected_option and correct_option else False
            score = 2 if is_correct else 0
            total_score += score

            db.execute("""
                INSERT INTO responses (session_id, question_id, selected_option, correct_option, score, is_correct)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (session_id, q_id, selected_option, correct_option, score, int(is_correct)))

        db.execute("""
            UPDATE interview_sessions SET total_score = ?, end_time = ? WHERE id = ?
        """, (total_score, datetime.now(), session_id))
        db.commit()

        # 🟢 Add result logic
        if total_score > 20:
            session['result_message'] = "🎉 You are ready for the interview!"
            session['retake'] = False
        else:
            session['result_message'] = "⚠️ Try to improve your marks. Please retake the interview."
            session['retake'] = True

        session['score'] = total_score
        session['session_id'] = session_id
        return redirect("/interview/finalize")

    questions = session.get('questions', [])
    return render_template("interview_session.html", questions=questions)



@app.route('/interview/finalize')
def finalize():
    questions = session.get('questions', [])
    score = session.get('score', 0)
    total = len(questions) * 2
    accuracy = round((score / total) * 100, 2) if total else 0
    message = session.get('result_message', '')
    retake = session.get('retake', False)

    return render_template(
        'finalize_interview.html',
        score=score,
        accuracy=accuracy,
        questions=questions,
        message=message,
        retake=retake,
        enumerate=enumerate
    )



@app.route('/feedback', methods=['POST'])  # match form action="/feedback"
def submit_feedback():
    db = get_db()
    user_id = session.get('user_id')  # fetch user id from session
    
    # Get name and email from form (make sure your form includes these fields)
    name = request.form.get('name')
    email = request.form.get('email')
    message = request.form.get('message')

    ratings = []
    for i in range(1, 11):
        rating = request.form.get(f'ux_feedback_{i}')
        ratings.append(int(rating) if rating else None)

    db.execute("""
        INSERT INTO user_feedback (
            user_id, name, email, q1, q2, q3, q4, q5, q6, q7, q8, q9, q10, message
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, name, email, *ratings, message))

    db.commit()
    return render_template("thank_you.html")



@app.route('/scorecard')
def scorecard():
    db = get_db()
    user_id = session.get('user_id', 1)  # for now fallback to 1 if no user session
    
    # Fetch interview sessions with scores for this user
    sessions = db.execute("""
        SELECT 
            isession.id AS session_id,
            jr.name AS job_role,
            isession.start_time,
            isession.end_time,
            isession.total_score,
            (SELECT COUNT(*) FROM responses r WHERE r.session_id = isession.id) AS total_questions
        FROM interview_sessions isession
        JOIN job_roles jr ON jr.id = isession.job_role_id
        WHERE isession.user_id = ?
        ORDER BY isession.start_time DESC
    """, (user_id,)).fetchall()
    
    # Pass the sessions data to template
    return render_template("scorecard.html", sessions=sessions)







#INTERVIEW  FLOW END___________________________________________________________




#resources
def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

# User: View Resources by Job Role
@app.route('/resources')
@login_required
def view_resources():
    conn = get_db()
    cursor = conn.cursor()

    # Fetch all job roles for dropdown
    cursor.execute("SELECT id, name FROM job_roles ORDER BY name")
    job_roles = cursor.fetchall()

    # Extract query parameters
    selected_role_id = request.args.get('role_id', type=int)
    action = request.args.get('action', default='resources')
    selected_role_name = None
    resources = []

    if selected_role_id:
        # Get the selected role name
        cursor.execute("SELECT name FROM job_roles WHERE id = ?", (selected_role_id,))
        role = cursor.fetchone()
        if role:
            selected_role_name = role['name']

            if action == 'resources':
                # Fetch learning resources for selected role
                cursor.execute("""
                    SELECT title, description, url, created_at
                    FROM learning_resources
                    WHERE job_role_id = ?
                    ORDER BY created_at DESC
                """, (selected_role_id,))
                resources = cursor.fetchall()

            elif action == 'qa':
                # Redirect to Q&A page for the selected role
                conn.close()
                return redirect(url_for('ques_ans', role_id=selected_role_id))
        else:
            flash("Selected job role not found.", "warning")

    conn.close()

    return render_template(
        'user/resources.html',
        job_roles=job_roles,
        resources=resources,
        selected_role_id=selected_role_id,
        selected_role_name=selected_role_name,
        action=action
    )
    
    
    
@app.route('/ques_ans')
def ques_ans():
    selected_role_id = request.args.get('role_id', type=int)
    if not selected_role_id:
        return redirect(url_for('dashboard'))  # Or wherever you'd prefer

    conn = get_db()
    cursor = conn.cursor()

    # Get job role name
    cursor.execute("SELECT name FROM job_roles WHERE id = ?", (selected_role_id,))
    role = cursor.fetchone()
    selected_role_name = role['name'] if role else "Unknown Role"

    # Fetch learning resources
    cursor.execute("""
        SELECT title, description, url, created_at
        FROM learning_resources
        WHERE job_role_id = ?
        ORDER BY created_at DESC
    """, (selected_role_id,))
    resources = cursor.fetchall()

    conn.close()

    return render_template(
        'user/ques_ans.html',
        selected_role_id=selected_role_id,
        selected_role_name=selected_role_name,
        resources=resources
    )

    

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')  # optional: handle if you want to store it
        message = request.form.get('message')

        if not name or not email or not phone or not message:
            flash("Please fill out all fields.", "danger")
            return redirect(url_for('contact'))

        # Connect to DB and insert
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        # If your contacts table doesn't have phone column, remove phone from this insert
        cursor.execute(
            "INSERT INTO contacts (name, email, message) VALUES (?, ?, ?)",
            (name, email, message)
        )
        conn.commit()
        conn.close()

        flash("Thank you for contacting us! We'll get back to you soon.", "success")
        return redirect(url_for('contact'))

    # GET request renders the form
    return render_template('contact.html')

@app.route('/privacy_policy')
def privacy_policy():
    return "Privacy Policy page (to be implemented)"

@app.route('/terms_of_service')
def terms_of_service():
    return "Terms of Service page (to be implemented)"

# Logout route
@app.route('/logout')
@login_required
def logout():
    try:
        # Get IP and User Agent
        ip_address = request.remote_addr
        user_agent = request.headers.get('User-Agent')

        # Log the logout activity
        log_user_activity(current_user.id, "Logged out", ip_address, user_agent)
    except Exception as e:
        print("Logging error:", e)  # Optional: log error but don't crash logout

    logout_user()  # Clear session
    flash("You have been logged out.")
    return redirect(url_for('index'))




# --------------------------------------------------------------------------------------------------------------

# Admin login route (fixed credentials)
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, login_user, current_user, logout_user, login_required
from dotenv import load_dotenv
import os
import bcrypt

from forms import SimpleLoginForm

# Load .env
load_dotenv()
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH").encode()

login_manager = LoginManager()
login_manager.init_app(app)

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, id_, name, email, role):
        self.id = id_
        self.name = name
        self.email = email
        self.role = role

    @staticmethod
    def get(user_id):
        # For admin user with id=0 (hardcoded), return User directly
        if user_id == '0':
            return User(0, "Admin", ADMIN_EMAIL, "Admin")
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        if user:
            return User(user[0], user[1], user[2], user[4])
        return None

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated:
        if current_user.role == "Admin":
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('dashboard'))

    form = SimpleLoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        if email == ADMIN_EMAIL and bcrypt.checkpw(password.encode(), ADMIN_PASSWORD_HASH):
            user_obj = User(id_="0", name="Admin", email=email, role="Admin")
            login_user(user_obj)
            flash("Admin logged in successfully", "success")
            return redirect(url_for('admin_dashboard'))
        else:
            flash("Invalid admin credentials", "danger")

    return render_template('auth/admin_login.html', form=form)



#--------------------------------------------------------------ADMIN ROUTES START-----------------------------------------------
@app.before_request
def update_user_last_active():
    if current_user.is_authenticated:
        now = datetime.utcnow()
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET last_active = ? WHERE id = ?", 
            (now, current_user.id)
        )
        conn.commit()
        conn.close()

#Admin dashboard Routes 
from datetime import datetime, timedelta

@app.route('/admin_dashboard')
@login_required
def admin_dashboard():
    if current_user.role != "Admin":
        flash("Access denied!")
        return redirect(url_for('user_login'))

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Total users count
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]

    # Active users: last_active within last 10 minutes
    ten_minutes_ago = datetime.utcnow() - timedelta(minutes=10)
    cursor.execute(
        "SELECT COUNT(*) FROM users WHERE last_active >= ?", 
        (ten_minutes_ago,)
    )
    active_users = cursor.fetchone()[0]

    # Active sessions: count distinct session ids (assuming you have session table)
    # If you track sessions in DB, query accordingly. 
    # Here, we fake active_sessions = active_users for demonstration:
    active_sessions = active_users  

    # Offline users = total - active
    offline_users = total_users - active_users

    # You can also count job_roles if needed
    cursor.execute("SELECT COUNT(*) FROM job_roles")
    total_job_roles = cursor.fetchone()[0]

    conn.close()

    return render_template(
        'admin/admin_dashboard.html',
        total_users=total_users,
        active_users=active_users,
        active_sessions=active_sessions,
        offline_users=offline_users,
        total_job_roles=total_job_roles,
        user=current_user
    )
    

#Manage Users Routes
@app.route('/admin/manage_users')
@login_required
def manage_users():
    if current_user.role != 'Admin':
        flash('Access denied. Admins only.')
        return redirect(url_for('index'))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    
    return render_template('admin/manage_users.html', users=users)

#adding new user route
@app.route('/admin/users/add', methods=['GET', 'POST'])
@login_required
def add_user():
    if current_user.role != 'Admin':
        flash('Access denied. Admins only.')
        return redirect(url_for('index'))

    # Log activity after verifying access
    log_user_activity(
        current_user.id,
        "New user added by admin",
        request.remote_addr,
        request.user_agent.string
    )

    if request.method == 'POST':
        name = request.form.get('full_name')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form['role']

        # Connect to DB
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if user already exists
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        existing_user = cursor.fetchone()

        if existing_user:
            flash('Email already registered.')
            return redirect(url_for('add_user'))

        # Insert new user
        hashed_password = generate_password_hash(password)
        cursor.execute(
            "INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
            (name, email, hashed_password, role)
        )
        conn.commit()

        flash('User added successfully.')
        return redirect(url_for('manage_users'))

    return render_template('admin/add_user.html')



#editing existing users route
@app.route('/admin/users/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    if current_user.role != 'Admin':
        flash('Access denied. Admins only.')
        return redirect(url_for('index'))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()

    if not user:
        flash('User not found.')
        return redirect(url_for('manage_users'))

    if request.method == 'POST':
        name = request.form.get('full_name')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')

        cursor.execute("SELECT * FROM users WHERE email = ? AND id != ?", (email, user_id))
        existing_user = cursor.fetchone()

        if existing_user:
            flash('Email already registered to another user.')

            return redirect(url_for('edit_user', user_id=user_id))

        if password:
            hashed_password = generate_password_hash(password)
        else:
            hashed_password = user['password']  # dict-like access works because of row_factory

        cursor.execute("""
            UPDATE users 
            SET name = ?, email = ?, password = ?, role = ? 
            WHERE id = ?
        """, (name, email, hashed_password, role, user_id))

        conn.commit()

        flash('User updated successfully.')
        return redirect(url_for('manage_users'))

    user_tuple = cursor.execute("SELECT id, name, email, role FROM users WHERE id = ?", (user_id,)).fetchone()

# Convert tuple to dict
    if user_tuple:
        user = {
        'id': user_tuple[0],
        'name': user_tuple[1],
        'email': user_tuple[2],
        'role': user_tuple[3],
    }
    else:
    # handle user not found, e.g. 404 or redirect
        abort(404)

    return render_template('admin/edit_user.html', user=user)



@app.route('/admin/users/delete/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if current_user.role != 'Admin':
        flash('Access denied. Admins only.', 'danger')
        return redirect(url_for('index'))

    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch user by ID
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()

    if user is None:
        abort(404)  # User not found

    # Prevent deleting self
    if user['id'] == current_user.id:
        flash('You cannot delete your own account.', 'warning')
        return redirect(url_for('manage_users'))

    # Delete the user
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()

    flash('User deleted successfully.', 'success')
    return redirect(url_for('manage_users'))

#job roles route
def get_db_connection():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/admin/manage_job_roles', methods=['GET', 'POST'])
def manage_job_roles():
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        # Add new role
        if 'add_role' in request.form:
            role_name = request.form.get('role_name', '').strip()
            if role_name:
                try:
                    cursor.execute("INSERT INTO job_roles (name) VALUES (?)", (role_name,))
                    conn.commit()
                    flash(f'Role "{role_name}" added successfully!', 'success')
                except sqlite3.IntegrityError:
                    flash('Role already exists.', 'danger')
            else:
                flash('Role name cannot be empty.', 'warning')

        # Edit existing role
        elif 'edit_role' in request.form:
            role_id = request.form.get('role_id')
            updated_name = request.form.get('updated_name', '').strip()
            if role_id and updated_name:
                try:
                    cursor.execute("UPDATE job_roles SET name = ? WHERE id = ?", (updated_name, role_id))
                    conn.commit()
                    flash('Role updated successfully.', 'success')
                except sqlite3.IntegrityError:
                    flash('Role name already exists.', 'danger')
            else:
                flash('Invalid data for update.', 'warning')

        # Delete role
        elif 'delete_role' in request.form:
            role_id = request.form.get('role_id')
            if role_id:
                cursor.execute("DELETE FROM job_roles WHERE id = ?", (role_id,))
                conn.commit()
                flash('Role deleted successfully.', 'success')
            else:
                flash('Invalid role ID for deletion.', 'warning')

        return redirect(url_for('manage_job_roles'))

    # GET: fetch roles for display
    cursor.execute("SELECT id, name FROM job_roles ORDER BY id")
    job_roles = cursor.fetchall()
    conn.close()

    return render_template('admin/manage_job_roles.html', job_roles=job_roles)


#monitor 
@app.route('/admin/monitor_activity')
@login_required
def monitor_activity():
    # Restrict access to Admin only
    if current_user.role.lower() != "admin":
        flash("Access denied! Admins only.", "danger")
        return redirect(url_for('index'))

    # Connect to database
    conn = get_db_connection()
    cursor = conn.cursor()

    # Optional: Check table schema (for debugging only)
    # cursor.execute("PRAGMA table_info(user_activity)")
    # print(cursor.fetchall())

    # Join with users table to get user names
    cursor.execute("""
        SELECT ua.user_id, u.name, ua.activity, ua.timestamp, ua.ip_address, ua.user_agent
        FROM user_activity ua
        JOIN users u ON ua.user_id = u.id
        ORDER BY ua.timestamp DESC
    """)
    activities = cursor.fetchall()

    conn.close()

    return render_template('admin/monitor_activity.html', activities=activities)



#manual feedback
from flask import render_template, request, redirect, url_for, flash

@app.route('/manual_feedback', methods=['GET', 'POST'])
def manual_feedback():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')

        # Collect responses to the rating questions
        feedback_responses = {}
        for i in range(1, 11):
            feedback_responses[f'q{i}'] = request.form.get(f'q{i}', '0')  # default to 0 if not selected

        # TODO: Store feedback into DB or process it as needed
        # Example (you can replace this with actual DB logic):
        print("Name:", name)
        print("Email:", email)
        print("Message:", message)
        print("Feedback:", feedback_responses)

        flash("Thanks for your feedback!", "success")
        return redirect(url_for('thank_you_feedback'))  # redirect to thank you page

    return render_template('manual_feedback.html')




# #feedback route is here
@app.route('/send_feedback', methods=['POST'])
def send_feedback():
    # Get form data
    name = request.form.get('name')
    email = request.form.get('email')
    message = request.form.get('message')

    # Get ratings q1 to q10
    ratings = {}
    for i in range(1, 11):
        ratings[f'q{i}'] = request.form.get(f'q{i}')

    # Insert feedback into DB
    conn = get_db_connection()
    conn.execute(
        """
        INSERT INTO feedback
        (name, email, message, q1, q2, q3, q4, q5, q6, q7, q8, q9, q10, submitted_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            name, email, message,
            ratings['q1'], ratings['q2'], ratings['q3'], ratings['q4'], ratings['q5'],
            ratings['q6'], ratings['q7'], ratings['q8'], ratings['q9'], ratings['q10'],
            datetime.utcnow()
        )
    )
    conn.commit()
    conn.close()

    # Redirect to thank you page
    return redirect(url_for('thank_you'))


@app.route('/thank_you')
def thank_you():
    return render_template('thank_you.html')



##uploading Resume Route
DB_NAME = 'users.db'
UPLOAD_FOLDER = 'uploads/resumes'
ALLOWED_EXTENSIONS = {'pdf'}
from werkzeug.utils import secure_filename

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def update_resume_filename(user_id, filename):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET resume_filename = ? WHERE id = ?', (filename, user_id))
    conn.commit()
    conn.close()

@app.route('/upload_resume', methods=['GET', 'POST'])
@login_required
def upload_resume():
    if request.method == 'POST':
        if 'resume_pdf' not in request.files:
            return render_template('dashboard.html', user=current_user, upload_error="No file part in request")

        file = request.files['resume_pdf']

        if file.filename == '':
            return render_template('dashboard.html', user=current_user, upload_error="No file selected")

        if file and allowed_file(file.filename):
            filename = secure_filename(f"{current_user.id}_{file.filename}")
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            
            # Update filename in DB
            update_resume_filename(current_user.id, filename)

            return render_template('user/user_dashboard.html', user=current_user, upload_success="Resume uploaded successfully!")
        else:
            return render_template('user/user_dashboard.html', user=current_user, upload_error="Invalid file format. Only PDFs allowed.")
    
    return render_template('user/user_dashboard.html', user=current_user)




#Manage Resources Route is here
from flask import g
def get_db_connection():
    if 'db' not in g:
        g.db = sqlite3.connect('users.db', check_same_thread=False)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_connection(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()

@app.route('/admin/resources', methods=['GET', 'POST'])
def manage_resources():
    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == 'POST':
        job_role_id = request.form['job_role']
        title = request.form['title']
        description = request.form.get('description', '')
        url = request.form['url']
        created_at = datetime.now().isoformat()

        cur.execute('''
            INSERT INTO learning_resources (job_role_id, title, description, url, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (job_role_id, title, description, url, created_at))
        conn.commit()
        flash('Resource added!')
        return redirect(url_for('manage_resources'))

    cur.execute('SELECT * FROM job_roles ORDER BY name')
    job_roles = cur.fetchall()

    cur.execute('''
        SELECT lr.id, lr.title, lr.description, lr.url, lr.created_at, jr.name AS job_role_name
        FROM learning_resources lr
        JOIN job_roles jr ON lr.job_role_id = jr.id
        ORDER BY lr.created_at DESC
    ''')
    resources = cur.fetchall()
    return render_template('admin/manage_resources.html', resources=resources, job_roles=job_roles)

@app.route('/admin/edit/<int:id>', methods=['GET', 'POST'])
def edit_resource(id):
    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == 'POST':
        job_role_id = request.form['job_role']
        title = request.form['title']
        description = request.form.get('description', '')
        url = request.form['url']
        cur.execute('''
            UPDATE learning_resources
            SET title = ?, description = ?, url = ?, job_role_id = ?
            WHERE id = ?
        ''', (title, description, url, job_role_id, id))
        conn.commit()
        flash('Resource updated!')
        return redirect(url_for('manage_resources'))

    cur.execute('SELECT * FROM learning_resources WHERE id = ?', (id,))
    resource = cur.fetchone()
    if resource is None:
        flash('Resource not found.', 'error')
        return redirect(url_for('manage_resources'))

    cur.execute('SELECT * FROM job_roles ORDER BY name')
    job_roles = cur.fetchall()

    return render_template('admin/edit_resource.html', resource=resource, job_roles=job_roles)

@app.route('/admin/delete/<int:id>', methods=['POST'])
def delete_resource(id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('DELETE FROM learning_resources WHERE id = ?', (id,))
    conn.commit()
    flash('Resource deleted.')
    return redirect(url_for('manage_resources'))


# Admin manage questions
@app.route('/admin/manage_questions')
def manage_questions():
    db = get_db()

    manual_questions = db.execute("""
        SELECT * FROM questions WHERE source_type = 'manual'
    """).fetchall()

    ai_questions = db.execute("""
        SELECT * FROM questions WHERE source_type = 'ai'
    """).fetchall()

    return render_template(
        'admin/manage_questions.html',
        manual_questions=manual_questions,
        ai_questions=ai_questions
    )


@app.route('/admin/questions/add', methods=['GET', 'POST'])
@login_required
def add_question():
    conn = get_db_connection()

    # Fetch job roles
    job_roles = conn.execute('SELECT id, name FROM job_roles').fetchall()

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
            conn.close()
            return render_template('admin/add_question.html', job_roles=job_roles)

        conn.execute('''
            INSERT INTO questions (job_role_id, content, option_a, option_b, option_c, option_d, correct_option, source_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (job_role_id, content, option_a, option_b, option_c, option_d, correct_option, source_type))
        conn.commit()
        conn.close()

        flash("Question added successfully!", "success")
        return redirect(url_for('manage_questions'))

    conn.close()
    return render_template('admin/add_question.html', job_roles=job_roles)



@app.route('/admin/questions/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_question(id):
    conn = get_db_connection()
    question = conn.execute('SELECT * FROM questions WHERE id = ?', (id,)).fetchone()
    job_roles = conn.execute('SELECT id, name FROM job_roles').fetchall()

    if not question:
        flash("Question not found!", "danger")
        conn.close()
        return redirect(url_for('manage_questions'))

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
            conn.close()
            return render_template('admin/edit_question.html', question=question, job_roles=job_roles)

        conn.execute('''
            UPDATE questions
            SET job_role_id = ?, content = ?, option_a = ?, option_b = ?, option_c = ?, option_d = ?, correct_option = ?
            WHERE id = ?
        ''', (job_role_id, content, option_a, option_b, option_c, option_d, correct_option, id))
        conn.commit()
        conn.close()

        flash("Question updated successfully!", "success")
        return redirect(url_for('manage_questions'))

    conn.close()
    return render_template('admin/edit_question.html', question=question, job_roles=job_roles)



@app.route('/admin/questions/delete/<int:id>', methods=['POST'])
@login_required
def delete_question(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM questions WHERE id = ?', (id,))
    conn.commit()
    conn.close()

    flash("Question deleted successfully!", "success")
    return redirect(url_for('manage_questions'))  # ✅ fixed here


@app.route('/admin/delete_all_questions/<source_type>', methods=['POST'])
def delete_all_questions(source_type):
    db = get_db()
    db.execute("DELETE FROM questions WHERE source_type = ?", (source_type,))
    db.commit()
    flash(f"All {source_type.upper()} questions deleted successfully!", "success")
    return redirect(url_for('manage_questions'))



# Admin: Manage Notice
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DB_NAME)
        db.row_factory = sqlite3.Row
    return db


@app.teardown_request
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


# Admin: Add / Edit / View Notices
@app.route('/manage_notice', methods=['GET', 'POST'])
@login_required
def manage_notice():
    if current_user.role.lower() != 'admin':
        flash("Unauthorized access!", "danger")
        return redirect(url_for('notice'))

    db = get_db()

    if request.method == 'POST':
        notice_id = request.form.get('notice_id')
        title = request.form.get('title')
        description = request.form.get('description')
        url = request.form.get('url')

        if not title or not description:
            flash("Title and Description are required.", "warning")
            return redirect(url_for('manage_notice'))

        if notice_id:  # Update
            db.execute(
                "UPDATE notice SET title = ?, description = ?, url = ? WHERE id = ?",
                (title, description, url, notice_id),
            )
            db.commit()
            flash("Notice updated successfully.", "success")
        else:  # Add new
            db.execute(
                "INSERT INTO notice (title, description, url, created_at) VALUES (?, ?, ?, ?)",
                (title, description, url, datetime.utcnow().isoformat()),
            )
            db.commit()
            flash("Notice added successfully.", "success")

        return redirect(url_for('manage_notice'))

    # GET all notices for admin view
    notices = db.execute("SELECT * FROM notice ORDER BY created_at DESC").fetchall()
    return render_template('admin/manage_notice.html', notices=notices)


# Admin: Delete a Notice
@app.route('/delete_notice/<int:notice_id>', methods=['POST'])
@login_required
def delete_notice(notice_id):
    if current_user.role.lower() != 'admin':
        flash("Unauthorized access!", "danger")
        return redirect(url_for('notice'))

    db = get_db()
    db.execute("DELETE FROM notice WHERE id = ?", (notice_id,))
    db.commit()
    flash("Notice deleted successfully.", "success")
    return redirect(url_for('manage_notice'))


# User: View Notices
@app.template_filter('format_datetime')
def format_datetime(value, format='%b %d, %Y'):
    if value is None:
        return ""
    if isinstance(value, str):
        try:
            dt = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')  # adjust format to your DB string format
            return dt.strftime(format)
        except Exception:
            return value  # fallback if parsing fails
    elif hasattr(value, 'strftime'):
        return value.strftime(format)
    return value


@app.route('/notice')
@login_required
def notice():
    db = get_db()  # your method to get DB connection
    notices = db.execute("SELECT * FROM notice ORDER BY created_at DESC").fetchall()
    return render_template('user/notice.html', notices=notices)


# Admin decorator for role check (optional helper)
def admin_required(f):
    @login_required
    def decorated_function(*args, **kwargs):
        if current_user.role.lower() != 'admin':
            flash("Access denied! Admins only.", "danger")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function


@app.route('/admin/view_feedback')
@login_required
def view_feedback():
    db = get_db()
    # Select all feedback records with their id
    feedbacks = db.execute("""
        SELECT
            user_id,
            name,
            email,
            q1, q2, q3, q4, q5, q6, q7, q8, q9, q10,
            message,
            submitted_at
        FROM user_feedback
        ORDER BY submitted_at DESC
    """).fetchall()

    return render_template('admin/view_feedback.html', feedbacks=feedbacks)


@app.route('/admin/view_score')
@login_required
def admin_view_score():
    db = get_db()
    # Join interview_sessions and users for better info display
    scores = db.execute("""
        SELECT 
            s.id as session_id,
            s.user_id,
            jr.name AS job_role,
            s.start_time,
            s.end_time,
            s.total_score
        FROM interview_sessions s
        LEFT JOIN users u ON s.user_id = u.id
        LEFT JOIN job_roles jr ON s.job_role_id = jr.id
        ORDER BY s.start_time DESC
    """).fetchall()

    return render_template('admin/admin_view_score.html', scores=scores)     #ageeeeeeeeeeeeeee


@app.route('/admin/feedback')
@login_required
def admin_feedback():
    # (Add your admin permission check here)
    conn = get_db_connection()
    feedbacks = conn.execute('SELECT * FROM feedback ORDER BY submitted_at DESC').fetchall()
    conn.close()
    return render_template('admin/admin_feedback.html', feedbacks=feedbacks)


@app.route('/admin/logout')
@login_required
def admin_logout():
    if current_user.role != 'admin':
        flash("Unauthorized access.", "danger")
        return redirect(url_for('login'))

    logout_user()
    flash("Logged out successfully.", "success")
    return redirect(url_for('login'))


if __name__ == '__main__':
    init_db()
    app.run(debug=True)
    