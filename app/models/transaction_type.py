"""Transaction Type model for the Flask application.

This module contains the TransactionType model class representing transaction categories.
"""

from .base import db, BaseModel
from sqlalchemy.orm import validates

class TransactionType(BaseModel):
    """Transaction Type model representing transaction categories."""
    
    __tablename__ = 'transaction_types'
    
    name = db.Column(db.String(50), nullable=False, unique=True, index=True)
    is_income = db.Column(db.Boolean, nullable=False, default=False, index=True)
    description = db.Column(db.Text)
    color = db.Column(db.String(7))  # Hex color code for UI display
    icon = db.Column(db.String(50))  # Icon name for UI display
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    sort_order = db.Column(db.Integer, default=0)  # For custom ordering
    parent_id = db.Column(db.Integer, db.ForeignKey('transaction_types.id'))  # For hierarchical categories
    
    # Relationships
    transactions = db.relationship('Transaction', backref='transaction_type', lazy='dynamic')
    children = db.relationship('TransactionType', backref=db.backref('parent', remote_side='TransactionType.id'), lazy='dynamic')
    
    @validates('name')
    def validate_name(self, key, name):
        """Validate transaction type name."""
        if not name or not name.strip():
            raise ValueError('Transaction type name cannot be empty')
        name = name.strip()
        if len(name) > 50:
            raise ValueError('Transaction type name cannot exceed 50 characters')
        return name
    
    @validates('color')
    def validate_color(self, key, color):
        """Validate hex color code."""
        if color:
            color = color.strip()
            if not color.startswith('#') or len(color) != 7:
                raise ValueError('Color must be a valid hex color code (e.g., #FF0000)')
            try:
                int(color[1:], 16)  # Validate hex format
            except ValueError:
                raise ValueError('Color must be a valid hex color code')
        return color
    
    @validates('sort_order')
    def validate_sort_order(self, key, sort_order):
        """Validate sort order."""
        if sort_order is not None and sort_order < 0:
            raise ValueError('Sort order must be non-negative')
        return sort_order or 0
    
    @classmethod
    def get_by_name(cls, name):
        """Get transaction type by name."""
        return cls.query.filter_by(name=name.strip()).first()
    
    @classmethod
    def get_or_create(cls, name, is_income=False, description=None, color=None, icon=None):
        """Get existing transaction type or create new one."""
        transaction_type = cls.get_by_name(name)
        if not transaction_type:
            transaction_type = cls.create(
                name=name,
                is_income=is_income,
                description=description,
                color=color,
                icon=icon
            )
        return transaction_type
    
    @classmethod
    def get_income_types(cls):
        """Get all income transaction types."""
        return cls.query.filter_by(is_income=True, is_active=True).order_by(cls.sort_order, cls.name).all()
    
    @classmethod
    def get_expense_types(cls):
        """Get all expense transaction types."""
        return cls.query.filter_by(is_income=False, is_active=True).order_by(cls.sort_order, cls.name).all()
    
    @classmethod
    def get_active_types(cls, is_income=None):
        """Get all active transaction types, optionally filtered by income/expense."""
        query = cls.query.filter_by(is_active=True)
        if is_income is not None:
            query = query.filter_by(is_income=is_income)
        return query.order_by(cls.sort_order, cls.name).all()
    
    @classmethod
    def get_root_types(cls):
        """Get all root-level transaction types (no parent)."""
        return cls.query.filter_by(parent_id=None, is_active=True).order_by(cls.sort_order, cls.name).all()
    
    @classmethod
    def create_default_types(cls):
        """Create default transaction types if they don't exist."""
        default_types = [
            # Income types
            {'name': '工资', 'is_income': True, 'color': '#4CAF50', 'icon': 'salary', 'sort_order': 1},
            {'name': '奖金', 'is_income': True, 'color': '#8BC34A', 'icon': 'bonus', 'sort_order': 2},
            {'name': '投资收益', 'is_income': True, 'color': '#CDDC39', 'icon': 'investment', 'sort_order': 3},
            {'name': '兼职收入', 'is_income': True, 'color': '#FFEB3B', 'icon': 'part-time', 'sort_order': 4},
            {'name': '其他收入', 'is_income': True, 'color': '#FFC107', 'icon': 'other-income', 'sort_order': 5},
            
            # Expense types
            {'name': '餐饮', 'is_income': False, 'color': '#FF9800', 'icon': 'restaurant', 'sort_order': 1},
            {'name': '交通', 'is_income': False, 'color': '#FF5722', 'icon': 'transport', 'sort_order': 2},
            {'name': '购物', 'is_income': False, 'color': '#F44336', 'icon': 'shopping', 'sort_order': 3},
            {'name': '娱乐', 'is_income': False, 'color': '#E91E63', 'icon': 'entertainment', 'sort_order': 4},
            {'name': '医疗', 'is_income': False, 'color': '#9C27B0', 'icon': 'medical', 'sort_order': 5},
            {'name': '教育', 'is_income': False, 'color': '#673AB7', 'icon': 'education', 'sort_order': 6},
            {'name': '住房', 'is_income': False, 'color': '#3F51B5', 'icon': 'housing', 'sort_order': 7},
            {'name': '通讯', 'is_income': False, 'color': '#2196F3', 'icon': 'communication', 'sort_order': 8},
            {'name': '保险', 'is_income': False, 'color': '#03A9F4', 'icon': 'insurance', 'sort_order': 9},
            {'name': '其他支出', 'is_income': False, 'color': '#607D8B', 'icon': 'other-expense', 'sort_order': 10},
        ]
        
        created_count = 0
        for type_data in default_types:
            if not cls.get_by_name(type_data['name']):
                cls.create(**type_data)
                created_count += 1
        
        return created_count
    
    def get_transactions_count(self):
        """Get the number of transactions for this type."""
        return self.transactions.count()
    
    def get_total_amount(self, start_date=None, end_date=None):
        """Get total amount for this transaction type within date range."""
        from .transaction import Transaction
        query = self.transactions
        if start_date:
            query = query.filter(Transaction.date >= start_date)
        if end_date:
            query = query.filter(Transaction.date <= end_date)
        
        total = query.with_entities(db.func.sum(Transaction.amount)).scalar()
        return total or 0.00
    
    def get_children_recursive(self):
        """Get all child transaction types recursively."""
        children = []
        for child in self.children:
            children.append(child)
            children.extend(child.get_children_recursive())
        return children
    
    def deactivate(self):
        """Deactivate the transaction type instead of deleting."""
        self.is_active = False
        self.save()
    
    def activate(self):
        """Activate the transaction type."""
        self.is_active = True
        self.save()
    
    def to_dict(self):
        """Convert transaction type instance to dictionary with additional info."""
        result = super().to_dict()
        result['transactions_count'] = self.get_transactions_count()
        result['total_amount'] = float(self.get_total_amount())
        result['parent_name'] = self.parent.name if self.parent else None
        result['children_count'] = self.children.count()
        return result
    
    def __repr__(self):
        return f'<TransactionType(id={self.id}, name="{self.name}", is_income={self.is_income})>'