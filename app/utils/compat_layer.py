"""Compatibility layer to convert new double-entry model to flat format for frontend"""

from typing import List, Dict, Any
from decimal import Decimal
from app.models import CoreTransaction, Entry, Account

class TransactionCompatLayer:
    """将复式记账数据转换为扁平格式供前端使用"""
    
    @staticmethod
    def get_summary() -> Dict[str, Any]:
        """
        获取交易汇总信息（模拟 Transaction.get_summary）
        """
        # 统计所有 ASSET 类型账户的分录
        from sqlalchemy import func
        from app.models import db
        
        # 获取所有实际账户（ASSET类型）
        asset_accounts = Account.query.filter_by(type='ASSET').all()
        asset_account_ids = [acc.id for acc in asset_accounts]
        
        if not asset_account_ids:
            return {
                'total_count': 0,
                'income_sum': 0.0,
                'expense_sum': 0.0,
                'net_amount': 0.0
            }
        
        # 统计这些账户的分录
        total_count = Entry.query.filter(Entry.account_id.in_(asset_account_ids)).count()
        
        income_sum = db.session.query(func.sum(Entry.amount)).filter(
            Entry.account_id.in_(asset_account_ids),
            Entry.amount > 0
        ).scalar() or 0
        
        expense_sum = db.session.query(func.sum(Entry.amount)).filter(
            Entry.account_id.in_(asset_account_ids),
            Entry.amount < 0
        ).scalar() or 0
        
        return {
            'total_count': total_count,
            'income_sum': float(income_sum),
            'expense_sum': float(expense_sum),
            'net_amount': float(income_sum + expense_sum)
        }
