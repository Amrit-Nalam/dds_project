import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'development_secret_key')
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:password@localhost/caterquest'
    SQLALCHEMY_TRACK_MODIFICATIONS = False