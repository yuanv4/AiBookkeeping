"""Bank model for the Flask application.

This module contains the Bank model class representing financial institutions.
"""

from .base import db, BaseModel
from sqlalchemy.orm import validates

class Bank(BaseModel):
    """Bank model representing financial institutions."""
    
    __tablename__ = 'banks'
    
    name = db.Column(db.String(100), nullable=False, unique=True, index=True)
    code = db.Column(db.String(20), unique=True, index=True)  # Bank code (optional)
    country = db.Column(db.String(50), default='CN')  # Country code
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
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
        return cls.query.filter_by(name=name.strip()).first()
    
    @classmethod
    def get_by_code(cls, code):
        """Get bank by code."""
        if not code:
            return None
        return cls.query.filter_by(code=code.strip().upper()).first()
    
    @classmethod
    def get_or_create(cls, name, code=None, country='CN'):
        """Get existing bank or create new one."""
        bank = cls.get_by_name(name)
        if not bank:
            bank = cls.create(name=name, code=code, country=country)
        return bank
    
    @classmethod
    def get_active_banks(cls):
        """Get all active banks."""
        return cls.query.filter_by(is_active=True).order_by(cls.name).all()
    
    def get_accounts_count(self):
        """Get the number of accounts for this bank."""
        return self.accounts.count()
    
    def get_total_balance(self):
        """Get total balance across all accounts for this bank."""
        from .transaction import Transaction
        total = 0
        for account in self.accounts:
            balance = db.session.query(db.func.sum(Transaction.amount)).filter_by(account_id=account.id).scalar()
            if balance:
                total += balance
        return total
    
    def deactivate(self):
        """Deactivate the bank instead of deleting."""
        self.is_active = False
        self.save()
    
    def activate(self):
        """Activate the bank."""
        self.is_active = True
        self.save()
    
    def to_dict(self):
        """Convert bank instance to dictionary with additional info."""
        result = super().to_dict()
        result['accounts_count'] = self.get_accounts_count()
        result['total_balance'] = self.get_total_balance()
        return result
    
    def __repr__(self):
        return f'<Bank(id={self.id}, name="{self.name}", code="{self.code}")>'