"""Transaction model for the Flask application.

This module contains the Transaction model class representing financial transactions.
"""

from .base import db, BaseModel
from sqlalchemy.orm import validates
from decimal import Decimal
from datetime import datetime, date
import logging
from typing import Any

class Transaction(BaseModel):
    """Transaction model representing financial transactions."""
    
    __tablename__ = 'transactions'
    
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=False, index=True)
    date = db.Column(db.Date, nullable=False, index=True)
    amount = db.Column(db.Numeric(15, 2), nullable=False, index=True)
    balance_after = db.Column(db.Numeric(15, 2), nullable=False, index=True)  # 交易后余额
    counterparty = db.Column(db.String(100), nullable=False, index=True)  # 交易对方
    description = db.Column(db.String(200), nullable=False, index=True)  # 交易描述
    currency = db.Column(db.String(3), default='CNY', nullable=False, index=True)
    reference_number = db.Column(db.String(50), index=True)  # 交易参考号
    merchant_name = db.Column(db.String(128), nullable=True, index=True)  # 规范化的商家名称
    category = db.Column(db.String(50), nullable=True, index=True, default='other')  # 商户分类
    
    # 索引优化
    __table_args__ = (
        db.Index('idx_account_date', 'account_id', 'date'),
        db.Index('idx_date_amount', 'date', 'amount'),
    )
    

    
    @validates('amount')
    def validate_amount(self, key, amount):
        """验证交易金额"""
        if amount is None:
            raise ValueError('交易金额不能为空')
        from app.utils import DataUtils
        return DataUtils.normalize_decimal(amount)

    @validates('balance_after')
    def validate_balance_after(self, key, balance):
        """验证交易后余额"""
        # balance_after 可以为空
        if balance is None:
            return None
        from app.utils import DataUtils
        return DataUtils.normalize_decimal(balance)
    
    @validates('date')
    def validate_date(self, key, transaction_date):
        """Validate transaction date."""
        if transaction_date is None:
            raise ValueError('Transaction date cannot be None')
        
        # 处理字符串类型的日期
        if isinstance(transaction_date, str):
            from app.utils import DataUtils
            parsed_date = DataUtils.parse_date_safe(transaction_date)
            if not parsed_date:
                raise ValueError('Invalid date format')
            transaction_date = parsed_date
        elif isinstance(transaction_date, datetime):
            transaction_date = transaction_date.date()
        elif not isinstance(transaction_date, date):
            raise ValueError('Date must be a date, datetime, or valid date string')
        
        # 检查日期范围
        if transaction_date > date.today():
            raise ValueError('Transaction date cannot be in the future')
        
        return transaction_date

    @validates('counterparty')
    def validate_counterparty(self, key, counterparty):
        """验证交易对手"""
        if counterparty is None:
            return None

        if not isinstance(counterparty, str):
            counterparty = str(counterparty)

        counterparty = counterparty.strip()
        if not counterparty:
            return None

        # 限制长度
        if len(counterparty) > 200:
            counterparty = counterparty[:200]

        return counterparty

    @validates('description')
    def validate_description(self, key, description):
        """验证交易描述"""
        if description is None:
            return None

        if not isinstance(description, str):
            description = str(description)

        description = description.strip()
        if not description:
            return None

        # 限制长度
        if len(description) > 500:
            description = description[:500]

        return description
    
    @validates('currency')
    def validate_currency(self, key, currency):
        """Validate currency code."""
        if currency:
            # 确保currency是字符串类型再调用strip()
            if not isinstance(currency, str):
                currency = str(currency)
            currency = currency.strip().upper()
            if len(currency) != 3:
                raise ValueError('Currency code must be 3 characters')
        return currency or 'CNY'
    

    
    @validates('reference_number')
    def validate_reference_number(self, key, reference_number):
        """Validate reference number."""
        if reference_number:
            # 确保reference_number是字符串类型再调用strip()
            if not isinstance(reference_number, str):
                reference_number = str(reference_number)
            reference_number = reference_number.strip()
            if len(reference_number) > 50:
                raise ValueError('Reference number cannot exceed 50 characters')
        return reference_number

    @validates('category')
    def validate_category(self, key, category):
        """验证商户分类"""
        if category:
            # 确保category是字符串类型再调用strip()
            if not isinstance(category, str):
                category = str(category)
            category = category.strip().lower()
            if len(category) > 50:
                raise ValueError('Category cannot exceed 50 characters')

            # 验证分类是否在有效列表中
            valid_categories = {
                'dining', 'transport', 'shopping', 'services',
                'healthcare', 'finance', 'other'
            }
            if category not in valid_categories:
                # 如果分类无效，记录警告并使用默认值
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"无效的商户分类: {category}, 使用默认值 'other'")
                category = 'other'

        return category or 'other'
    
    def get_transaction_type(self) -> str:
        """Get transaction type based on amount.
        
        Returns:
            str: 'income' for positive amounts, 'expense' for negative amounts, 'transfer' for zero
        """
        if self.amount > 0:
            return 'income'
        elif self.amount < 0:
            return 'expense'
        else:
            return 'transfer'
    
    def is_income(self):
        """Check if this is an income transaction."""
        return self.amount > 0
    
    def is_expense(self):
        """Check if this is an expense transaction."""
        return self.amount < 0
    
    def get_absolute_amount(self):
        """Get absolute amount value."""
        return abs(self.amount)
    
    def to_dict(self):
        """Convert transaction instance to dictionary."""
        result = super().to_dict()
        result['amount'] = float(self.amount)
        result['balance_after'] = float(self.balance_after) if self.balance_after else None
        result['date'] = self.date.isoformat() if self.date else None
        result['is_income'] = self.is_income()
        result['is_expense'] = self.is_expense()
        result['absolute_amount'] = float(self.get_absolute_amount())
        result['merchant_name'] = self.merchant_name
        result['category'] = self.category
        return result
    
    def __repr__(self):
        return f'<Transaction(id={self.id}, account_id={self.account_id}, date={self.date}, amount={self.amount})>'




