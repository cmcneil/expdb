# config.py
import os

class Config:
    DB_USER = os.getenv('DB_USER', 'expdb')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'alchemical')
    DB_HOST = os.getenv('DB_HOST', '35.230.24.99')
    DB_NAME = os.getenv('DB_NAME', 'expdb')
    
    SQLALCHEMY_DATABASE_URI = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv('SECRET_KEY', 'a-secure-default-key')
    GS_BUCKET_NAME = os.getenv('GS_BUCKET_NAME', 'expdb')
    UPLOAD_FOLDER = 'uploads'

class DevelopmentConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DEV_DATABASE_URL', 
        f"sqlite:///{os.path.join(os.getcwd(), 'dev_db.sqlite')}")  # SQLite for development
    GS_BUCKET_NAME = 'expdb_dev'
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False

def get_config():
    env = os.getenv('FLASK_ENV', 'development')
    if env == 'development':
        return DevelopmentConfig
    return ProductionConfig