"""Database Statistics Analysis Module.

包含数据库统计分析器，提供数据库实体统计和健康状况分析功能。
"""

from typing import Dict, Any
import logging

from app.models import Bank, Account, Transaction, db
from app.services.analysis.analysis_models import DatabaseStats, DatabaseMetrics
from app.utils.cache_manager import optimized_cache
from .base_analyzer import BaseAnalyzer
from app.utils.performance_monitor import performance_monitor

logger = logging.getLogger(__name__)


class DatabaseStatsAnalyzer(BaseAnalyzer):
    """数据库统计分析器。
    
    提供数据库实体统计、数据健康状况和完整性分析功能。
    """
    
    @performance_monitor("database_stats_analysis")
    def analyze(self) -> DatabaseStats:
        """分析数据库统计信息。"""
        try:
            # 获取基础统计信息
            basic_stats = self.get_database_stats()
            
            # 构建数据库指标
            metrics = self._build_database_metrics(basic_stats)
            
            return DatabaseStats(
                metrics=metrics,
                basic_stats=basic_stats,
                health_score=self._calculate_health_score(basic_stats)
            )
        except Exception as e:
            logger.error(f"数据库统计分析失败: {e}")
            return DatabaseStats()
    
    @optimized_cache('database_stats', expire_minutes=15, priority=3)
    def get_database_stats(self) -> Dict[str, Any]:
        """获取数据库统计信息。"""
        try:
            stats = {
                'banks_count': Bank.query.count(),
                'active_banks_count': Bank.query.filter_by(is_active=True).count(),
                'accounts_count': Account.query.count(),
                'active_accounts_count': Account.query.filter_by(is_active=True).count(),
                'transactions_count': Transaction.query.count(),
                'income_transactions_count': Transaction.query.filter(Transaction.amount > 0).count(),
                'expense_transactions_count': Transaction.query.filter(Transaction.amount < 0).count(),
            }
            
            # 添加派生统计
            stats['inactive_banks_count'] = stats['banks_count'] - stats['active_banks_count']
            stats['inactive_accounts_count'] = stats['accounts_count'] - stats['active_accounts_count']
            
            # 计算比例
            if stats['banks_count'] > 0:
                stats['active_banks_ratio'] = stats['active_banks_count'] / stats['banks_count']
            else:
                stats['active_banks_ratio'] = 0.0
                
            if stats['accounts_count'] > 0:
                stats['active_accounts_ratio'] = stats['active_accounts_count'] / stats['accounts_count']
            else:
                stats['active_accounts_ratio'] = 0.0
                
            if stats['transactions_count'] > 0:
                stats['income_ratio'] = stats['income_transactions_count'] / stats['transactions_count']
                stats['expense_ratio'] = stats['expense_transactions_count'] / stats['transactions_count']
            else:
                stats['income_ratio'] = 0.0
                stats['expense_ratio'] = 0.0
            
            return stats
        except Exception as e:
            logger.error(f"获取数据库统计失败: {e}")
            return {}
    
    def _build_database_metrics(self, basic_stats: Dict[str, Any]) -> DatabaseMetrics:
        """构建数据库指标。"""
        try:
            return DatabaseMetrics(
                total_banks=basic_stats.get('banks_count', 0),
                active_banks=basic_stats.get('active_banks_count', 0),
                total_accounts=basic_stats.get('accounts_count', 0),
                active_accounts=basic_stats.get('active_accounts_count', 0),
                total_transactions=basic_stats.get('transactions_count', 0),
                income_transactions=basic_stats.get('income_transactions_count', 0),
                expense_transactions=basic_stats.get('expense_transactions_count', 0),
                active_banks_ratio=basic_stats.get('active_banks_ratio', 0.0),
                active_accounts_ratio=basic_stats.get('active_accounts_ratio', 0.0),
                income_ratio=basic_stats.get('income_ratio', 0.0),
                expense_ratio=basic_stats.get('expense_ratio', 0.0)
            )
        except Exception as e:
            logger.error(f"构建数据库指标失败: {e}")
            return DatabaseMetrics()
    
    def _calculate_health_score(self, basic_stats: Dict[str, Any]) -> float:
        """计算数据库健康分数。"""
        try:
            score = 0.0
            max_score = 100.0
            
            # 数据完整性检查（30分）
            if basic_stats.get('banks_count', 0) > 0:
                score += 10
            if basic_stats.get('accounts_count', 0) > 0:
                score += 10
            if basic_stats.get('transactions_count', 0) > 0:
                score += 10
            
            # 活跃度检查（40分）
            active_banks_ratio = basic_stats.get('active_banks_ratio', 0.0)
            active_accounts_ratio = basic_stats.get('active_accounts_ratio', 0.0)
            
            score += active_banks_ratio * 20  # 最多20分
            score += active_accounts_ratio * 20  # 最多20分
            
            # 数据平衡性检查（30分）
            income_ratio = basic_stats.get('income_ratio', 0.0)
            expense_ratio = basic_stats.get('expense_ratio', 0.0)
            
            # 理想的收支比例应该相对平衡
            if income_ratio > 0 and expense_ratio > 0:
                balance_score = 30 - abs(income_ratio - expense_ratio) * 30
                score += max(0, balance_score)
            elif income_ratio > 0 or expense_ratio > 0:
                score += 15  # 至少有一种类型的交易
            
            return min(max_score, score)
            
        except Exception as e:
            logger.error(f"计算健康分数失败: {e}")
            return 0.0
    
    @optimized_cache('data_integrity_check', expire_minutes=30, priority=2)
    def check_data_integrity(self) -> Dict[str, Any]:
        """检查数据完整性。"""
        try:
            integrity_issues = []
            
            # 检查孤立账户（没有关联银行的账户）
            orphaned_accounts = Account.query.filter(Account.bank_id.is_(None)).count()
            if orphaned_accounts > 0:
                integrity_issues.append(f"发现 {orphaned_accounts} 个孤立账户（无关联银行）")
            
            # 检查孤立交易（没有关联账户的交易）
            orphaned_transactions = Transaction.query.filter(Transaction.account_id.is_(None)).count()
            if orphaned_transactions > 0:
                integrity_issues.append(f"发现 {orphaned_transactions} 个孤立交易（无关联账户）")
            
            # 检查无效的账户关联
            invalid_account_refs = db.session.query(Transaction).join(
                Account, Transaction.account_id == Account.id, isouter=True
            ).filter(Account.id.is_(None)).count()
            
            if invalid_account_refs > 0:
                integrity_issues.append(f"发现 {invalid_account_refs} 个无效的账户关联")
            
            return {
                'has_issues': len(integrity_issues) > 0,
                'issues_count': len(integrity_issues),
                'issues': integrity_issues,
                'integrity_score': max(0, 100 - len(integrity_issues) * 10)
            }
            
        except Exception as e:
            logger.error(f"数据完整性检查失败: {e}")
            return {
                'has_issues': True,
                'issues_count': 1,
                'issues': [f"完整性检查失败: {str(e)}"],
                'integrity_score': 0
            }