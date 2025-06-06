# -*- coding: utf-8 -*-
"""
Configuration management module for AiBookkeeping application.

This module provides configuration classes for different environments:
- DevelopmentConfig: For local development
- ProductionConfig: For production deployment
- TestingConfig: For running tests
"""

import os
from typing import Dict, Any

# Import configuration classes
from .base import Config
from .development import DevelopmentConfig
from .production import ProductionConfig
from .testing import TestingConfig


# Configuration mapping
config: Dict[str, Any] = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config(config_name: str = None) -> Config:
    """Get configuration class by name.
    
    Args:
        config_name: Name of the configuration ('development', 'production', 'testing')
                    If None, uses FLASK_ENV environment variable or defaults to 'development'
    
    Returns:
        Configuration class instance
    """
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    return config.get(config_name, config['default'])


# Export all configuration classes for direct import
__all__ = [
    'Config',
    'DevelopmentConfig', 
    'ProductionConfig',
    'TestingConfig',
    'config',
    'get_config'
]