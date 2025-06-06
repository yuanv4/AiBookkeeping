# -*- coding: utf-8 -*-
"""
Pytest configuration and fixtures for AiBookkeeping tests.

This module provides common test fixtures and configuration for all test modules.
"""

import os
import sys
import tempfile
import pytest
from flask import Flask

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from config import TestingConfig


@pytest.fixture(scope='session')
def app():
    """Create application for the tests."""
    # Create a temporary directory for test uploads
    test_upload_dir = tempfile.mkdtemp()
    
    # Override upload folder for tests
    TestingConfig.UPLOAD_FOLDER = test_upload_dir
    
    # Create the Flask application
    app = create_app('testing')
    
    # Establish an application context
    with app.app_context():
        yield app
    
    # Cleanup
    import shutil
    if os.path.exists(test_upload_dir):
        shutil.rmtree(test_upload_dir)


@pytest.fixture(scope='function')
def client(app):
    """Create a test client for the Flask application."""
    return app.test_client()


@pytest.fixture(scope='function')
def runner(app):
    """Create a test runner for the Flask application's Click commands."""
    return app.test_cli_runner()


@pytest.fixture(scope='function')
def db(app):
    """Create a clean database for each test."""
    from flask_sqlalchemy import SQLAlchemy
    
    # Import db from app if it exists
    try:
        from app.models import db as _db
        db = _db
    except ImportError:
        # If models don't exist yet, create a basic db instance
        db = SQLAlchemy()
        db.init_app(app)
    
    with app.app_context():
        db.create_all()
        yield db
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope='function')
def session(db):
    """Create a database session for the test."""
    connection = db.engine.connect()
    transaction = connection.begin()
    
    options = dict(bind=connection, binds={})
    session = db.create_scoped_session(options=options)
    
    db.session = session
    
    yield session
    
    transaction.rollback()
    connection.close()
    session.remove()


@pytest.fixture
def auth_headers():
    """Provide authentication headers for API tests."""
    return {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }


@pytest.fixture
def sample_upload_file():
    """Create a sample file for upload tests."""
    import io
    
    # Create a simple CSV content
    csv_content = "Date,Description,Amount\n2024-01-01,Test Transaction,100.00\n"
    
    return {
        'file': (io.BytesIO(csv_content.encode('utf-8')), 'test.csv'),
        'content': csv_content
    }


@pytest.fixture
def sample_transaction_data():
    """Provide sample transaction data for tests."""
    return {
        'date': '2024-01-01',
        'description': 'Test Transaction',
        'amount': 100.00,
        'category': 'Test Category',
        'type': 'income'
    }


# Pytest configuration
def pytest_configure(config):
    """Configure pytest settings."""
    # Add custom markers
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m "not slow"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        # Add 'unit' marker to all tests by default
        if not any(marker.name in ['integration', 'slow'] for marker in item.iter_markers()):
            item.add_marker(pytest.mark.unit)