# -*- coding: utf-8 -*-
"""
Testing environment specific configuration.

This module contains configuration settings optimized for running tests,
including in-memory database, disabled security features, and test-specific settings.
"""

import os
import tempfile
from .base import Config


class TestingConfig(Config):
    """Testing environment configuration."""
    
    # Debug settings
    DEBUG = False
    TESTING = True
    
    # Database settings - use in-memory SQLite for tests
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or 'sqlite://'
    SQLALCHEMY_ECHO = False  # Disable SQL logging during tests
    
    # Security settings - disabled for easier testing
    WTF_CSRF_ENABLED = False
    SECRET_KEY = 'test-secret-key'
    
    # Session settings
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = False
    
    # Logging settings - minimal logging during tests
    LOG_LEVEL = 'CRITICAL'
    LOG_TO_STDOUT = False
    
    # Performance settings
    FLASK_ENV = 'testing'
    
    # File upload settings - use temporary directory
    UPLOAD_FOLDER = tempfile.mkdtemp()
    MAX_CONTENT_LENGTH = 1 * 1024 * 1024  # 1MB for tests
    
    # Test-specific settings
    PRESERVE_CONTEXT_ON_EXCEPTION = False
    TRAP_HTTP_EXCEPTIONS = True
    TRAP_BAD_REQUEST_ERRORS = True
    
    @staticmethod
    def init_app(app):
        """Initialize application for testing environment."""
        Config.init_app(app)
        
        # Disable logging during tests to reduce noise
        import logging
        logging.disable(logging.CRITICAL)
        
        # Ensure upload directory exists
        os.makedirs(TestingConfig.UPLOAD_FOLDER, exist_ok=True)
    
    @staticmethod
    def cleanup():
        """Clean up test resources."""
        import shutil
        if os.path.exists(TestingConfig.UPLOAD_FOLDER):
            shutil.rmtree(TestingConfig.UPLOAD_FOLDER)