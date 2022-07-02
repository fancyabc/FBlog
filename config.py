# 应用配置文件
import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard to guess string'
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.qq.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', '465'))
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'True')
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME','2310403052@qq.com')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', 'passwd')
    FLASKY_MAIL_SUBJECT_PREFIX = '[FBlogy]'     
    FLASKY_MAIL_SENDER = '2310403052@qq.com'     
    FLASKY_ADMIN = os.environ.get('FBlogy_ADMIN')     
    SQLALCHEMY_TRACK_MODIFICATIONS = False

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
    