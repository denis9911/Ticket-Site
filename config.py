import os
from dotenv import load_dotenv

load_dotenv()  

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key'
    DIGISELLER_SELLER_ID = os.environ.get("DIGISELLER_SELLER_ID")
    DIGISELLER_API_KEY = os.environ.get("DIGISELLER_API_KEY")
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(basedir, 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
