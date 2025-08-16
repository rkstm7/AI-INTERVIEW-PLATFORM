# utils/db.py
import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    return pymysql.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', ''),
        db=os.getenv('DB_NAME', 'ai_interview_platform'),
        cursorclass=pymysql.cursors.DictCursor,
        charset='utf8mb4',
        autocommit=True   # ensures inserts/updates commit automatically
    )
