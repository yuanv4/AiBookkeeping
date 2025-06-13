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

class Transaction(BaseModel):
    """Transaction model representing financial transactions."""
    
    __tablename__ = 'transactions'
    
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=False, index=True)
    transaction_type = db.Column(db.String(50), nullable=False, index=True)
    date = db.Column(db.Date, nullable=False, index=True)
    amount = db.Column(db.Numeric(15, 2), nullable=False, index=True)
    currency = db.Column(db.String(3), default='CNY', nullable=False)
    description = db.Column(db.String(200))
    counterparty = db.Column(db.String(100), index=True)  # 交易对方
    reference_number = db.Column(db.String(50), index=True)  # 交易参考号
    balance_after = db.Column(db.Numeric(15, 2))  # 交易后余额
    is_verified = db.Column(db.Boolean, default=False)  # 是否已核实
    is_reconciled = db.Column(db.Boolean, default=False)  # 是否已对账
    tags = db.Column(db.String(200))  # 标签，用逗号分隔
    location = db.Column(db.String(100))  # 交易地点
    
    # 索引优化
    __table_args__ = (
        db.Index('idx_account_date', 'account_id', 'date'),
        db.Index('idx_date_amount', 'date', 'amount'),
        db.Index('idx_type_date', 'transaction_type', 'date'),
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
            currency = currency.strip().upper()
            if len(currency) != 3:
                raise ValueError('Currency code must be 3 characters')
        return currency or 'CNY'
    
    @validates('description')
    def validate_description(self, key, description):
        """Validate transaction description."""
        if description:
            description = description.strip()
            if len(description) > 200:
                raise ValueError('Description cannot exceed 200 characters')
        return description
    
    @validates('counterparty')
    def validate_counterparty(self, key, counterparty):
        """Validate counterparty."""
        if counterparty:
            counterparty = counterparty.strip()
            if len(counterparty) > 100:
                raise ValueError('Counterparty cannot exceed 100 characters')
        return counterparty
    
    @validates('reference_number')
    def validate_reference_number(self, key, reference_number):
        """Validate reference number."""
        if reference_number:
            reference_number = reference_number.strip()
            if len(reference_number) > 50:
                raise ValueError('Reference number cannot exceed 50 characters')
        return reference_number
    
    @validates('tags')
    def validate_tags(self, key, tags):
        """Validate tags."""
        if tags:
            tags = tags.strip()
            if len(tags) > 200:
                raise ValueError('Tags cannot exceed 200 characters')
            # 验证标签格式（逗号分隔）
            tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
            tags = ','.join(tag_list)
        return tags
    
    @classmethod
    def get_by_account(cls, account_id, start_date=None, end_date=None, limit=None, offset=None):
        """Get transactions by account with optional date filtering."""
        query = cls.query.filter_by(account_id=account_id)
        
        if start_date:
            query = query.filter(cls.date >= start_date)
        if end_date:
            query = query.filter(cls.date <= end_date)
        
        query = query.order_by(cls.date.desc(), cls.created_at.desc())
        
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    @classmethod
    def get_by_type(cls, transaction_type, start_date=None, end_date=None):
        """Get transactions by type with optional date filtering."""
        query = cls.query.filter_by(transaction_type=transaction_type)
        
        if start_date:
            query = query.filter(cls.date >= start_date)
        if end_date:
            query = query.filter(cls.date <= end_date)
        
        return query.order_by(cls.date.desc()).all()
    
    @classmethod
    def search(cls, keyword, account_id=None, start_date=None, end_date=None):
        """Search transactions by keyword in description or counterparty."""
        query = cls.query
        
        if account_id:
            query = query.filter_by(account_id=account_id)
        
        if start_date:
            query = query.filter(cls.date >= start_date)
        if end_date:
            query = query.filter(cls.date <= end_date)
        
        # 搜索关键词
        search_filter = db.or_(
            cls.description.ilike(f'%{keyword}%'),
            cls.counterparty.ilike(f'%{keyword}%')
        )
        query = query.filter(search_filter)
        
        return query.order_by(cls.date.desc()).all()
    
    @classmethod
    def get_income_transactions(cls, account_id=None, start_date=None, end_date=None):
        """Get income transactions (positive amounts)."""
        query = cls.query.filter(cls.amount > 0)
        
        if account_id:
            query = query.filter_by(account_id=account_id)
        if start_date:
            query = query.filter(cls.date >= start_date)
        if end_date:
            query = query.filter(cls.date <= end_date)
        
        return query.order_by(cls.date.desc()).all()
    
    @classmethod
    def get_expense_transactions(cls, account_id=None, start_date=None, end_date=None):
        """Get expense transactions (negative amounts)."""
        query = cls.query.filter(cls.amount < 0)
        
        if account_id:
            query = query.filter_by(account_id=account_id)
        if start_date:
            query = query.filter(cls.date >= start_date)
        if end_date:
            query = query.filter(cls.date <= end_date)
        
        return query.order_by(cls.date.desc()).all()
    
    @classmethod
    def get_summary_by_type(cls, account_id=None, start_date=None, end_date=None):
        """Get transaction summary grouped by type."""
        query = db.session.query(
            cls.transaction_type,
            db.func.count(cls.id).label('count'),
            db.func.sum(cls.amount).label('total')
        )
        
        if account_id:
            query = query.filter(cls.account_id == account_id)
        if start_date:
            query = query.filter(cls.date >= start_date)
        if end_date:
            query = query.filter(cls.date <= end_date)
        
        results = query.group_by(cls.transaction_type).all()
        
        # 转换结果格式以保持向后兼容
        formatted_results = []
        for transaction_type, count, total in results:
            # 简单判断收入/支出类型（基于金额正负）
            is_income = total > 0 if total else False
            formatted_results.append({
                'name': transaction_type,
                'is_income': is_income,
                'count': count,
                'total': total
            })
        
        return sorted(formatted_results, key=lambda x: x['name'])
    
    @classmethod
    def get_monthly_summary(cls, account_id=None, year=None):
        """Get monthly transaction summary."""
        if not year:
            year = date.today().year
        
        query = db.session.query(
            db.extract('month', cls.date).label('month'),
            db.func.sum(db.case((cls.amount > 0, cls.amount), else_=0)).label('income'),
            db.func.sum(db.case((cls.amount < 0, cls.amount), else_=0)).label('expense'),
            db.func.count(cls.id).label('count')
        ).filter(db.extract('year', cls.date) == year)
        
        if account_id:
            query = query.filter(cls.account_id == account_id)
        
        return query.group_by(db.extract('month', cls.date)).order_by('month').all()
    
    def get_tags_list(self):
        """Get tags as a list."""
        if not self.tags:
            return []
        return [tag.strip() for tag in self.tags.split(',') if tag.strip()]
    
    def is_income(self):
        """Check if this is an income transaction."""
        return self.amount > 0
    
    def is_expense(self):
        """Check if this is an expense transaction."""
        return self.amount < 0
    
    def get_absolute_amount(self):
        """Get absolute amount value."""
        return abs(self.amount)
    
    def mark_verified(self):
        """Mark transaction as verified."""
        self.is_verified = True
        self.save()
    
    def mark_reconciled(self):
        """Mark transaction as reconciled."""
        self.is_reconciled = True
        self.save()
    
    def to_dict(self):
        """Convert transaction instance to dictionary with additional info."""
        result = super().to_dict()
        result['amount'] = float(self.amount)
        result['balance_after'] = float(self.balance_after) if self.balance_after else None
        result['date'] = self.date.isoformat() if self.date else None
        result['is_income'] = self.is_income()
        result['is_expense'] = self.is_expense()
        result['absolute_amount'] = float(self.get_absolute_amount())
        result['tags_list'] = self.get_tags_list()
        result['account_name'] = self.account.account_name if self.account else None
        result['bank_name'] = self.account.bank.name if self.account and self.account.bank else None
        result['transaction_type_name'] = self.transaction_type if self.transaction_type else None
        result['transaction_type_is_income'] = self.is_income() if self.transaction_type else None
        return result
    
    def __repr__(self):
        return f'<Transaction(id={self.id}, account_id={self.account_id}, date={self.date}, amount={self.amount})>'