"""Transaction service for handling transaction-related business logic.

This module provides transaction processing, validation, and analysis functionality.
"""

from typing import List, Dict, Any, Optional, Tuple
from decimal import Decimal
from datetime import date, datetime, timedelta
import logging
from collections import defaultdict

from app.models import Transaction, Account, TransactionType, db
from app.services.database_service import DatabaseService
from sqlalchemy import func, and_, or_, case
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

class TransactionService:
    """Service for handling transaction operations and business logic."""
    
    @staticmethod
    def process_transaction(account_id: int, transaction_type_id: int, date: date,
                          amount: Decimal, currency: str = 'CNY', description: str = None,
                          counterparty: str = None, notes: str = None,
                          original_description: str = None, auto_categorize: bool = True,
                          **kwargs) -> Tuple[Transaction, bool]:
        """Process a new transaction with validation and auto-categorization.
        
        Returns:
            Tuple of (transaction, is_new_transaction)
        """
        try:
            # Validate account
            account = DatabaseService.get_account_by_id(account_id)
            if not account:
                raise ValueError(f"Account with ID {account_id} not found")
            
            # Validate transaction type
            transaction_type = DatabaseService.get_transaction_type_by_id(transaction_type_id)
            if not transaction_type:
                raise ValueError(f"Transaction type with ID {transaction_type_id} not found")
            
            # Auto-categorize if enabled and no type specified
            if auto_categorize and not transaction_type_id:
                suggested_type = TransactionService._auto_categorize_transaction(
                    description or original_description, counterparty, amount
                )
                if suggested_type:
                    transaction_type_id = suggested_type.id
            
            # Adjust amount based on transaction type
            adjusted_amount = TransactionService._adjust_amount_by_type(amount, transaction_type)
            
            # Create transaction
            transaction = DatabaseService.create_transaction(
                account_id=account_id,
                transaction_type_id=transaction_type_id,
                date=date,
                amount=adjusted_amount,
                currency=currency,
                description=description,
                counterparty=counterparty,
                notes=notes,
                original_description=original_description,
                **kwargs
            )
            
            # Update account balance if needed
            TransactionService._update_account_balance(account, adjusted_amount)
            
            logger.info(f"Transaction processed successfully: {transaction.id}")
            return transaction, True
            
        except Exception as e:
            logger.error(f"Error processing transaction: {e}")
            db.session.rollback()
            raise
    
    @staticmethod
    def _auto_categorize_transaction(description: str, counterparty: str, amount: Decimal) -> Optional[TransactionType]:
        """Auto-categorize transaction based on description and counterparty."""
        if not description and not counterparty:
            return None
        
        search_text = f"{description or ''} {counterparty or ''}".lower()
        
        # Define categorization rules
        categorization_rules = {
            # Income categories
            '工资': ['salary', 'wage', '工资', '薪水', '薪资'],
            '奖金': ['bonus', '奖金', '年终奖', '绩效'],
            '投资收益': ['dividend', 'interest', '股息', '利息', '投资', '理财'],
            
            # Expense categories
            '餐饮': ['restaurant', 'food', '餐厅', '外卖', '美团', '饿了么', 'mcdonald', 'kfc'],
            '交通': ['transport', 'taxi', 'uber', '滴滴', '地铁', '公交', '加油', 'gas'],
            '购物': ['shopping', 'mall', '淘宝', '京东', '超市', 'walmart', '沃尔玛'],
            '娱乐': ['entertainment', 'movie', 'game', '电影', '游戏', '娱乐'],
            '医疗': ['hospital', 'pharmacy', 'medical', '医院', '药店', '医疗'],
            '教育': ['education', 'school', 'course', '学校', '培训', '教育'],
            '房租': ['rent', 'housing', '房租', '租金', '物业'],
            '水电费': ['utility', 'electric', 'water', '水费', '电费', '燃气'],
        }
        
        # Find matching category
        for category_name, keywords in categorization_rules.items():
            for keyword in keywords:
                if keyword in search_text:
                    transaction_type = DatabaseService.get_transaction_type_by_name(category_name)
                    if transaction_type:
                        return transaction_type
        
        # Default categorization based on amount
        if amount > 0:
            return DatabaseService.get_transaction_type_by_name('其他收入')
        else:
            return DatabaseService.get_transaction_type_by_name('其他支出')
    
    @staticmethod
    def _adjust_amount_by_type(amount: Decimal, transaction_type: TransactionType) -> Decimal:
        """Adjust amount sign based on transaction type."""
        if transaction_type.is_income and amount < 0:
            return abs(amount)
        elif not transaction_type.is_income and amount > 0:
            return -abs(amount)
        return amount
    
    @staticmethod
    def _update_account_balance(account: Account, amount: Decimal):
        """Update account balance after transaction."""
        try:
            account.balance = (account.balance or 0) + amount
            db.session.commit()
        except Exception as e:
            logger.error(f"Error updating account balance: {e}")
            db.session.rollback()
            raise
    
    @staticmethod
    def bulk_import_transactions(transactions_data: List[Dict[str, Any]], 
                               account_id: int = None, auto_categorize: bool = True) -> Dict[str, Any]:
        """Import multiple transactions in bulk.
        
        Returns:
            Dictionary with import statistics
        """
        results = {
            'total': len(transactions_data),
            'successful': 0,
            'failed': 0,
            'errors': [],
            'duplicates': 0
        }
        
        for i, transaction_data in enumerate(transactions_data):
            try:
                # Use provided account_id if not in data
                if account_id and 'account_id' not in transaction_data:
                    transaction_data['account_id'] = account_id
                
                # Check for duplicates
                if TransactionService._is_duplicate_transaction(transaction_data):
                    results['duplicates'] += 1
                    continue
                
                # Process transaction
                TransactionService.process_transaction(
                    auto_categorize=auto_categorize,
                    **transaction_data
                )
                results['successful'] += 1
                
            except Exception as e:
                error_msg = f"Row {i+1}: {str(e)}"
                results['errors'].append(error_msg)
                results['failed'] += 1
                logger.error(f"Failed to import transaction at row {i+1}: {e}")
        
        logger.info(f"Bulk import completed: {results['successful']} successful, "
                   f"{results['failed']} failed, {results['duplicates']} duplicates")
        return results
    
    @staticmethod
    def _is_duplicate_transaction(transaction_data: Dict[str, Any]) -> bool:
        """Check if transaction is a duplicate."""
        try:
            existing = Transaction.query.filter(
                and_(
                    Transaction.account_id == transaction_data.get('account_id'),
                    Transaction.date == transaction_data.get('date'),
                    Transaction.amount == transaction_data.get('amount'),
                    or_(
                        Transaction.description == transaction_data.get('description'),
                        Transaction.original_description == transaction_data.get('original_description')
                    )
                )
            ).first()
            return existing is not None
        except Exception:
            return False
    
    @staticmethod
    def get_transaction_summary(account_id: int = None, start_date: date = None, 
                              end_date: date = None) -> Dict[str, Any]:
        """Get transaction summary for specified period."""
        try:
            query = Transaction.query
            
            if account_id:
                query = query.filter_by(account_id=account_id)
            if start_date:
                query = query.filter(Transaction.date >= start_date)
            if end_date:
                query = query.filter(Transaction.date <= end_date)
            
            transactions = query.all()
            
            summary = {
                'total_transactions': len(transactions),
                'total_income': Decimal('0'),
                'total_expense': Decimal('0'),
                'net_amount': Decimal('0'),
                'income_transactions': 0,
                'expense_transactions': 0,
                'categories': defaultdict(lambda: {'count': 0, 'amount': Decimal('0')}),
                'monthly_breakdown': defaultdict(lambda: {
                    'income': Decimal('0'), 
                    'expense': Decimal('0'), 
                    'net': Decimal('0')
                })
            }
            
            for transaction in transactions:
                amount = transaction.amount
                month_key = transaction.date.strftime('%Y-%m')
                category_name = transaction.transaction_type.name if transaction.transaction_type else 'Unknown'
                
                if amount > 0:
                    summary['total_income'] += amount
                    summary['income_transactions'] += 1
                    summary['monthly_breakdown'][month_key]['income'] += amount
                else:
                    summary['total_expense'] += abs(amount)
                    summary['expense_transactions'] += 1
                    summary['monthly_breakdown'][month_key]['expense'] += abs(amount)
                
                summary['categories'][category_name]['count'] += 1
                summary['categories'][category_name]['amount'] += amount
                summary['monthly_breakdown'][month_key]['net'] += amount
            
            summary['net_amount'] = summary['total_income'] - summary['total_expense']
            
            # Convert defaultdicts to regular dicts for JSON serialization
            summary['categories'] = dict(summary['categories'])
            summary['monthly_breakdown'] = dict(summary['monthly_breakdown'])
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting transaction summary: {e}")
            raise
    
    @staticmethod
    def get_spending_by_category(account_id: int = None, start_date: date = None,
                               end_date: date = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Get spending breakdown by category."""
        try:
            query = db.session.query(
                TransactionType.name,
                TransactionType.color,
                TransactionType.icon,
                func.count(Transaction.id).label('transaction_count'),
                func.sum(func.abs(Transaction.amount)).label('total_amount')
            ).join(Transaction)
            
            if account_id:
                query = query.filter(Transaction.account_id == account_id)
            if start_date:
                query = query.filter(Transaction.date >= start_date)
            if end_date:
                query = query.filter(Transaction.date <= end_date)
            
            # Only expense transactions
            query = query.filter(Transaction.amount < 0)
            
            results = query.group_by(
                TransactionType.id, TransactionType.name, 
                TransactionType.color, TransactionType.icon
            ).order_by(func.sum(func.abs(Transaction.amount)).desc()).limit(limit).all()
            
            return [
                {
                    'category': result.name,
                    'color': result.color,
                    'icon': result.icon,
                    'transaction_count': result.transaction_count,
                    'total_amount': float(result.total_amount or 0),
                }
                for result in results
            ]
            
        except Exception as e:
            logger.error(f"Error getting spending by category: {e}")
            raise
    
    @staticmethod
    def get_income_by_category(account_id: int = None, start_date: date = None,
                             end_date: date = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Get income breakdown by category."""
        try:
            query = db.session.query(
                TransactionType.name,
                TransactionType.color,
                TransactionType.icon,
                func.count(Transaction.id).label('transaction_count'),
                func.sum(Transaction.amount).label('total_amount')
            ).join(Transaction)
            
            if account_id:
                query = query.filter(Transaction.account_id == account_id)
            if start_date:
                query = query.filter(Transaction.date >= start_date)
            if end_date:
                query = query.filter(Transaction.date <= end_date)
            
            # Only income transactions
            query = query.filter(Transaction.amount > 0)
            
            results = query.group_by(
                TransactionType.id, TransactionType.name,
                TransactionType.color, TransactionType.icon
            ).order_by(func.sum(Transaction.amount).desc()).limit(limit).all()
            
            return [
                {
                    'category': result.name,
                    'color': result.color,
                    'icon': result.icon,
                    'transaction_count': result.transaction_count,
                    'total_amount': float(result.total_amount or 0),
                }
                for result in results
            ]
            
        except Exception as e:
            logger.error(f"Error getting income by category: {e}")
            raise
    
    @staticmethod
    def get_monthly_trends(account_id: int = None, months: int = 12) -> List[Dict[str, Any]]:
        """Get monthly income/expense trends."""
        try:
            end_date = date.today()
            start_date = end_date.replace(day=1) - timedelta(days=months*30)
            
            query = db.session.query(
                func.strftime('%Y-%m', Transaction.date).label('month'),
                func.sum(case((Transaction.amount > 0, Transaction.amount), else_=0)).label('income'),
            func.sum(case((Transaction.amount < 0, func.abs(Transaction.amount)), else_=0)).label('expense')
            )
            
            if account_id:
                query = query.filter(Transaction.account_id == account_id)
            
            query = query.filter(Transaction.date >= start_date)
            
            results = query.group_by(
                func.strftime('%Y-%m', Transaction.date)
            ).order_by(
                func.strftime('%Y-%m', Transaction.date)
            ).all()
            
            trends = []
            for result in results:
                income = float(result.income or 0)
                expense = float(result.expense or 0)
                trends.append({
                    'month': result.month,
                    'income': income,
                    'expense': expense,
                    'net': income - expense
                })
            
            return trends
            
        except Exception as e:
            logger.error(f"Error getting monthly trends: {e}")
            raise
    
    @staticmethod
    def reconcile_transactions(account_id: int, expected_balance: Decimal) -> Dict[str, Any]:
        """Reconcile account transactions with expected balance."""
        try:
            account = DatabaseService.get_account_by_id(account_id)
            if not account:
                raise ValueError(f"Account with ID {account_id} not found")
            
            # Calculate actual balance from transactions
            transactions = Transaction.query.filter_by(account_id=account_id).all()
            calculated_balance = sum(t.amount for t in transactions)
            
            # Compare with account balance and expected balance
            account_balance = account.balance or Decimal('0')
            
            reconciliation = {
                'account_id': account_id,
                'account_balance': float(account_balance),
                'calculated_balance': float(calculated_balance),
                'expected_balance': float(expected_balance),
                'account_difference': float(account_balance - calculated_balance),
                'expected_difference': float(expected_balance - calculated_balance),
                'is_reconciled': abs(expected_balance - calculated_balance) < Decimal('0.01'),
                'total_transactions': len(transactions)
            }
            
            # Update account balance if needed
            if abs(account_balance - calculated_balance) > Decimal('0.01'):
                account.balance = calculated_balance
                db.session.commit()
                reconciliation['balance_updated'] = True
            else:
                reconciliation['balance_updated'] = False
            
            return reconciliation
            
        except Exception as e:
            logger.error(f"Error reconciling transactions: {e}")
            raise
    
    @staticmethod
    def detect_anomalies(account_id: int = None, threshold_multiplier: float = 3.0) -> List[Dict[str, Any]]:
        """Detect anomalous transactions based on statistical analysis."""
        try:
            query = Transaction.query
            if account_id:
                query = query.filter_by(account_id=account_id)
            
            transactions = query.all()
            
            if len(transactions) < 10:
                return []  # Not enough data for anomaly detection
            
            # Calculate statistics
            amounts = [abs(float(t.amount)) for t in transactions]
            mean_amount = sum(amounts) / len(amounts)
            variance = sum((x - mean_amount) ** 2 for x in amounts) / len(amounts)
            std_dev = variance ** 0.5
            
            threshold = mean_amount + (threshold_multiplier * std_dev)
            
            # Find anomalous transactions
            anomalies = []
            for transaction in transactions:
                amount = abs(float(transaction.amount))
                if amount > threshold:
                    anomalies.append({
                        'transaction_id': transaction.id,
                        'date': transaction.date.isoformat(),
                        'amount': float(transaction.amount),
                        'description': transaction.description,
                        'counterparty': transaction.counterparty,
                        'deviation_score': (amount - mean_amount) / std_dev if std_dev > 0 else 0,
                        'category': transaction.transaction_type.name if transaction.transaction_type else 'Unknown'
                    })
            
            # Sort by deviation score
            anomalies.sort(key=lambda x: x['deviation_score'], reverse=True)
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Error detecting anomalies: {e}")
            raise