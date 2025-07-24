"""Transaction model representing financial transactions"""

from .base import db, BaseModel
from sqlalchemy.orm import validates

class Transaction(BaseModel):
    """交易模型"""
    
    __tablename__ = 'transactions'
    
    # 银行信息（直接嵌入，替代外键关系）
    bank_name = db.Column(db.String(100), nullable=False, index=True)  # 银行名称
    bank_code = db.Column(db.String(20), nullable=True, index=True)  # 银行代码

    # 账户信息（直接嵌入，替代外键关系）
    account_number = db.Column(db.String(50), nullable=False, index=True)  # 账户号码
    account_name = db.Column(db.String(100), nullable=True)  # 账户名称
    account_type = db.Column(db.String(20), default='checking')  # 账户类型

    # 交易基本信息
    date = db.Column(db.Date, nullable=False, index=True)
    amount = db.Column(db.Numeric(15, 2), nullable=False, index=True)
    balance_after = db.Column(db.Numeric(15, 2), nullable=False, index=True)  # 交易后余额
    counterparty = db.Column(db.String(100), nullable=False, index=True)  # 交易对方
    description = db.Column(db.String(200), nullable=False, index=True)  # 交易描述
    currency = db.Column(db.String(3), default='CNY', nullable=False, index=True)
    reference_number = db.Column(db.String(50), index=True)  # 交易参考号

    # 分类信息
    merchant_name = db.Column(db.String(128), nullable=True, index=True)  # 规范化的商家名称
    category = db.Column(db.String(50), nullable=True, index=True, default='other')  # 商户分类

    # 索引优化
    __table_args__ = (
        db.Index('idx_bank_account', 'bank_name', 'account_number'),
        db.Index('idx_account_date', 'account_number', 'date'),
        db.Index('idx_date_amount', 'date', 'amount'),
        db.Index('idx_bank_date', 'bank_name', 'date'),
    )
    

    
    @validates('bank_name')
    def validate_bank_name(self, _key, bank_name):
        """验证银行名称"""
        if not bank_name or not bank_name.strip():
            raise ValueError('银行名称不能为空')
        return bank_name.strip()

    @validates('bank_code')
    def validate_bank_code(self, _key, bank_code):
        """验证银行代码"""
        if bank_code:
            bank_code = bank_code.strip().upper()
            if len(bank_code) > 20:
                raise ValueError('银行代码不能超过20个字符')
        return bank_code

    @validates('account_number')
    def validate_account_number(self, _key, account_number):
        """验证账户号码"""
        if not account_number or not account_number.strip():
            raise ValueError('账户号码不能为空')
        account_number = account_number.strip()
        if len(account_number) > 50:
            raise ValueError('账户号码不能超过50个字符')
        return account_number

    @validates('account_type')
    def validate_account_type(self, _key, account_type):
        """验证账户类型"""
        valid_types = ['checking', 'savings', 'credit', 'investment', 'loan', 'other']
        if account_type and account_type.lower() not in valid_types:
            raise ValueError(f'账户类型必须是以下之一: {", ".join(valid_types)}')
        return account_type.lower() if account_type else 'checking'

    @validates('amount')
    def validate_amount(self, _key, amount):
        """验证交易金额"""
        if amount is None:
            raise ValueError('交易金额不能为空')
        from app.utils import DataUtils
        return DataUtils.normalize_decimal(amount)

    @validates('balance_after')
    def validate_balance_after(self, _key, balance):
        """验证交易后余额"""
        if balance is None:
            return None
        from app.utils import DataUtils
        return DataUtils.normalize_decimal(balance)

    @validates('date')
    def validate_date(self, _key, transaction_date):
        """验证交易日期"""
        if transaction_date is None:
            raise ValueError('交易日期不能为空')

        from datetime import datetime, date
        from app.utils import DataUtils

        # 处理字符串类型的日期
        if isinstance(transaction_date, str):
            parsed_date = DataUtils.parse_date_safe(transaction_date)
            if not parsed_date:
                raise ValueError('无效的日期格式')
            transaction_date = parsed_date
        elif isinstance(transaction_date, datetime):
            transaction_date = transaction_date.date()
        elif not isinstance(transaction_date, date):
            raise ValueError('日期必须是 date、datetime 或有效的日期字符串')

        # 检查未来日期
        if transaction_date > date.today():
            raise ValueError('交易日期不能是未来日期')

        return transaction_date

    @validates('counterparty')
    def validate_counterparty(self, _key, counterparty):
        """验证交易对手"""
        if counterparty is None:
            return None
        if not isinstance(counterparty, str):
            counterparty = str(counterparty)
        counterparty = counterparty.strip()
        if len(counterparty) > 100:
            counterparty = counterparty[:100]
        return counterparty or None

    @validates('description')
    def validate_description(self, _key, description):
        """验证交易描述"""
        if description is None:
            return None
        if not isinstance(description, str):
            description = str(description)
        description = description.strip()
        if len(description) > 200:
            description = description[:200]
        return description or None

    @validates('currency')
    def validate_currency(self, _key, currency):
        """验证货币代码"""
        if not currency:
            return 'CNY'
        if not isinstance(currency, str):
            currency = str(currency)
        currency = currency.strip().upper()
        if len(currency) != 3:
            raise ValueError('货币代码必须是3个字符')
        return currency

    @validates('reference_number')
    def validate_reference_number(self, _key, reference_number):
        """验证参考号"""
        if not reference_number:
            return None
        if not isinstance(reference_number, str):
            reference_number = str(reference_number)
        reference_number = reference_number.strip()
        if len(reference_number) > 50:
            raise ValueError('参考号不能超过50个字符')
        return reference_number

    @validates('category')
    def validate_category(self, _key, category):
        """验证分类字段"""
        if category is None:
            return 'other'

        # 简化验证逻辑，直接检查硬编码分类
        from app.services.category_service import CATEGORIES
        if category in CATEGORIES:
            return category

        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"无效的分类代码: {category}，已设置为默认分类")
        return 'other'
    
    def get_transaction_type(self) -> str:
        """获取交易类型"""
        if self.amount > 0:
            return 'income'
        elif self.amount < 0:
            return 'expense'
        else:
            return 'transfer'

    def is_income(self):
        """是否为收入"""
        return self.amount > 0

    def is_expense(self):
        """是否为支出"""
        return self.amount < 0

    def get_absolute_amount(self):
        """获取绝对金额"""
        return abs(self.amount)

    @classmethod
    def get_by_account(cls, account_number: str):
        """根据账户号码获取交易记录"""
        return cls.query.filter_by(account_number=account_number.strip()).order_by(cls.date.desc()).all()

    @classmethod
    def get_by_bank(cls, bank_name: str):
        """根据银行名称获取交易记录"""
        return cls.query.filter_by(bank_name=bank_name.strip()).order_by(cls.date.desc()).all()

    @classmethod
    def get_account_summary(cls):
        """获取账户汇总信息"""
        from sqlalchemy import func
        return cls.query.with_entities(
            cls.bank_name,
            cls.bank_code,
            cls.account_number,
            cls.account_name,
            cls.account_type,
            cls.currency,
            func.max(cls.balance_after).label('latest_balance'),
            func.max(cls.date).label('latest_date'),
            func.count(cls.id).label('transaction_count')
        ).group_by(
            cls.bank_name,
            cls.account_number
        ).order_by(cls.bank_name, cls.account_number).all()

    @classmethod
    def get_distinct_banks(cls):
        """获取所有不同的银行"""
        from sqlalchemy import func
        return cls.query.with_entities(
            cls.bank_name,
            cls.bank_code
        ).distinct().order_by(cls.bank_name).all()

    @classmethod
    def get_distinct_accounts(cls):
        """获取所有不同的账户"""
        return cls.query.with_entities(
            cls.bank_name,
            cls.account_number,
            cls.account_name,
            cls.account_type
        ).distinct().order_by(cls.bank_name, cls.account_number).all()

    def to_dict(self):
        """转换为字典"""
        result = super().to_dict()
        result['amount'] = float(self.amount)
        result['balance_after'] = float(self.balance_after) if self.balance_after else None
        result['date'] = self.date.isoformat() if self.date else None
        result['is_income'] = self.is_income()
        result['is_expense'] = self.is_expense()
        result['absolute_amount'] = float(self.get_absolute_amount())
        result['merchant_name'] = self.merchant_name
        result['category'] = self.category
        # 添加银行和账户信息
        result['bank_name'] = self.bank_name
        result['bank_code'] = self.bank_code
        result['account_number'] = self.account_number
        result['account_name'] = self.account_name
        result['account_type'] = self.account_type
        return result
    
    def __repr__(self):
        return f'<Transaction(id={self.id}, bank={self.bank_name}, account={self.account_number}, date={self.date}, amount={self.amount})>'
