#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
统一商户分类服务模块

整合配置管理、商户分类和业务分析功能到单一服务中。
提供基于配置文件的精确匹配分类和完整的支出分析功能。
"""

import os
import logging
import time
import yaml
import jsonschema
from pathlib import Path
from typing import Dict, List, Any, Optional
from functools import lru_cache
from threading import Lock

from datetime import date, datetime
from decimal import Decimal
from sqlalchemy.orm import Session

from app.models import Transaction, db
from app.utils.query_cache import cached_query
from .models import DateUtils

logger = logging.getLogger(__name__)


class CategoryService:
    """统一商户分类服务
    
    整合配置管理、商户分类和业务分析功能。
    提供完整的商户分类和支出分析解决方案。
    """
    
    # 配置验证Schema
    CONFIG_SCHEMA = {
        "type": "object",
        "required": ["categories", "merchants"],
        "properties": {
            "categories": {
                "type": "object",
                "patternProperties": {
                    "^[a-z_]+$": {
                        "type": "object",
                        "required": ["name", "icon", "color", "description"],
                        "properties": {
                            "name": {"type": "string", "minLength": 1},
                            "icon": {"type": "string", "minLength": 1},
                            "color": {"type": "string", "minLength": 1},
                            "description": {"type": "string", "minLength": 1}
                        },
                        "additionalProperties": False
                    }
                }
            },
            "merchants": {
                "type": "object",
                "patternProperties": {
                    "^[a-z_]+$": {
                        "type": "array",
                        "items": {"type": "string", "minLength": 1},
                        "uniqueItems": True
                    }
                }
            }
        }
    }
    
    def __init__(self, config_path: Optional[str] = None, db_session: Optional[Session] = None):
        """初始化分类服务
        
        Args:
            config_path: 配置文件路径，如果为None则使用默认路径
            db_session: 数据库会话，如果为None则使用默认会话
        """
        self.logger = logging.getLogger(__name__)
        self.db = db_session or db.session
        
        # 配置管理
        self.config_path = Path(config_path) if config_path else self._get_default_config_path()
        self._config_data: Optional[Dict[str, Any]] = None
        self._merchant_lookup: Optional[Dict[str, str]] = None
        self._last_modified: Optional[float] = None
        self._config_lock = Lock()
        
        # 性能统计
        self._classification_count = 0
        self._cache_hits = 0
        self._total_time = 0.0
        
        # 加载配置
        self._load_config()
    
    def _get_default_config_path(self) -> Path:
        """获取默认配置文件路径"""
        current_dir = Path(__file__).parent
        while current_dir.parent != current_dir:
            config_path = current_dir / "config" / "merchant_categories.yaml"
            if config_path.exists():
                return config_path
            current_dir = current_dir.parent
        
        project_root = Path(__file__).parent.parent.parent
        return project_root / "config" / "merchant_categories.yaml"
    
    def _load_config(self) -> None:
        """加载配置文件"""
        start_time = time.time()
        
        try:
            if not self.config_path.exists():
                raise FileNotFoundError(f"配置文件不存在: {self.config_path}")
            
            current_modified = self.config_path.stat().st_mtime
            if self._last_modified and current_modified <= self._last_modified:
                return
            
            with self._config_lock:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f)
                
                # 验证配置
                jsonschema.validate(config_data, self.CONFIG_SCHEMA)
                
                # 验证分类一致性
                categories = set(config_data.get('categories', {}).keys())
                merchants_categories = set(config_data.get('merchants', {}).keys())
                invalid_categories = merchants_categories - categories
                if invalid_categories:
                    raise ValueError(f"merchants中存在未定义的分类: {invalid_categories}")
                
                if 'other' not in categories:
                    raise ValueError("配置中必须包含'other'分类")
                
                # 构建商户查找表
                merchant_lookup = {}
                for category, merchant_list in config_data.get('merchants', {}).items():
                    for merchant in merchant_list:
                        if merchant in merchant_lookup:
                            self.logger.warning(f"商户'{merchant}'重复定义")
                        merchant_lookup[merchant] = category
                
                self._config_data = config_data
                self._merchant_lookup = merchant_lookup
                self._last_modified = current_modified
                
                load_time = time.time() - start_time
                self.logger.info(
                    f"配置加载成功: {len(categories)}个分类, {len(merchant_lookup)}个商户, "
                    f"耗时{load_time:.3f}秒"
                )
                
        except Exception as e:
            self.logger.error(f"配置加载失败: {e}")
            if self._config_data is None:
                self._load_default_config()
            raise
    
    def _load_default_config(self) -> None:
        """加载默认配置"""
        self.logger.warning("使用默认配置")
        
        default_config = {
            'categories': {
                'other': {
                    'name': '其他支出',
                    'icon': 'more-horizontal',
                    'color': 'dark',
                    'description': '未分类的其他支出'
                }
            },
            'merchants': {'other': []}
        }
        
        with self._config_lock:
            self._config_data = default_config
            self._merchant_lookup = {}
            self._last_modified = time.time()
    
    @lru_cache(maxsize=1000)
    def classify_merchant(self, merchant_name: str) -> str:
        """对商户进行分类
        
        Args:
            merchant_name: 商户名称
            
        Returns:
            商户分类标识，如果未找到匹配则返回'other'
        """
        start_time = time.time()
        
        try:
            if not merchant_name or not isinstance(merchant_name, str):
                return 'other'
            
            normalized_name = merchant_name.strip()
            if not normalized_name:
                return 'other'
            
            # 检查是否需要重新加载配置
            if self._should_reload():
                try:
                    self._load_config()
                    # 清除缓存以使用新配置
                    self.classify_merchant.cache_clear()
                except Exception as e:
                    self.logger.error(f"自动重新加载配置失败: {e}")
            
            category = self._merchant_lookup.get(normalized_name, 'other') if self._merchant_lookup else 'other'
            
            # 更新性能统计
            self._update_stats(start_time, category != 'other')
            
            self.logger.debug(f"商户分类: '{normalized_name}' -> '{category}'")
            return category
            
        except Exception as e:
            self.logger.error(f"商户分类失败: {merchant_name}, 错误: {e}")
            self._update_stats(start_time, False)
            return 'other'
    
    def get_category_display_info(self, category: str) -> Dict[str, str]:
        """获取分类的显示信息
        
        Args:
            category: 分类标识
            
        Returns:
            包含名称、颜色、描述、图标的字典
        """
        if not self._config_data:
            return self._get_default_category_info()
        
        categories = self._config_data.get('categories', {})
        return categories.get(category, categories.get('other', self._get_default_category_info()))
    
    def _get_default_category_info(self) -> Dict[str, str]:
        """获取默认分类信息"""
        return {
            'name': '其他支出',
            'icon': 'more-horizontal',
            'color': 'dark',
            'description': '未分类的其他支出'
        }
    
    def get_all_categories(self) -> Dict[str, Dict[str, str]]:
        """获取所有分类信息"""
        if not self._config_data:
            return {'other': self._get_default_category_info()}
        return self._config_data.get('categories', {})
    
    def get_merchants_by_category(self, category: str) -> List[str]:
        """获取指定分类下的所有商户"""
        if not self._config_data:
            return []
        merchants_data = self._config_data.get('merchants', {})
        return merchants_data.get(category, [])
    
    def batch_classify(self, merchant_names: List[str]) -> Dict[str, str]:
        """批量分类商户"""
        start_time = time.time()
        results = {}
        
        try:
            for merchant_name in merchant_names:
                results[merchant_name] = self.classify_merchant(merchant_name)
            
            batch_time = time.time() - start_time
            self.logger.info(f"批量分类完成: {len(merchant_names)}个商户, 耗时{batch_time:.3f}秒")
            
        except Exception as e:
            self.logger.error(f"批量分类失败: {e}")
        
        return results
    
    def reload_config(self) -> bool:
        """重新加载配置"""
        try:
            old_modified = self._last_modified
            self._load_config()
            if self._last_modified != old_modified:
                self.classify_merchant.cache_clear()
                self.logger.info("配置重新加载成功，缓存已清除")
                return True
            return False
        except Exception as e:
            self.logger.error(f"重新加载配置失败: {e}")
            return False
    
    def clear_cache(self) -> None:
        """清除分类缓存"""
        self.classify_merchant.cache_clear()
        self.logger.info("分类缓存已清除")
    
    def get_cache_info(self) -> Dict[str, Any]:
        """获取缓存信息"""
        cache_info = self.classify_merchant.cache_info()
        return {
            'cache_size': cache_info.currsize,
            'max_size': cache_info.maxsize,
            'hits': cache_info.hits,
            'misses': cache_info.misses,
            'hit_rate': cache_info.hits / (cache_info.hits + cache_info.misses) if (cache_info.hits + cache_info.misses) > 0 else 0.0
        }
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计信息"""
        avg_time = self._total_time / self._classification_count if self._classification_count > 0 else 0.0
        
        return {
            'total_classifications': self._classification_count,
            'cache_hits': self._cache_hits,
            'total_time': self._total_time,
            'average_time': avg_time,
            'cache_hit_rate': self._cache_hits / self._classification_count if self._classification_count > 0 else 0.0,
            'cache_info': self.get_cache_info()
        }
    
    def get_config_stats(self) -> Dict[str, Any]:
        """获取配置统计信息"""
        if not self._config_data or not self._merchant_lookup:
            return {
                'categories_count': 0,
                'merchants_count': 0,
                'config_path': str(self.config_path),
                'last_modified': None,
                'is_loaded': False
            }
        
        return {
            'categories_count': len(self._config_data.get('categories', {})),
            'merchants_count': len(self._merchant_lookup),
            'config_path': str(self.config_path),
            'last_modified': datetime.fromtimestamp(self._last_modified).isoformat() if self._last_modified else None,
            'is_loaded': True
        }
    
    def _should_reload(self) -> bool:
        """检查是否应该重新加载配置"""
        if not self.config_path.exists():
            return False
        
        try:
            current_modified = self.config_path.stat().st_mtime
            return current_modified > (self._last_modified or 0)
        except OSError:
            return False
    
    def _update_stats(self, start_time: float, is_match: bool) -> None:
        """更新性能统计"""
        elapsed_time = time.time() - start_time
        self._classification_count += 1
        self._total_time += elapsed_time

        if is_match:
            self._cache_hits += 1

    # ==================== 业务分析功能 ====================

    def get_expense_analysis_by_category(self, start_date: Optional[date] = None,
                                       end_date: Optional[date] = None,
                                       category_filter: Optional[str] = None,
                                       search_term: Optional[str] = None) -> Dict[str, Any]:
        """按商户类别分析支出数据"""
        try:
            transactions = self._get_filtered_transactions(start_date, end_date, search_term)
            category_data, total_expense = self._process_transactions(transactions, category_filter)
            self._calculate_statistics(category_data, total_expense)
            return self._build_analysis_result(category_data, total_expense, start_date, end_date)
        except Exception as e:
            self.logger.error(f"支出分析失败: {e}")
            return self._get_empty_result(start_date, end_date)

    def _get_filtered_transactions(self, start_date: Optional[date], end_date: Optional[date], search_term: Optional[str]):
        """获取过滤后的交易数据"""
        if start_date is None and end_date is None:
            self.logger.info("获取所有历史交易数据")
        else:
            if not end_date:
                end_date = date.today()
            if not start_date:
                start_date, _ = DateUtils.get_date_range(6, end_date)
            self.logger.info(f"获取交易数据，时间范围：{start_date} 到 {end_date}")

        query = self.db.query(Transaction).filter(
            Transaction.amount < 0,
            Transaction.counterparty.isnot(None),
            Transaction.counterparty != ''
        )

        if start_date and end_date:
            query = query.filter(
                Transaction.date >= start_date,
                Transaction.date <= end_date
            )

        transactions = query.all()
        self.logger.info(f"找到 {len(transactions)} 条支出交易记录")

        if search_term:
            search_term_lower = search_term.lower()
            transactions = [t for t in transactions if search_term_lower in t.counterparty.lower()]

        return transactions

    def _process_transactions(self, transactions, category_filter):
        """处理交易数据并按类别分组"""
        category_data = {}
        total_expense = 0.0

        for transaction in transactions:
            merchant = transaction.counterparty
            amount = float(abs(transaction.amount))
            category = self.classify_merchant(merchant)

            if category_filter and category != category_filter:
                continue

            total_expense += amount

            if category not in category_data:
                category_data[category] = {
                    'total_amount': 0.0,
                    'transaction_count': 0,
                    'merchants': {},
                    'monthly_data': {}
                }

            category_data[category]['total_amount'] += amount
            category_data[category]['transaction_count'] += 1

            if merchant not in category_data[category]['merchants']:
                category_data[category]['merchants'][merchant] = {
                    'total_amount': 0.0,
                    'transaction_count': 0,
                    'avg_amount': 0.0,
                    'last_date': None
                }

            merchant_data = category_data[category]['merchants'][merchant]
            merchant_data['total_amount'] += amount
            merchant_data['transaction_count'] += 1
            merchant_data['last_date'] = max(
                merchant_data['last_date'] or transaction.date,
                transaction.date
            )

            month_key = transaction.date.strftime('%Y-%m')
            if month_key not in category_data[category]['monthly_data']:
                category_data[category]['monthly_data'][month_key] = 0.0
            category_data[category]['monthly_data'][month_key] += amount

        return category_data, total_expense

    def _calculate_statistics(self, category_data, total_expense):
        """计算统计信息"""
        for category, data in category_data.items():
            data['percentage'] = (data['total_amount'] / total_expense * 100) if total_expense > 0 else 0
            data['avg_amount'] = data['total_amount'] / data['transaction_count'] if data['transaction_count'] > 0 else 0

            for merchant_data in data['merchants'].values():
                merchant_data['avg_amount'] = (
                    merchant_data['total_amount'] / merchant_data['transaction_count']
                    if merchant_data['transaction_count'] > 0 else 0
                )

            data['merchants'] = dict(sorted(
                data['merchants'].items(),
                key=lambda x: x[1]['total_amount'],
                reverse=True
            ))

    def _build_analysis_result(self, category_data, total_expense, start_date, end_date):
        """构建分析结果"""
        result = {
            'categories': {},
            'summary': {
                'total_expense': total_expense,
                'analyzed_period': f"{start_date} to {end_date}",
                'total_merchants': sum(len(data['merchants']) for data in category_data.values()),
                'total_transactions': sum(data['transaction_count'] for data in category_data.values())
            }
        }

        for category, data in category_data.items():
            display_info = self.get_category_display_info(category)
            result['categories'][category] = {**data, **display_info}

        result['categories'] = dict(sorted(
            result['categories'].items(),
            key=lambda x: x[1]['total_amount'],
            reverse=True
        ))

        self.logger.info(f"支出分析完成，共分析 {len(category_data)} 个类别")
        return result

    def _get_empty_result(self, start_date, end_date):
        """获取空结果"""
        return {
            'categories': {},
            'summary': {
                'total_expense': 0.0,
                'analyzed_period': f"{start_date} to {end_date}",
                'total_merchants': 0,
                'total_transactions': 0
            }
        }

    def get_available_months(self) -> Dict[str, Any]:
        """获取数据库中有交易数据的所有月份列表"""
        try:
            transactions = self.db.query(Transaction).filter(
                Transaction.amount < 0,
                Transaction.counterparty.isnot(None),
                Transaction.counterparty != ''
            ).all()

            if not transactions:
                return {
                    'months': [],
                    'latest_month': None,
                    'total_months': 0,
                    'month_stats': {}
                }

            month_stats = {}
            for transaction in transactions:
                month_key = transaction.date.strftime('%Y-%m')
                if month_key not in month_stats:
                    month_stats[month_key] = {
                        'transaction_count': 0,
                        'total_amount': 0.0
                    }

                month_stats[month_key]['transaction_count'] += 1
                month_stats[month_key]['total_amount'] += float(abs(transaction.amount))

            sorted_months = sorted(month_stats.keys(), reverse=True)
            latest_month = sorted_months[0] if sorted_months else None

            self.logger.info(f"找到 {len(sorted_months)} 个有数据的月份，最新月份: {latest_month}")

            return {
                'months': sorted_months,
                'latest_month': latest_month,
                'total_months': len(sorted_months),
                'month_stats': month_stats
            }

        except Exception as e:
            self.logger.error(f"获取可用月份失败: {e}")
            return {
                'months': [],
                'latest_month': None,
                'total_months': 0,
                'month_stats': {}
            }

    def get_month_expense_analysis(self, target_month: str,
                                 category_filter: Optional[str] = None,
                                 search_term: Optional[str] = None) -> Dict[str, Any]:
        """获取指定月份的支出分析数据"""
        try:
            from calendar import monthrange

            month_date = datetime.strptime(target_month, '%Y-%m').date()
            start_date = month_date.replace(day=1)
            last_day = monthrange(month_date.year, month_date.month)[1]
            end_date = month_date.replace(day=last_day)

            self.logger.info(f"开始分析 {target_month} 月份的支出数据")

            single_month_result = self.get_expense_analysis_by_category(
                start_date=start_date,
                end_date=end_date,
                category_filter=category_filter,
                search_term=search_term
            )

            full_history_result = self.get_expense_analysis_by_category(
                start_date=None,
                end_date=None,
                category_filter=category_filter,
                search_term=search_term
            )

            result = single_month_result.copy()

            for category in result['categories']:
                if category in full_history_result['categories']:
                    result['categories'][category]['monthly_data'] = full_history_result['categories'][category].get('monthly_data', {})

            result['target_month'] = target_month
            result['period'] = {
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'month': target_month
            }

            result['summary']['analyzed_period'] = f"{start_date} to {end_date}"

            self.logger.info(f"{target_month} 月份支出分析完成")
            return result

        except Exception as e:
            self.logger.error(f"月份支出分析失败: {e}")
            return {
                'categories': {},
                'summary': {
                    'total_expense': 0.0,
                    'analyzed_period': target_month,
                    'total_merchants': 0,
                    'total_transactions': 0
                },
                'target_month': target_month,
                'period': {
                    'start_date': None,
                    'end_date': None,
                    'month': target_month
                }
            }

    def get_category_monthly_trend(self, category: str, months: int = 12) -> List[Dict[str, Any]]:
        """获取指定类别的月度趋势数据"""
        try:
            start_date, end_date = DateUtils.get_date_range(months)

            transactions = self.db.query(Transaction).filter(
                Transaction.amount < 0,
                Transaction.date >= start_date,
                Transaction.date <= end_date,
                Transaction.counterparty.isnot(None),
                Transaction.counterparty != ''
            ).all()

            category_transactions = [
                t for t in transactions
                if self.classify_merchant(t.counterparty) == category
            ]

            monthly_data = {}
            for transaction in category_transactions:
                month_key = transaction.date.strftime('%Y-%m')
                if month_key not in monthly_data:
                    monthly_data[month_key] = {
                        'month': month_key,
                        'amount': 0.0,
                        'transaction_count': 0
                    }

                monthly_data[month_key]['amount'] += float(abs(transaction.amount))
                monthly_data[month_key]['transaction_count'] += 1

            result = list(monthly_data.values())
            result.sort(key=lambda x: x['month'])

            return result

        except Exception as e:
            self.logger.error(f"获取类别月度趋势失败: {e}")
            return []

    def get_merchant_details_by_category(self, category: str, limit: int = 50) -> List[Dict[str, Any]]:
        """获取指定类别下的商户详情"""
        try:
            start_date, end_date = DateUtils.get_date_range(6)

            transactions = self.db.query(Transaction).filter(
                Transaction.amount < 0,
                Transaction.date >= start_date,
                Transaction.date <= end_date,
                Transaction.counterparty.isnot(None),
                Transaction.counterparty != ''
            ).all()

            merchant_data = {}
            for transaction in transactions:
                if self.classify_merchant(transaction.counterparty) == category:
                    merchant = transaction.counterparty
                    if merchant not in merchant_data:
                        merchant_data[merchant] = {
                            'merchant_name': merchant,
                            'total_amount': 0.0,
                            'transaction_count': 0,
                            'avg_amount': 0.0,
                            'last_date': None,
                            'first_date': None,
                            'transactions': []
                        }

                    amount = float(abs(transaction.amount))
                    data = merchant_data[merchant]
                    data['total_amount'] += amount
                    data['transaction_count'] += 1
                    data['last_date'] = max(data['last_date'] or transaction.date, transaction.date)
                    data['first_date'] = min(data['first_date'] or transaction.date, transaction.date)

                    data['transactions'].append({
                        'date': transaction.date.strftime('%Y-%m-%d'),
                        'amount': amount,
                        'description': transaction.description or ''
                    })

            for data in merchant_data.values():
                data['avg_amount'] = data['total_amount'] / data['transaction_count'] if data['transaction_count'] > 0 else 0
                data['last_date'] = data['last_date'].strftime('%Y-%m-%d') if data['last_date'] else None
                data['first_date'] = data['first_date'].strftime('%Y-%m-%d') if data['first_date'] else None
                data['transactions'].sort(key=lambda x: x['date'], reverse=True)

            result = sorted(merchant_data.values(), key=lambda x: x['total_amount'], reverse=True)
            return result[:limit]

        except Exception as e:
            self.logger.error(f"获取商户详情失败: {e}")
            return []

    def get_merchant_transactions(self, merchant_name: str, limit: int = 20, month: Optional[str] = None) -> Dict[str, Any]:
        """获取指定商户的交易记录"""
        try:
            query = self.db.query(Transaction).filter(
                Transaction.amount < 0,
                Transaction.counterparty == merchant_name
            )

            month_start = None
            month_end = None
            if month:
                try:
                    month_start, month_end = DateUtils.get_month_boundaries(month)
                    query = query.filter(
                        Transaction.date >= month_start,
                        Transaction.date <= month_end
                    )
                    self.logger.info(f"筛选商户 {merchant_name} 在 {month} 的交易记录")
                except ValueError as e:
                    self.logger.error(f"月份参数格式错误: {month}, 错误: {e}")

            transactions = query.order_by(Transaction.date.desc()).limit(limit).all()

            if not transactions:
                period_info = "所有时间" if not month else f"{month}月"
                return {
                    'merchant_name': merchant_name,
                    'category': 'other',
                    'category_info': self.get_category_display_info('other'),
                    'transactions': [],
                    'statistics': {
                        'total_amount': 0.0,
                        'average_amount': 0.0,
                        'transaction_count': 0
                    },
                    'filter_info': {
                        'filtered_month': month,
                        'period_info': period_info,
                        'date_range': {
                            'start': month_start.strftime('%Y-%m-%d') if month_start else None,
                            'end': month_end.strftime('%Y-%m-%d') if month_end else None
                        }
                    }
                }

            transaction_list = []
            total_amount = 0.0

            for t in transactions:
                amount = float(abs(t.amount))
                total_amount += amount
                transaction_list.append({
                    'date': t.date.strftime('%Y-%m-%d'),
                    'amount': amount,
                    'description': t.description or '',
                    'account': t.account.account_name if t.account else ''
                })

            avg_amount = total_amount / len(transactions) if transactions else 0
            category = self.classify_merchant(merchant_name)
            period_info = "所有时间" if not month else f"{month}月"

            return {
                'merchant_name': merchant_name,
                'category': category,
                'category_info': self.get_category_display_info(category),
                'transactions': transaction_list,
                'statistics': {
                    'total_amount': total_amount,
                    'average_amount': avg_amount,
                    'transaction_count': len(transactions)
                },
                'filter_info': {
                    'filtered_month': month,
                    'period_info': period_info,
                    'date_range': {
                        'start': month_start.strftime('%Y-%m-%d') if month_start else None,
                        'end': month_end.strftime('%Y-%m-%d') if month_end else None
                    }
                }
            }

        except Exception as e:
            self.logger.error(f"获取商户交易记录失败 {merchant_name}: {e}")
            period_info = "所有时间" if not month else f"{month}月"

            return {
                'merchant_name': merchant_name,
                'category': 'other',
                'category_info': self.get_category_display_info('other'),
                'transactions': [],
                'statistics': {
                    'total_amount': 0.0,
                    'average_amount': 0.0,
                    'transaction_count': 0
                },
                'filter_info': {
                    'filtered_month': month,
                    'period_info': period_info,
                    'date_range': {
                        'start': None,
                        'end': None
                    }
                }
            }



