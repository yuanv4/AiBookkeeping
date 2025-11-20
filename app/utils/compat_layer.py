"""Compatibility layer to convert new double-entry model to flat format for frontend"""

from typing import List, Dict, Any
from decimal import Decimal
from app.models import CoreTransaction, Entry, Account

class TransactionCompatLayer:
    """将复式记账数据转换为扁平格式供前端使用"""
    
    @staticmethod
    def transaction_to_flat_dict(transaction: CoreTransaction) -> Dict[str, Any]:
        """
        将 CoreTransaction + Entries 转换为扁平的字典格式
        
        模拟旧 Transaction 模型的字段结构
        """
        # 获取该交易的所有分录
        entries = Entry.query.filter_by(transaction_id=transaction.id).all()
        
        if not entries:
            return None
        
        # 找到实际账户的分录（非系统虚拟账户）
        actual_account_entry = None
        amount = Decimal('0')
        
        for entry in entries:
            account = Account.query.get(entry.account_id)
            if account and account.type == 'ASSET':
                # 这是实际的银行账户/支付账户
                actual_account_entry = entry
                amount = entry.amount
                break
        
        if not actual_account_entry:
            # 如果没找到实际账户，使用第一个分录
            actual_account_entry = entries[0]
            amount = actual_account_entry.amount
        
        account = Account.query.get(actual_account_entry.account_id)
        
        # 找到对手方（另一个分录的账户）
        counterparty = "未知"
        category = "uncategorized"
        
        for entry in entries:
            if entry.id != actual_account_entry.id:
                other_account = Account.query.get(entry.account_id)
                if other_account:
                    counterparty = other_account.name
                    # 根据账户类型推断分类
                    if other_account.type == 'EXPENSE':
                        category = 'lifestyle'  # 可以根据描述进一步细化
                    elif other_account.type == 'INCOME':
                        category = 'employer'
                break
        
        # 构建扁平字典
        return {
            'id': transaction.id,
            'date': transaction.date.isoformat() if transaction.date else None,
            'description': transaction.description,
            'amount': float(amount),
            'absolute_amount': float(abs(amount)),
            'balance_after': None,  # 复式记账中不需要这个字段
            'counterparty': counterparty,
            'currency': account.currency if account else 'CNY',
            'category': category,
            'bank_name': account.bank_name if account else 'Unknown',
            'bank_code': account.bank_name if account else 'UNKNOWN',
            'account_number': account.account_number if account else 'unknown',
            'account_name': account.name if account else '未知账户',
            'account_type': account.type if account else 'ASSET',
            'created_at': transaction.created_at.isoformat() if transaction.created_at else None,
            'updated_at': transaction.updated_at.isoformat() if transaction.updated_at else None,
            'raw_data': transaction.raw_data
        }
    
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
    
    @staticmethod
    def get_filtered_transactions(filters: dict = None, page: int = None, per_page: int = None) -> List[Dict]:
        """
        根据过滤条件获取交易记录（扁平格式）
        """
        query = CoreTransaction.query
        
        # TODO: 实现过滤逻辑（根据需要）
        # 目前先返回所有交易
        
        # 按日期降序排列
        query = query.order_by(CoreTransaction.date.desc(), CoreTransaction.id.desc())
        
        if page and per_page:
            pagination = query.paginate(page=page, per_page=per_page, error_out=False)
            transactions = pagination.items
        else:
            transactions = query.all()
        
        # 转换为扁平格式
        return [TransactionCompatLayer.transaction_to_flat_dict(tx) for tx in transactions if tx]

