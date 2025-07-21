"""Account model for the Flask application.

This module contains the Account model class representing bank accounts.
"""

from .base import db, BaseModel
from sqlalchemy.orm import validates
from decimal import Decimal
from typing import Optional, Dict, Any
from datetime import date

class Account(BaseModel):
    """Account model representing bank accounts."""
    
    __tablename__ = 'accounts'
    
    bank_id = db.Column(db.Integer, db.ForeignKey('banks.id'), nullable=False, index=True)
    account_number = db.Column(db.String(50), nullable=False, index=True)
    account_name = db.Column(db.String(100))
    currency = db.Column(db.String(3), default='CNY', nullable=False)
    account_type = db.Column(db.String(20), default='checking')  # checking, savings, credit, etc.
    
    # Relationships
    transactions = db.relationship('Transaction', backref='account', lazy='dynamic', cascade='all, delete-orphan')
    
    # Unique constraint for bank_id and account_number combination
    __table_args__ = (
        db.UniqueConstraint('bank_id', 'account_number', name='uq_bank_account'),
    )
    
    @validates('account_number')
    def validate_account_number(self, key, account_number):
        """Validate account number."""
        if not account_number:
            raise ValueError('Account number cannot be empty')
        if not account_number.strip():
            raise ValueError('Account number cannot be empty')
        account_number = account_number.strip()
        if len(account_number) > 50:
            raise ValueError('Account number cannot exceed 50 characters')
        return account_number
    
    @validates('currency')
    def validate_currency(self, key, currency):
        """Validate currency code."""
        if currency:
            currency = currency.strip().upper()
            if len(currency) != 3:
                raise ValueError('Currency code must be 3 characters')
        return currency or 'CNY'
    
    @validates('account_type')
    def validate_account_type(self, key, account_type):
        """Validate account type."""
        valid_types = ['checking', 'savings', 'credit', 'investment', 'loan', 'other']
        if account_type and account_type.lower() not in valid_types:
            raise ValueError(f'Account type must be one of: {", ".join(valid_types)}')
        return account_type.lower() if account_type else 'checking'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert account instance to dictionary."""
        result = super().to_dict()
        result['bank_name'] = self.bank.name if self.bank else None
        return result
    
    def __repr__(self):
        return f'<Account(id={self.id}, bank_id={self.bank_id}, number="{self.account_number}", name="{self.account_name}")>'