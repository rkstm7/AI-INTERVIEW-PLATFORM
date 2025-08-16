# routes/auth/user_login.py
from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request,
    current_app,
    session,
)
from flask_login import current_user, login_user
from models.model import User, Role
from extensions import bcrypt
from forms.login_form import SimpleLoginForm
from utils import get_db_connection, log_user_activity
import pymysql.cursors
from oauthlib.oauth2 import WebApplicationClient
import urllib.parse
import requests
import json
from datetime import datetime
from uuid import uuid4
from configs.config import Config
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

user_login_bp = Blueprint("user_login", __name__, url_prefix="/auth")


# ---------------------- Standard Email/Password Login ----------------------
@user_login_bp.route("/user_login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("user_dashboard.dashboard"))

    form = SimpleLoginForm()

    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        conn = get_db_connection()
        try:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            user_data = cursor.fetchone()
        finally:
            conn.close()

        # Check if user exists and password hash is valid
        if user_data and user_data.get("password"):
            try:
                password_matches = bcrypt.check_password_hash(
                    user_data["password"], password
                )
            except ValueError:
                flash("Login failed. Password stored in database is invalid.", "danger")
                return redirect(url_for("user_login.login"))

            if password_matches:
                # Fetch Role object
                role = Role.query.get(user_data["role_id"])
                if not role or role.role_name.lower() != "user":
                    flash("This is User Login. You don't have User role.", "warning")
                    return redirect(url_for("user_login.login"))

                # Create Flask-Login user object
                user_obj = User()
                user_obj.id = user_data["id"]
                user_obj.username = user_data["username"]
                user_obj.email = user_data["email"]
                user_obj.role_id = role.id
                user_obj.role_obj = role

                login_user(user_obj)

                # Log activity
                ip_address = request.remote_addr
                user_agent = request.headers.get("User-Agent")
                log_user_activity(user_obj.id, "Logged in", ip_address, user_agent)

                flash("User logged in successfully.", "success")
                return redirect(url_for("user_dashboard.dashboard"))

        flash("Login failed. Check your credentials.", "danger")
        return redirect(url_for("user_login.login"))

    return render_template("public/login/user_login.html", form=form)


# Google OAuth setup
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"


def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()


# ---------------------- Google OAuth ----------------------
@user_login_bp.route("/google-login")
def google_login():
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    client = WebApplicationClient(current_app.config["GOOGLE_CLIENT_ID"])
    state = str(uuid4())
    session["oauth_state"] = state

    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=url_for("user_login.google_callback", _external=True),
        scope=["openid", "email", "profile"],
        state=state,
    )
    return redirect(request_uri)


@user_login_bp.route("/google-callback")
def google_callback():
    if request.args.get("state") != session.get("oauth_state"):
        flash("Invalid OAuth state.", "danger")
        return redirect(url_for("user_login.login"))

    code = request.args.get("code")
    if not code:
        flash("Google login failed: No authorization code.", "danger")
        return redirect(url_for("user_login.login"))

    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]

    client = WebApplicationClient(current_app.config["GOOGLE_CLIENT_ID"])

    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=url_for("user_login.google_callback", _external=True),
        code=code,
    )
    body += f"&client_id={current_app.config['GOOGLE_CLIENT_ID']}&client_secret={current_app.config['GOOGLE_CLIENT_SECRET']}"
    token_response = requests.post(token_url, headers=headers, data=body).json()

    if "error" in token_response:
        flash(
            f"Google login error: {token_response.get('error_description')}", "danger"
        )
        return redirect(url_for("user_login.login"))

    client.parse_request_body_response(json.dumps(token_response))
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body).json()

    if not userinfo_response.get("email_verified"):
        flash("Google account email not verified.", "danger")
        return redirect(url_for("user_login.login"))

    email = userinfo_response["email"]
    name = userinfo_response.get("name", "Google User")
    unique_id = userinfo_response.get("sub")

    # Database logic
    conn = get_db_connection()
    try:
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        base_username = email.split("@")[0]
        username = base_username
        counter = 1

        while True:
            cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
            if not cursor.fetchone():
                break
            username = f"{base_username}{counter}"
            counter += 1

        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user_data = cursor.fetchone()

        if not user_data:
            # Get role_id for "User"
            role = Role.query.filter_by(name="User").first()
            role_id = role.id if role else None

            cursor.execute(
                """
                INSERT INTO users (name, username, email, role_id, password, created_at, last_active)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    name,
                    username,
                    email,
                    role_id,
                    bcrypt.generate_password_hash("oauth_user_" + unique_id).decode(
                        "utf-8"
                    ),
                    datetime.utcnow(),
                    datetime.utcnow(),
                ),
            )
            conn.commit()
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            user_data = cursor.fetchone()
        else:
            cursor.execute(
                "UPDATE users SET last_active = %s WHERE id = %s",
                (datetime.utcnow(), user_data["id"]),
            )
            conn.commit()
    finally:
        conn.close()

    # Create Flask-Login object
    role = Role.query.filter_by(id=user_data["role_id"]).first()
    user_obj = User()
    user_obj.id = user_data["id"]
    user_obj.name = user_data["name"]
    user_obj.username = user_data["username"]
    user_obj.email = user_data["email"]
    user_obj.role_id = role.id if role else None
    user_obj.role_obj = role

    login_user(user_obj)
    flash("Logged in with Google successfully!", "success")
    return redirect(url_for("user_dashboard.dashboard"))


# ---------------------- Facebook OAuth ----------------------
@user_login_bp.route("/facebook-login")
def facebook_login():
    fb_auth_base = "https://www.facebook.com/v10.0/dialog/oauth"
    state = str(uuid4())
    session["oauth_state"] = state
    params = {
        "client_id": current_app.config.get("FACEBOOK_CLIENT_ID"),
        "redirect_uri": url_for("user_login.facebook_callback", _external=True),
        "scope": "email",
        "response_type": "code",
        "state": state,
    }
    url = f"{fb_auth_base}?{urllib.parse.urlencode(params)}"
    return redirect(url)


@user_login_bp.route("/facebook-callback")
def facebook_callback():
    if request.args.get("state") != session.get("oauth_state"):
        flash("Invalid OAuth state.", "danger")
        return redirect(url_for("user_login.login"))

    code = request.args.get("code")
    if not code:
        flash("Facebook login failed.", "danger")
        return redirect(url_for("user_login.login"))

    token_url = "https://graph.facebook.com/v10.0/oauth/access_token"
    params = {
        "client_id": current_app.config.get("FACEBOOK_CLIENT_ID"),
        "client_secret": current_app.config.get("FACEBOOK_CLIENT_SECRET"),
        "redirect_uri": url_for("user_login.facebook_callback", _external=True),
        "code": code,
    }
    token_res = requests.get(token_url, params=params).json()

    if "error" in token_res:
        flash("Facebook login error.", "danger")
        return redirect(url_for("user_login.login"))

    access_token = token_res.get("access_token")
    user_info = requests.get(
        "https://graph.facebook.com/me?fields=id,name,email",
        params={"access_token": access_token},
    ).json()

    email = user_info.get("email")
    name = user_info.get("name")

    conn = get_db_connection()
    try:
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user_data = cursor.fetchone()
    finally:
        conn.close()

    if not user_data:
        flash("No user associated with this Facebook account.", "danger")
        return redirect(url_for("user_login.login"))

    role = Role.query.filter_by(id=user_data["role_id"]).first()
    user_obj = User()
    user_obj.id = user_data["id"]
    user_obj.name = user_data["name"]
    user_obj.email = user_data["email"]
    user_obj.username = user_data["username"]
    user_obj.role_id = role.id if role else None
    user_obj.role_obj = role

    login_user(user_obj)
    flash("Logged in with Facebook.", "success")
    return redirect(url_for("user_dashboard.dashboard"))


# ---------------------- Microsoft OAuth ----------------------
@user_login_bp.route("/microsoft-login")
def microsoft_login():
    ms_auth_base = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
    state = str(uuid4())
    session["oauth_state"] = state
    params = {
        "client_id": current_app.config.get("MICROSOFT_CLIENT_ID"),
        "response_type": "code",
        "redirect_uri": url_for("user_login.microsoft_callback", _external=True),
        "response_mode": "query",
        "scope": "User.Read",
        "state": state,
    }
    url = f"{ms_auth_base}?{urllib.parse.urlencode(params)}"
    return redirect(url)


@user_login_bp.route("/microsoft-callback")
def microsoft_callback():
    if request.args.get("state") != session.get("oauth_state"):
        flash("Invalid OAuth state.", "danger")
        return redirect(url_for("user_login.login"))

    code = request.args.get("code")
    if not code:
        flash("Microsoft login failed.", "danger")
        return redirect(url_for("user_login.login"))

    token_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
    data = {
        "client_id": current_app.config.get("MICROSOFT_CLIENT_ID"),
        "client_secret": current_app.config.get("MICROSOFT_CLIENT_SECRET"),
        "code": code,
        "redirect_uri": url_for("user_login.microsoft_callback", _external=True),
        "grant_type": "authorization_code",
    }
    token_res = requests.post(token_url, data=data).json()

    if "error" in token_res:
        flash("Microsoft login error.", "danger")
        return redirect(url_for("user_login.login"))

    access_token = token_res.get("access_token")
    user_info = requests.get(
        "https://graph.microsoft.com/v1.0/me",
        headers={"Authorization": f"Bearer {access_token}"},
    ).json()

    email = user_info.get("mail") or user_info.get("userPrincipalName")
    name = user_info.get("displayName")

    conn = get_db_connection()
    try:
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user_data = cursor.fetchone()
    finally:
        conn.close()

    if not user_data:
        flash("No user associated with this Microsoft account.", "danger")
        return redirect(url_for("user_login.login"))

    role = Role.query.filter_by(id=user_data["role_id"]).first()
    user_obj = User()
    user_obj.id = user_data["id"]
    user_obj.name = user_data["name"]
    user_obj.email = user_data["email"]
    user_obj.username = user_data["username"]
    user_obj.role_id = role.id if role else None
    user_obj.role_obj = role

    login_user(user_obj)
    flash("Logged in with Microsoft.", "success")
    return redirect(url_for("user_dashboard.dashboard"))
