# models/user_session.py
from flask_login import UserMixin
from utils.db import get_db_connection
import os

ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")

class User(UserMixin):
    def __init__(self, id, name, email, role):
        self.id = id
        self.name = name
        self.email = email
        self.role = role

    @staticmethod
    def get(user_id):
        # Hardcoded admin
        if str(user_id) == '0':
            return User(0, "Admin", ADMIN_EMAIL, "Admin")

        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
                user = cursor.fetchone()
                if user:
                    return User(user['id'], user['name'], user['email'], user['role'])
        finally:
            conn.close()
        return None
