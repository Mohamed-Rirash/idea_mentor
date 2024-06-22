import os

from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.environ.get("client_id", None)
CLIENT_SECRET = os.environ.get("client_secret", None)
SECRET_KEY = os.environ.get("secret_key", None)
EMAIL_SENDER = os.environ.get("email_sender", None)
EMAIL_PASSWORD = os.environ.get("email_password", None)
OTP_SECRET_KEY = os.environ.get("otp_secret_key", None)
SQLALCHEMY_DATABASE_URL = os.environ.get("sqlalchemy_database_url", None)
ALGORITHM = os.environ.get("algorithm", None)
AUTH_SECRET = os.environ.get("auth_secret_key", None)
SQLALCHEMY_DATABASE_URL = os.environ.get("SQLALCHEMY_DATABASE_URL", None)
