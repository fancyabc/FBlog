# 应用配置文件
import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard to guess string'
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.qq.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', '465'))
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'True')
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME','@qq.com')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', 'pass')
    FBLOG_MAIL_SUBJECT_PREFIX = '[FBlog]'     
    FBLOG_MAIL_SENDER = MAIL_USERNAME     
    FBLOG_ADMIN = os.environ.get('FBLOG_ADMIN')     
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    FBLOG_POSTS_PER_PAGE = 20
    FBLOG_FOLLOWERS_PER_PAGE = 10
    FBLOG_COMMENTS_PER_PAGE = 10

    UPLOAD_PATH = os.path.join(basedir, 'uploads')
    AVATARS_SAVE_PATH = os.path.join(UPLOAD_PATH, 'avatars')
    AVATARS_SIZE_TUPLE = (30, 100, 200)
    AVATARS_SERVE_LOCAL = True

    SQLALCHEMY_RECORD_QUERIES = True # 启用缓慢查询记录功能的配置
    FBLOG_SLOW_DB_QUERY_TIME = 0.5

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

    @classmethod     
    def init_app(cls, app):         
        Config.init_app(app)          
        # 出错时邮件通知管理员         
        import logging         
        from logging.handlers import SMTPHandler         
        credentials = None         
        secure = None         
        if getattr(cls, 'MAIL_USERNAME', None) is not None:             
            credentials = (cls.MAIL_USERNAME, cls.MAIL_PASSWORD)             
            if getattr(cls, 'MAIL_USE_TLS', None):                 
                secure = ()         
        mail_handler = SMTPHandler(
            mailhost=(cls.MAIL_SERVER, cls.MAIL_PORT),             
            fromaddr=cls.FBLOG_MAIL_SENDER,             
            toaddrs=[cls.FBLOG_ADMIN],             
            subject=cls.FBLOG_MAIL_SUBJECT_PREFIX + ' Application Error',             
            credentials=credentials,
            secure=secure)         
        mail_handler.setLevel(logging.ERROR)         
        app.logger.addHandler(mail_handler)
        

config = {
    'development': DevelopmentConfig,     
    'testing': TestingConfig,     
    'production': ProductionConfig,
    'default': DevelopmentConfig 
}
    