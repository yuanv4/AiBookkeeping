# -*- coding: utf-8 -*-
"""
Tests for configuration management.

This module tests the configuration classes and their behavior
across different environments.
"""

import os
import pytest
from config import (
    Config, DevelopmentConfig, ProductionConfig, TestingConfig,
    config, get_config
)


class TestBaseConfig:
    """Test the base configuration class."""
    
    def test_config_has_required_attributes(self):
        """Test that base config has all required attributes."""
        required_attrs = [
            'SECRET_KEY', 'SQLALCHEMY_TRACK_MODIFICATIONS',
            'MAX_CONTENT_LENGTH', 'UPLOAD_FOLDER', 'LOG_FOLDER'
        ]
        
        for attr in required_attrs:
            assert hasattr(Config, attr), f"Config missing required attribute: {attr}"
    
    def test_config_init_app(self, app):
        """Test that config.init_app works correctly."""
        Config.init_app(app)
        
        # Check that directories are created
        assert os.path.exists(Config.UPLOAD_FOLDER)
        assert os.path.exists(Config.LOG_FOLDER)
    
    def test_get_config_vars(self):
        """Test that get_config_vars returns configuration variables."""
        config_vars = Config.get_config_vars()
        
        assert isinstance(config_vars, dict)
        assert 'SECRET_KEY' in config_vars
        assert 'UPLOAD_FOLDER' in config_vars


class TestDevelopmentConfig:
    """Test the development configuration."""
    
    def test_development_config_inherits_from_base(self):
        """Test that DevelopmentConfig inherits from Config."""
        assert issubclass(DevelopmentConfig, Config)
    
    def test_development_config_debug_enabled(self):
        """Test that debug is enabled in development."""
        assert DevelopmentConfig.DEBUG is True
        assert DevelopmentConfig.TESTING is False
    
    def test_development_config_database_uri(self):
        """Test development database URI."""
        assert 'data-dev.db' in DevelopmentConfig.SQLALCHEMY_DATABASE_URI
    
    def test_development_config_templates_auto_reload(self):
        """Test that templates auto-reload is enabled."""
        assert DevelopmentConfig.TEMPLATES_AUTO_RELOAD is True
    
    def test_development_config_sql_echo(self):
        """Test that SQL echo is enabled for development."""
        assert DevelopmentConfig.SQLALCHEMY_ECHO is True


class TestProductionConfig:
    """Test the production configuration."""
    
    def test_production_config_inherits_from_base(self):
        """Test that ProductionConfig inherits from Config."""
        assert issubclass(ProductionConfig, Config)
    
    def test_production_config_debug_disabled(self):
        """Test that debug is disabled in production."""
        assert ProductionConfig.DEBUG is False
        assert ProductionConfig.TESTING is False
    
    def test_production_config_database_uri(self):
        """Test production database URI."""
        assert 'data.db' in ProductionConfig.SQLALCHEMY_DATABASE_URI
    
    def test_production_config_sql_echo_disabled(self):
        """Test that SQL echo is disabled for production."""
        assert ProductionConfig.SQLALCHEMY_ECHO is False
    
    def test_production_config_security_settings(self):
        """Test production security settings."""
        assert ProductionConfig.SESSION_COOKIE_SECURE is True
        assert ProductionConfig.SESSION_COOKIE_HTTPONLY is True
        assert ProductionConfig.SESSION_COOKIE_SAMESITE == 'Lax'
    
    def test_production_config_requires_secret_key(self, monkeypatch):
        """Test that production config requires SECRET_KEY environment variable."""
        # Remove SECRET_KEY from environment
        monkeypatch.delenv('SECRET_KEY', raising=False)
        
        # Mock app for testing
        class MockApp:
            logger = None
        
        app = MockApp()
        
        # Should raise ValueError when SECRET_KEY is not set
        with pytest.raises(ValueError, match="SECRET_KEY environment variable must be set"):
            ProductionConfig.init_app(app)


class TestTestingConfig:
    """Test the testing configuration."""
    
    def test_testing_config_inherits_from_base(self):
        """Test that TestingConfig inherits from Config."""
        assert issubclass(TestingConfig, Config)
    
    def test_testing_config_testing_enabled(self):
        """Test that testing is enabled."""
        assert TestingConfig.TESTING is True
        assert TestingConfig.DEBUG is False
    
    def test_testing_config_in_memory_database(self):
        """Test that testing uses in-memory database."""
        assert TestingConfig.SQLALCHEMY_DATABASE_URI == 'sqlite://'
    
    def test_testing_config_csrf_disabled(self):
        """Test that CSRF is disabled for testing."""
        assert TestingConfig.WTF_CSRF_ENABLED is False
    
    def test_testing_config_security_relaxed(self):
        """Test that security settings are relaxed for testing."""
        assert TestingConfig.SESSION_COOKIE_SECURE is False
        assert TestingConfig.SESSION_COOKIE_HTTPONLY is False
    
    def test_testing_config_upload_folder_is_temp(self):
        """Test that upload folder is temporary directory."""
        import tempfile
        assert TestingConfig.UPLOAD_FOLDER.startswith(tempfile.gettempdir())


class TestConfigMapping:
    """Test the configuration mapping and helper functions."""
    
    def test_config_mapping_contains_all_environments(self):
        """Test that config mapping contains all environments."""
        expected_keys = ['development', 'production', 'testing', 'default']
        
        for key in expected_keys:
            assert key in config, f"Config mapping missing key: {key}"
    
    def test_config_mapping_values_are_classes(self):
        """Test that config mapping values are configuration classes."""
        assert config['development'] == DevelopmentConfig
        assert config['production'] == ProductionConfig
        assert config['testing'] == TestingConfig
        assert config['default'] == DevelopmentConfig
    
    def test_get_config_with_explicit_name(self):
        """Test get_config with explicit configuration name."""
        assert get_config('development') == DevelopmentConfig
        assert get_config('production') == ProductionConfig
        assert get_config('testing') == TestingConfig
    
    def test_get_config_with_invalid_name(self):
        """Test get_config with invalid configuration name."""
        assert get_config('invalid') == DevelopmentConfig  # Should return default
    
    def test_get_config_with_environment_variable(self, monkeypatch):
        """Test get_config using FLASK_ENV environment variable."""
        monkeypatch.setenv('FLASK_ENV', 'production')
        assert get_config() == ProductionConfig
        
        monkeypatch.setenv('FLASK_ENV', 'testing')
        assert get_config() == TestingConfig
    
    def test_get_config_defaults_to_development(self, monkeypatch):
        """Test that get_config defaults to development when no env var is set."""
        monkeypatch.delenv('FLASK_ENV', raising=False)
        assert get_config() == DevelopmentConfig


class TestConfigIntegration:
    """Integration tests for configuration with Flask app."""
    
    def test_config_applied_to_app(self, app):
        """Test that configuration is properly applied to Flask app."""
        # App should be using TestingConfig (from conftest.py)
        assert app.config['TESTING'] is True
        assert app.config['WTF_CSRF_ENABLED'] is False
        assert app.config['SQLALCHEMY_DATABASE_URI'] == 'sqlite://'
    
    def test_config_directories_created(self, app):
        """Test that configuration creates necessary directories."""
        upload_folder = app.config['UPLOAD_FOLDER']
        log_folder = app.config['LOG_FOLDER']
        
        assert os.path.exists(upload_folder)
        assert os.path.exists(log_folder)