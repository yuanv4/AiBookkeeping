#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
支出分析服务模块

专门负责支出数据的分析和统计功能。
"""

import logging
from datetime import date, datetime
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session

from app.models import Transaction, db
from .models import DateUtils
from .category_service import CategoryService

logger = logging.getLogger(__name__)


class ExpenseAnalysisService:
    """支出分析服务
    
    专门负责支出数据的分析和统计功能。
    """
    
    def __init__(self, db_session: Optional[Session] = None, category_service: Optional[CategoryService] = None):
        """初始化支出分析服务
        
        Args:
            db_session: 数据库会话，如果为None则使用默认会话
            category_service: 分类服务实例，如果为None则创建新实例
        """
        self.logger = logging.getLogger(__name__)
        self.db = db_session or db.session
        self.category_service = category_service or CategoryService()
    
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
            category = self.category_service.classify_merchant(merchant)

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
            display_info = self.category_service.get_category_display_info(category)
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
