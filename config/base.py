# -*- coding: utf-8 -*-
"""
Base configuration class for AiBookkeeping application.

This module provides the base configuration class that contains common settings
shared across all environments (development, production, testing).
"""

import os


class Config:
    """Base configuration class with common settings."""
    
    # Basic Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database settings
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    
    # Upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'csv', 'xlsx', 'xls'}
    
    # Logging settings
    LOG_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    
    # Pagination settings
    POSTS_PER_PAGE = 25
    
    # Mail settings
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_SUBJECT_PREFIX = '[AiBookkeeping] '
    MAIL_SENDER = 'AiBookkeeping Admin <noreply@aiBookkeeping.com>'
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL')
    
    # Cache settings
    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 300
    
    # Security settings
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hour
    
    # Application settings
    APP_NAME = 'AiBookkeeping'
    APP_VERSION = '1.0.0'
    
    @staticmethod
    def init_app(app):
        """Initialize application with this configuration."""
        # Create necessary directories
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(Config.LOG_FOLDER, exist_ok=True)
        
        # Set up basic logging
        if not app.debug and not app.testing:
            import logging
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
            )
    
    @staticmethod
    def get_config_vars():
        """Get all configuration variables for debugging."""
        return {
            key: value for key, value in Config.__dict__.items()
            if not key.startswith('_') and not callable(value)
        }