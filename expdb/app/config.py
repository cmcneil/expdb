# config.py
import os

class Config:
    DB_USER = os.getenv('DB_USER', 'expdb')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'alchemical')
    DB_HOST = os.getenv('DB_HOST', 'expdb.c.alembiclabs.internal')
    DB_NAME = os.getenv('DB_NAME', 'expdb')
    
    SQLALCHEMY_DATABASE_URI = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
    SECRET_KEY = os.getenv('SECRET_KEY', 'a-secure-default-key')

class DevelopmentConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.getenv('DEV_DATABASE_URL', 'sqlite:///dev_db.sqlite')  # SQLite for development
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False

def get_config():
    env = os.getenv('FLASK_ENV', 'development')
    if env == 'development':
        return DevelopmentConfig
    return ProductionConfig