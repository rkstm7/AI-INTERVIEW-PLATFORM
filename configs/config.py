# configs/config.py
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    # Secret Key
    SECRET_KEY = os.getenv("SECRET_KEY", "default_secret_key")

    # Database connection string (MySQL + SQLAlchemy)
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{os.getenv('DB_USER', 'root')}:{os.getenv('DB_PASSWORD', '')}"
        f"@{os.getenv('DB_HOST', 'localhost')}/{os.getenv('DB_NAME', 'ai_interview_platform')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # OpenAI API key
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    # Admin credentials
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
    ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH")


# Optional: For development
class DevelopmentConfig(Config):
    DEBUG = True


# Optional: For production
class ProductionConfig(Config):
    DEBUG = False
