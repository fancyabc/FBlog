# 应用配置文件
import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard to guess string'
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.qq.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', '465'))
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'True')
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME','2211@qq.com')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', 'pass')
    FBLOG_MAIL_SUBJECT_PREFIX = '[FBlog]'     
    FBLOG_MAIL_SENDER = '12121@qq.com'     
    FBLOG_ADMIN = os.environ.get('FBLOG_ADMIN')     
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_PATH = os.path.join(basedir, 'uploads')
    AVATARS_SAVE_PATH = os.path.join(UPLOAD_PATH, 'avatars')
    AVATARS_SIZE_TUPLE = (30, 100, 200)
    AVATARS_SERVE_LOCAL = True

    @staticmethod
    def init_app(app):
        pass

class DevelopmentConfig(Config):     
    DEBUG = True     
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'data-dev.sqlite')


class TestingConfig(Config):     
    TESTING = True
    WTF_CSRF_ENABLED = False     
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
        'sqlite://'  
    

class ProductionConfig(Config):     
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'data.sqlite')  


    
config = {
    'development': DevelopmentConfig,     
    'testing': TestingConfig,     
    'production': ProductionConfig,
    'default': DevelopmentConfig 
}
    