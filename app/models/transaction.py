"""Transaction model representing financial transactions"""

from .base import db, BaseModel
from sqlalchemy.orm import validates

class Transaction(BaseModel):
    """交易模型"""
    
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
        """验证商户分类"""
        # 获取有效分类列表
        from app.utils import get_valid_category_codes
        valid_categories = set(get_valid_category_codes())

        # 处理空分类
        if not category:
            return 'other' if 'other' in valid_categories else list(valid_categories)[0]

        # 标准化分类值
        if not isinstance(category, str):
            category = str(category)
        category = category.strip().lower()

        # 验证分类有效性
        if category not in valid_categories:
            raise ValueError(f"无效的商户分类: {category}")

        return category
    
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
        return result
    
    def __repr__(self):
        return f'<Transaction(id={self.id}, account_id={self.account_id}, date={self.date}, amount={self.amount})>'
