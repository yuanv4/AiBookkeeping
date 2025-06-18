"""Flask blueprints package for the Flask application.

This package contains all Flask blueprints for the application.
"""

# 聚合所有蓝图对象
from .main import main_bp
from .transactions import transactions_bp
from .settings import settings_bp
from .income import income_bp

__all__ = [
    'main_bp',
    'transactions_bp',
    'settings_bp',
    'income_bp'
]