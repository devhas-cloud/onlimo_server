import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'change-this-to-a-secure-random-string')
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{os.getenv('DB_USER', 'onlimo')}:"
        f"{os.getenv('DB_PASSWORD', 'onlimo_db_pass_2026')}@"
        f"{os.getenv('DB_HOST', 'localhost')}:"
        f"{os.getenv('DB_PORT', '3306')}/"
        f"{os.getenv('DB_NAME', 'onlimo_dlh')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    FTP_ROOT = os.getenv('FTP_ROOT', '/home/onlimo')
    ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')