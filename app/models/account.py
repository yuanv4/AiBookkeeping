"""Account model for double-entry bookkeeping"""

from .base import db, BaseModel
from sqlalchemy.orm import validates

class Account(BaseModel):
    """资金账户模型"""
    
    __tablename__ = 'accounts'
    
    # 账户基本信息
    name = db.Column(db.String(100), nullable=False, index=True)
    type = db.Column(db.String(20), nullable=False)  # ASSET, LIABILITY, INCOME, EXPENSE, EQUITY
    currency = db.Column(db.String(3), default='CNY', nullable=False)
    
    # 账户标识 (用于自动匹配)
    bank_name = db.Column(db.String(100))      # 例如: "招商银行"
    account_number = db.Column(db.String(100), index=True) # 例如: 卡号或支付宝ID
    
    # 余额 (缓存值，实际应由 Entry 计算，但在 SQLite 且无复杂并发下，存个快照查询更快)
    balance = db.Column(db.Numeric(15, 2), default=0)
    
    # 关系
    entries = db.relationship('Entry', back_populates='account', lazy='dynamic')

    __table_args__ = (
        # 同一个银行的同一个卡号必须唯一
        db.UniqueConstraint('bank_name', 'account_number', name='uq_account_identity'),
    )

    @validates('type')
    def validate_type(self, _key, type_val):
        valid_types = ['ASSET', 'LIABILITY', 'INCOME', 'EXPENSE', 'EQUITY']
        if type_val not in valid_types:
            raise ValueError(f"Invalid account type. Must be one of {valid_types}")
        return type_val

    def __repr__(self):
        return f'<Account(name={self.name}, type={self.type}, balance={self.balance})>'

