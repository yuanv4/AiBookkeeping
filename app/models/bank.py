"""Bank model for the Flask application.

This module contains the Bank model class representing financial institutions.
"""

from .base import db, BaseModel
from sqlalchemy.orm import validates
from app.utils.db_utils import BankQueries

class Bank(BaseModel):
    """Bank model representing financial institutions."""
    
    __tablename__ = 'banks'
    
    name = db.Column(db.String(100), nullable=False, unique=True, index=True)
    code = db.Column(db.String(20), unique=True, index=True)  # Bank code (optional)
    
    # Relationships
    accounts = db.relationship('Account', backref='bank', lazy='dynamic', cascade='all, delete-orphan')
    
    @validates('name')
    def validate_name(self, key, name):
        """Validate bank name."""
        if not name or not name.strip():
            raise ValueError('Bank name cannot be empty')
        return name.strip()
    
    @validates('code')
    def validate_code(self, key, code):
        """Validate bank code."""
        if code:
            code = code.strip().upper()
            if len(code) > 20:
                raise ValueError('Bank code cannot exceed 20 characters')
        return code
    
    @classmethod
    def get_by_name(cls, name):
        """Get bank by name."""
        return BankQueries.get_by_name(name)
    
    @classmethod
    def get_by_code(cls, code):
        """Get bank by code."""
        return BankQueries.get_by_code(code)
    
    @classmethod
    def get_or_create(cls, name, code=None):
        """Get existing bank or create new one."""
        return BankQueries.get_or_create(name, code)
    
    def to_dict(self):
        """Convert bank instance to dictionary with additional info."""
        result = super().to_dict()
        return result
    
    def __repr__(self):
        return f'<Bank(id={self.id}, name="{self.name}", code="{self.code}")>'