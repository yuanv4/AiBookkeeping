"""Transaction model for the Flask application.

This module contains the Transaction model class representing financial transactions.
"""

from .base import db, BaseModel
from sqlalchemy.orm import validates
from decimal import Decimal
from datetime import datetime, date
import re
import decimal
from typing import Any
from app.utils.db_utils import TransactionQueries

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
    
    # 索引优化
    __table_args__ = (
        db.Index('idx_account_date', 'account_id', 'date'),
        db.Index('idx_date_amount', 'date', 'amount'),
    )
    
    @staticmethod
    def _normalize_decimal(value: Any) -> Decimal:
        """通用金额标准化和转换方法
        
        Args:
            value: 任意类型的金额值（字符串、数字、Decimal等）
            
        Returns:
            Decimal: 标准化后的Decimal金额
            
        Raises:
            ValueError: 当金额格式无效时
        """
        if value is None:
            return None
            
        try:
            # 如果是字符串类型，进行标准化处理
            if isinstance(value, str):
                # 移除所有非数字字符（保留小数点和负号）
                value = re.sub(r'[^\d.-]', '', value.strip())
            
            # 转换为Decimal
            if isinstance(value, (int, float)):
                decimal_value = Decimal(str(value))
            elif not isinstance(value, Decimal):
                decimal_value = Decimal(str(value))
            else:
                decimal_value = value
                
            # 验证精度
            if decimal_value.as_tuple().exponent < -2:
                raise ValueError('金额最多支持2位小数')
                
            return decimal_value
            
        except (ValueError, TypeError, decimal.InvalidOperation) as e:
            raise ValueError(f'无效的金额格式: {value} - {str(e)}')
    
    @validates('amount')
    def validate_amount(self, key, amount):
        """验证交易金额"""
        if amount is None:
            raise ValueError('交易金额不能为空')
        return self._normalize_decimal(amount)
    
    @validates('balance_after')
    def validate_balance_after(self, key, balance):
        """验证交易后余额"""
        # balance_after 可以为空
        if balance is None:
            return None
        return self._normalize_decimal(balance)
    
    @validates('date')
    def validate_date(self, key, transaction_date):
        """Validate transaction date."""
        if transaction_date is None:
            raise ValueError('Transaction date cannot be None')
        
        if isinstance(transaction_date, str):
            try:
                # 尝试解析多种日期格式
                for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%d/%m/%Y', '%d-%m-%Y']:
                    try:
                        transaction_date = datetime.strptime(transaction_date, fmt).date()
                        break
                    except ValueError:
                        continue
                else:
                    raise ValueError('Invalid date format')
            except ValueError:
                raise ValueError('Invalid date format')
        elif isinstance(transaction_date, datetime):
            transaction_date = transaction_date.date()
        elif not isinstance(transaction_date, date):
            raise ValueError('Date must be a date, datetime, or valid date string')
        
        # 检查日期范围
        if transaction_date > date.today():
            raise ValueError('Transaction date cannot be in the future')
        
        return transaction_date
    
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
    
    @validates('description')
    def validate_description(self, key, description):
        """Validate transaction description."""
        if description:
            # 确保description是字符串类型再调用strip()
            if not isinstance(description, str):
                description = str(description)
            description = description.strip()
            if len(description) > 200:
                raise ValueError('Description cannot exceed 200 characters')
        return description
    
    @validates('counterparty')
    def validate_counterparty(self, key, counterparty):
        """Validate counterparty."""
        if counterparty:
            # 确保counterparty是字符串类型再调用strip()
            if not isinstance(counterparty, str):
                counterparty = str(counterparty)
            counterparty = counterparty.strip()
            if len(counterparty) > 100:
                raise ValueError('Counterparty cannot exceed 100 characters')
        return counterparty
    
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
    
    @classmethod
    def get_by_account(cls, account_id, start_date=None, end_date=None, limit=None, offset=None):
        """Get transactions by account with optional date filtering."""
        return TransactionQueries.get_by_account(account_id, start_date, end_date, limit, offset)
    
    @classmethod
    def get_by_type(cls, transaction_type, start_date=None, end_date=None):
        """Get transactions by type with optional date filtering."""
        return TransactionQueries.get_by_type(transaction_type, start_date, end_date)
    
    @classmethod
    def search(cls, keyword, account_id=None, start_date=None, end_date=None):
        """Search transactions by keyword in description or counterparty."""
        return TransactionQueries.search(keyword, account_id, start_date, end_date)
    
    @classmethod
    def get_income_transactions(cls, account_id=None, start_date=None, end_date=None):
        """Get income transactions (positive amounts)."""
        return TransactionQueries.get_income_transactions(account_id, start_date, end_date)
    
    @classmethod
    def get_expense_transactions(cls, account_id=None, start_date=None, end_date=None):
        """Get expense transactions (negative amounts)."""
        return TransactionQueries.get_expense_transactions(account_id, start_date, end_date)
    
    @classmethod
    def get_summary_by_type(cls, account_id=None, start_date=None, end_date=None):
        """Get transaction summary grouped by type."""
        return TransactionQueries.get_summary_by_type(account_id, start_date, end_date)
    
    @classmethod
    def get_monthly_summary(cls, account_id=None, year=None):
        """Get monthly transaction summary."""
        return TransactionQueries.get_monthly_summary(account_id, year)
    
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
        """Convert transaction instance to dictionary with additional info."""
        result = super().to_dict()
        result['amount'] = float(self.amount)
        result['balance_after'] = float(self.balance_after) if self.balance_after else None
        result['date'] = self.date.isoformat() if self.date else None
        result['is_income'] = self.is_income()
        result['is_expense'] = self.is_expense()
        result['absolute_amount'] = float(self.get_absolute_amount())

        result['account_name'] = self.account.account_name if self.account else None
        result['bank_name'] = self.account.bank.name if self.account and self.account.bank else None
        result['transaction_type'] = self.get_transaction_type()
        return result
    
    def __repr__(self):
        return f'<Transaction(id={self.id}, account_id={self.account_id}, date={self.date}, amount={self.amount})>'