# -*- coding: utf-8 -*-
"""
Production environment specific configuration.

This module contains configuration settings optimized for production deployment,
including security settings, performance optimizations, and logging configurations.
"""

import os
from .base import Config


class ProductionConfig(Config):
    """Production environment configuration."""
    
    # Debug settings
    DEBUG = False
    TESTING = False
    
    # Database settings
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data.db')
    SQLALCHEMY_ECHO = False  # Disable SQL logging in production
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 300,
        'pool_pre_ping': True
    }
    
    # Security settings
    SECRET_KEY = os.environ.get('SECRET_KEY')
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hour
    
    # Session settings
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Logging settings
    LOG_LEVEL = 'INFO'
    LOG_TO_STDOUT = False
    
    # Performance settings
    FLASK_ENV = 'production'
    SEND_FILE_MAX_AGE_DEFAULT = 31536000  # 1 year cache for static files
    
    # File upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB for production
    
    @classmethod
    def init_app(cls, app):
        """Initialize application for production environment."""
        Config.init_app(app)
        
        # Ensure secret key is set
        if not cls.SECRET_KEY:
            raise ValueError('SECRET_KEY environment variable must be set for production')
        
        # Setup production logging
        import logging
        from logging.handlers import RotatingFileHandler, SMTPHandler
        
        # Create logs directory if it doesn't exist
        if not os.path.exists(cls.LOG_FOLDER):
            os.makedirs(cls.LOG_FOLDER)
        
        # File handler for general logs
        file_handler = RotatingFileHandler(
            os.path.join(cls.LOG_FOLDER, 'aiBookkeeping.log'),
            maxBytes=10240000,  # 10MB
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
        # Error handler for critical errors
        error_handler = RotatingFileHandler(
            os.path.join(cls.LOG_FOLDER, 'errors.log'),
            maxBytes=10240000,  # 10MB
            backupCount=5
        )
        error_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        error_handler.setLevel(logging.ERROR)
        app.logger.addHandler(error_handler)
        
        # Email handler for critical errors (if configured)
        mail_server = os.environ.get('MAIL_SERVER')
        if mail_server:
            auth = None
            if os.environ.get('MAIL_USERNAME') or os.environ.get('MAIL_PASSWORD'):
                auth = (os.environ.get('MAIL_USERNAME'), os.environ.get('MAIL_PASSWORD'))
            secure = None
            if os.environ.get('MAIL_USE_TLS'):
                secure = ()
            mail_handler = SMTPHandler(
                mailhost=(mail_server, int(os.environ.get('MAIL_PORT') or 587)),
                fromaddr=os.environ.get('MAIL_FROM_ADDR'),
                toaddrs=os.environ.get('ADMINS', '').split(','),
                subject='AiBookkeeping Application Error',
                credentials=auth,
                secure=secure
            )
            mail_handler.setLevel(logging.ERROR)
            app.logger.addHandler(mail_handler)
        
        app.logger.setLevel(logging.INFO)
        app.logger.info('AiBookkeeping production startup')