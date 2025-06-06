# -*- coding: utf-8 -*-
"""
Development environment specific configuration.

This module contains configuration settings optimized for local development,
including debug settings, database configurations, and development tools.
"""

import os
from .base import Config


class DevelopmentConfig(Config):
    """Development environment configuration."""
    
    # Debug settings
    DEBUG = True
    TESTING = False
    
    # Database settings
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data-dev.db')
    SQLALCHEMY_ECHO = True  # Log all SQL statements
    
    # Template settings
    TEMPLATES_AUTO_RELOAD = True
    EXPLAIN_TEMPLATE_LOADING = False
    
    # Security settings (relaxed for development)
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None
    
    # Logging settings
    LOG_LEVEL = 'DEBUG'
    LOG_TO_STDOUT = True
    
    # Development tools
    FLASK_ENV = 'development'
    
    # File upload settings
    MAX_CONTENT_LENGTH = 32 * 1024 * 1024  # 32MB for development
    
    @staticmethod
    def init_app(app):
        """Initialize application for development environment."""
        Config.init_app(app)
        
        # Setup development logging
        import logging
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        )
        
        # Enable SQL query logging
        logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)