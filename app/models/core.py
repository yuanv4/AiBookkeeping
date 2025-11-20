"""Core Transaction and Entry models for double-entry bookkeeping"""

from .base import db, BaseModel
from sqlalchemy.orm import validates
from sqlalchemy.dialects.sqlite import JSON
from datetime import datetime

class CoreTransaction(BaseModel):
    """交易事件模型 (核心主表)"""

    __tablename__ = 'core_transactions'

    date = db.Column(db.Date, nullable=False, index=True)
    description = db.Column(db.String(200), nullable=False)
    type = db.Column(db.String(20), default='EXPENSE') # EXPENSE, INCOME, TRANSFER

    # 商户和分类字段 (基于数据源提取)
    merchant_name = db.Column(db.String(200), index=True, nullable=True)
    source_category = db.Column(db.String(100), index=True, nullable=True)

    # 关联字段 (用于将两笔 Transaction 关联起来，如转账的两端)
    link_id = db.Column(db.String(36), index=True, nullable=True)

    # 原始数据快照 (方便追溯)
    raw_data = db.Column(JSON, nullable=True)
    
    # 关系
    entries = db.relationship('Entry', back_populates='transaction', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<CoreTransaction(date={self.date}, merchant={self.merchant_name}, category={self.source_category})>'


class Entry(BaseModel):
    """资金分录模型 (原子变动)"""

    __tablename__ = 'entries'

    transaction_id = db.Column(db.Integer, db.ForeignKey('core_transactions.id'), nullable=False, index=True)
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=False, index=True)

    amount = db.Column(db.Numeric(15, 2), nullable=False) # 正数=增加, 负数=减少

    # 可选：分录备注 (通常用 Transaction 的 description，但有时分录有单独说明)
    memo = db.Column(db.String(200))

    # 关系
    transaction = db.relationship('CoreTransaction', back_populates='entries')
    account = db.relationship('Account', back_populates='entries')

    def __repr__(self):
        return f'<Entry(tx={self.transaction_id}, acc={self.account_id}, amt={self.amount})>'



