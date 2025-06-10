"""Balance Analysis Module.

包含账户余额分析器，提供余额范围、历史记录和汇总分析功能。
"""

from typing import Dict, List, Any, Optional
from decimal import Decimal
from datetime import datetime, timedelta
import logging
from dateutil.relativedelta import relativedelta
from sqlalchemy import func

from app.models import Bank, Account, Transaction, db
from app.services.analysis.analysis_models import BalanceAnalysis, BalanceMetrics
from app.utils.query_builder import OptimizedQueryBuilder, AnalysisException
from app.utils.cache_manager import optimized_cache
from .base_analyzer import BaseAnalyzer
from app.utils.performance_monitor import performance_monitor

logger = logging.getLogger(__name__)


class BalanceAnalyzer(BaseAnalyzer):
    """账户余额分析器。
    
    提供余额范围分析、月度历史记录和详细余额汇总功能。
    """
    
    @performance_monitor("balance_analysis")
    def analyze(self) -> BalanceAnalysis:
        """分析账户余额状况。"""
        try:
            # 获取余额范围
            balance_range = self.get_balance_range()
            
            # 获取月度历史
            monthly_history = self.get_monthly_history()
            
            # 获取余额汇总
            balance_summary = self.get_balance_summary()
            
            # 构建余额指标
            metrics = self._build_balance_metrics(balance_range, monthly_history, balance_summary)
            
            return BalanceAnalysis(
                metrics=metrics,
                balance_range=balance_range,
                monthly_history=monthly_history,
                balance_summary=balance_summary
            )
        except Exception as e:
            logger.error(f"余额分析失败: {e}")
            return BalanceAnalysis()
    
    @optimized_cache('balance_range', expire_minutes=30, priority=2)
    def get_balance_range(self) -> Dict[str, Any]:
        """获取余额范围（最小值和最大值）。"""
        try:
            accounts = Account.query.filter_by(is_active=True).all()
            if not accounts:
                return {'min_balance': 0, 'max_balance': 0, 'range': 0}
            
            balances = [float(account.get_current_balance()) for account in accounts]
            min_balance = min(balances)
            max_balance = max(balances)
            
            return {
                'min_balance': min_balance,
                'max_balance': max_balance,
                'range': max_balance - min_balance
            }
            
        except Exception as e:
            logger.error(f"获取余额范围失败: {e}")
            return {'min_balance': 0, 'max_balance': 0, 'range': 0}
    
    @optimized_cache('monthly_balance_history', expire_minutes=60, priority=1)
    def get_monthly_history(self, months: int = 12) -> List[Dict[str, Any]]:
        """获取指定月数的月度余额历史记录。"""
        try:
            # 计算开始日期
            end_date = datetime.now().date()
            start_date = end_date - relativedelta(months=months-1)
            start_date = start_date.replace(day=1)  # 月初
            
            # 获取所有活跃账户
            accounts = Account.query.filter_by(is_active=True).all()
            if not accounts:
                return []
            
            history = []
            current_date = start_date
            
            while current_date <= end_date:
                month_end = (current_date + relativedelta(months=1)) - timedelta(days=1)
                if month_end > end_date:
                    month_end = end_date
                
                total_balance = Decimal('0')
                for account in accounts:
                    # 计算该月末的余额
                    # 获取开户余额 + 截至月末的交易总和
                    transactions_sum = db.session.query(func.sum(Transaction.amount)).filter(
                        Transaction.account_id == account.id,
                        Transaction.date <= month_end
                    ).scalar() or Decimal('0')
                    
                    balance = account.opening_balance + transactions_sum
                    total_balance += balance
                
                history.append({
                    'year': current_date.year,
                    'month': current_date.month,
                    'date': current_date.strftime('%Y-%m'),
                    'balance': float(total_balance)
                })
                
                current_date = current_date + relativedelta(months=1)
            
            return history
            
        except Exception as e:
            logger.error(f"获取月度余额历史失败: {e}")
            return []
    
    @optimized_cache('balance_summary', expire_minutes=30, priority=2)
    def get_balance_summary(self) -> Dict[str, Any]:
        """获取所有账户的余额汇总。"""
        try:
            accounts = Account.query.filter_by(is_active=True).all()
            summary = {
                'total_accounts': len(accounts),
                'total_balance': Decimal('0'),
                'accounts': [],
                'by_bank': {},
                'by_currency': {}
            }
            
            for account in accounts:
                current_balance = account.get_current_balance()
                account_info = {
                    'id': account.id,
                    'name': account.account_name,
                    'number': account.account_number,
                    'bank_name': account.bank.name if account.bank else 'Unknown',
                    'currency': account.currency,
                    'balance': float(current_balance),
                    'account_type': account.account_type
                }
                
                summary['accounts'].append(account_info)
                summary['total_balance'] += current_balance
                
                # 按银行分组
                bank_name = account.bank.name if account.bank else 'Unknown'
                if bank_name not in summary['by_bank']:
                    summary['by_bank'][bank_name] = {'count': 0, 'balance': Decimal('0')}
                summary['by_bank'][bank_name]['count'] += 1
                summary['by_bank'][bank_name]['balance'] += current_balance
                
                # 按货币分组
                if account.currency not in summary['by_currency']:
                    summary['by_currency'][account.currency] = {'count': 0, 'balance': Decimal('0')}
                summary['by_currency'][account.currency]['count'] += 1
                summary['by_currency'][account.currency]['balance'] += current_balance
            
            # 转换Decimal为float以便JSON序列化
            summary['total_balance'] = float(summary['total_balance'])
            for bank_data in summary['by_bank'].values():
                bank_data['balance'] = float(bank_data['balance'])
            for currency_data in summary['by_currency'].values():
                currency_data['balance'] = float(currency_data['balance'])
            
            return summary
            
        except Exception as e:
            logger.error(f"获取余额汇总失败: {e}")
            return {
                'total_accounts': 0,
                'total_balance': 0,
                'accounts': [],
                'by_bank': {},
                'by_currency': {}
            }
    
    def _build_balance_metrics(self, balance_range: Dict[str, Any], 
                              monthly_history: List[Dict[str, Any]], 
                              balance_summary: Dict[str, Any]) -> BalanceMetrics:
        """构建余额指标。"""
        try:
            # 计算余额趋势
            trend = self._calculate_balance_trend(monthly_history)
            
            # 计算余额稳定性
            stability = self._calculate_balance_stability(monthly_history)
            
            return BalanceMetrics(
                total_balance=balance_summary.get('total_balance', 0.0),
                min_balance=balance_range.get('min_balance', 0.0),
                max_balance=balance_range.get('max_balance', 0.0),
                balance_range=balance_range.get('range', 0.0),
                account_count=balance_summary.get('total_accounts', 0),
                balance_trend=trend,
                balance_stability=stability
            )
        except Exception as e:
            logger.error(f"构建余额指标失败: {e}")
            return BalanceMetrics()
    
    def _calculate_balance_trend(self, monthly_history: List[Dict[str, Any]]) -> str:
        """计算余额趋势。"""
        try:
            if len(monthly_history) < 2:
                return "稳定"
            
            # 计算最近3个月的趋势
            recent_months = monthly_history[-3:] if len(monthly_history) >= 3 else monthly_history
            
            if len(recent_months) < 2:
                return "稳定"
            
            # 计算平均变化率
            total_change = 0
            for i in range(1, len(recent_months)):
                prev_balance = recent_months[i-1]['balance']
                curr_balance = recent_months[i]['balance']
                
                if prev_balance > 0:
                    change_rate = (curr_balance - prev_balance) / prev_balance
                    total_change += change_rate
            
            avg_change = total_change / (len(recent_months) - 1)
            
            if avg_change > 0.05:  # 5%以上增长
                return "上升"
            elif avg_change < -0.05:  # 5%以上下降
                return "下降"
            else:
                return "稳定"
                
        except Exception as e:
            logger.error(f"计算余额趋势失败: {e}")
            return "稳定"
    
    def _calculate_balance_stability(self, monthly_history: List[Dict[str, Any]]) -> float:
        """计算余额稳定性（变异系数）。"""
        try:
            if len(monthly_history) < 2:
                return 1.0
            
            balances = [month['balance'] for month in monthly_history]
            
            # 计算平均值和标准差
            mean_balance = sum(balances) / len(balances)
            if mean_balance == 0:
                return 1.0
            
            variance = sum((balance - mean_balance) ** 2 for balance in balances) / len(balances)
            std_dev = variance ** 0.5
            
            # 变异系数（标准差/平均值）
            coefficient_of_variation = std_dev / mean_balance
            
            # 稳定性分数（1 - 变异系数，限制在0-1之间）
            stability = max(0, min(1, 1 - coefficient_of_variation))
            
            return stability
            
        except Exception as e:
            logger.error(f"计算余额稳定性失败: {e}")
            return 1.0