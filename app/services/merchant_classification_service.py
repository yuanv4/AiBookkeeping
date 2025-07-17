#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
商户分类服务模块

提供基于商户名称的智能分类功能，支持支出分析和统计。
替代原有的固定支出分析算法，专注于商户类型识别和分类汇总。
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Transaction, db
from app.utils.query_cache import cached_query
from .models import DateUtils

logger = logging.getLogger(__name__)


class MerchantClassificationService:
    """商户分类服务
    
    提供商户类型识别、支出分类汇总、趋势分析等功能。
    """
    
    def __init__(self, db_session: Optional[Session] = None):
        """初始化商户分类服务
        
        Args:
            db_session: 数据库会话，如果为None则使用默认会话
        """
        self.db = db_session or db.session
        self.logger = logging.getLogger(__name__)

        # 商户分类关键词配置
        self.category_keywords = {
            'dining': [
                '餐厅', '咖啡', '早餐', '午餐', '晚餐', '肠粉', '面', '饭', '茶', '奶茶', 
                '食堂', '麦当劳', '肯德基', '星巴克', '喜茶', '蜜雪冰城', '沙县', 
                '兰州拉面', '黄焖鸡', '煲仔饭', '盖浇饭', '快餐', '外卖', '美食', 
                '小吃', '烧烤', '火锅', '川菜', '粤菜', '湘菜', '小湘厨', '潮汕汤粉'
            ],
            'transport': [
                '深圳通', '地铁', '公交', '打车', '高德', '滴滴', '出租', '停车', 
                '加油', '中石油', '中石化', '共享单车', '摩拜', '哈啰', '青桔', 
                '网约车', '出行', '租车', '代驾'
            ],
            'shopping': [
                '京东', '淘宝', '天猫', '拼多多', '超市', '便利店', '7-11', 'ace', 
                '全家', '罗森', '华润万家', '沃尔玛', '家乐福', '永辉', '大润发',
                '商场', '天虹', '万象城', '海岸城', '购物中心', '网购', '电商'
            ],
            'services': [
                '理发', '美容', '洗衣', '维修', '快递', '顺丰', '圆通', '中通', 
                '申通', '韵达', '移动', '联通', '电信', '宽带', '网络', '话费', '流量'
            ],
            'healthcare': [
                '药店', '体检', '牙科', '眼科', '医疗', '诊所', '医院', '住院', 
                '三甲医院', '人民医院', '中医院'
            ],
            'finance': [
                '保险', '人寿', '平安', '太平洋', '中国人寿', '泰康', '银行', '转账'
            ]
        }
        
        # 排除的关键词（这些通常不是日常消费）
        self.excluded_keywords = [
            '游戏', '娱乐', 'ktv', '酒吧', '电影', '健身', '运动'
        ]

    def _build_expense_query(self, start_date=None, end_date=None, counterparty_filter=None):
        """构建支出交易的基础查询 - 统一查询构建器

        Args:
            start_date: 开始日期
            end_date: 结束日期
            counterparty_filter: 交易对手过滤条件

        Returns:
            Query: 配置好的查询对象
        """
        # 基础查询条件：支出交易且有有效交易对手
        # 建议：为Transaction表添加复合索引：(amount, date, counterparty)
        query = self.db.query(Transaction).filter(
            Transaction.amount < 0,
            Transaction.counterparty.isnot(None),
            Transaction.counterparty != ''
        )

        # 添加日期范围过滤
        if start_date:
            query = query.filter(Transaction.date >= start_date)
        if end_date:
            query = query.filter(Transaction.date <= end_date)

        # 添加交易对手过滤
        if counterparty_filter:
            query = query.filter(Transaction.counterparty.ilike(f'%{counterparty_filter}%'))

        return query

    @cached_query(ttl=3600)  # 缓存1小时，商户分类结果相对稳定
    def classify_merchant(self, merchant_name: str) -> str:
        """对商户进行分类

        Args:
            merchant_name: 商户名称

        Returns:
            商户类别 ('dining', 'transport', 'shopping', 'services', 'healthcare', 'finance', 'other')
        """
        if not merchant_name:
            return 'other'

        # 优先检查排除关键词
        if any(excluded in merchant_name for excluded in self.excluded_keywords):
            return 'other'

        # 按优先级进行分类匹配，一旦找到匹配就立即返回
        for category, keywords in self.category_keywords.items():
            if any(keyword in merchant_name for keyword in keywords):
                return category

        # 默认分类
        return 'other'
    
    def get_category_display_info(self, category: str) -> Dict[str, str]:
        """
        获取分类的显示信息
        
        Args:
            category: 分类标识
            
        Returns:
            包含名称、颜色、描述的字典
        """
        category_info = {
            'dining': {
                'name': '餐饮支出',
                'color': 'primary',
                'description': '餐厅、咖啡、外卖等饮食消费',
                'icon': 'coffee'
            },
            'transport': {
                'name': '交通支出',
                'color': 'success',
                'description': '地铁、打车、加油等出行费用',
                'icon': 'car'
            },
            'shopping': {
                'name': '购物支出',
                'color': 'info',
                'description': '网购、超市、商场等购物消费',
                'icon': 'shopping-bag'
            },
            'services': {
                'name': '生活服务',
                'color': 'warning',
                'description': '通信、快递、美容等服务费用',
                'icon': 'settings'
            },
            'healthcare': {
                'name': '医疗健康',
                'color': 'danger',
                'description': '医院、药店、体检等医疗支出',
                'icon': 'heart'
            },
            'finance': {
                'name': '金融保险',
                'color': 'secondary',
                'description': '保险、转账等金融相关支出',
                'icon': 'credit-card'
            },
            'other': {
                'name': '其他支出',
                'color': 'dark',
                'description': '未分类的其他支出',
                'icon': 'more-horizontal'
            }
        }
        
        return category_info.get(category, category_info['other'])
    
    def get_expense_analysis_by_category(self, start_date: Optional[date] = None,
                                       end_date: Optional[date] = None,
                                       category_filter: Optional[str] = None,
                                       search_term: Optional[str] = None) -> Dict[str, Any]:
        """按商户类别分析支出数据

        Args:
            start_date: 开始日期，默认为6个月前
            end_date: 结束日期，默认为今天
            category_filter: 分类筛选，只返回指定分类的数据
            search_term: 搜索词，筛选包含该词的商户

        Returns:
            Dict[str, Any]: 包含以下结构的字典：
                - categories: 按类别组织的支出数据
                - summary: 汇总统计信息
                    - total_expense: 总支出金额
                    - analyzed_period: 分析时间段
                    - total_merchants: 商户总数
                    - total_transactions: 交易总数
        """
        try:
            # 设置默认日期范围（最近6个月），但允许None值表示不限制
            use_date_filter = True
            if start_date is None and end_date is None:
                # 如果两个都是None，则不使用日期过滤
                use_date_filter = False
                self.logger.info("开始分析支出数据，不限制时间范围（获取所有历史数据）")
            else:
                # 设置默认值
                if not end_date:
                    end_date = date.today()
                if not start_date:
                    # 使用DateUtils计算6个月前的日期
                    start_date, _ = DateUtils.get_date_range(6, end_date)
                self.logger.info(f"开始分析支出数据，时间范围：{start_date} 到 {end_date}")

            # 构建查询条件 - 优化：使用索引字段进行过滤
            # 建议：为Transaction表的amount、counterparty、date字段添加数据库索引以提升查询性能
            query = self.db.query(Transaction).filter(
                Transaction.amount < 0,
                Transaction.counterparty.isnot(None),
                Transaction.counterparty != ''
            )

            # 根据需要添加日期过滤
            if use_date_filter:
                query = query.filter(
                    Transaction.date >= start_date,
                    Transaction.date <= end_date
                )

            transactions = query.all()
            
            self.logger.info(f"找到 {len(transactions)} 条支出交易记录")
            
            # 按商户分类汇总
            category_data = {}
            total_expense = 0.0

            # 预先过滤搜索条件，减少后续处理量
            if search_term:
                search_term_lower = search_term.lower()
                transactions = [t for t in transactions
                              if search_term_lower in t.counterparty.lower()]

            for transaction in transactions:
                merchant = transaction.counterparty
                amount = float(abs(transaction.amount))

                # 使用缓存的分类方法，避免重复计算
                category = self.classify_merchant(merchant)

                # 应用分类筛选
                if category_filter and category != category_filter:
                    continue

                total_expense += amount

                # 使用 setdefault 简化字典初始化
                if category not in category_data:
                    category_data[category] = {
                        'total_amount': 0.0,
                        'transaction_count': 0,
                        'merchants': {},
                        'monthly_data': {}
                    }

                # 累加类别总金额
                category_data[category]['total_amount'] += amount
                category_data[category]['transaction_count'] += 1

                # 按商户汇总，使用 setdefault 简化初始化
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
                
                # 按月汇总
                month_key = transaction.date.strftime('%Y-%m')
                if month_key not in category_data[category]['monthly_data']:
                    category_data[category]['monthly_data'][month_key] = 0.0
                category_data[category]['monthly_data'][month_key] += amount
            
            # 计算百分比和平均值
            for category, data in category_data.items():
                data['percentage'] = (data['total_amount'] / total_expense * 100) if total_expense > 0 else 0
                data['avg_amount'] = data['total_amount'] / data['transaction_count'] if data['transaction_count'] > 0 else 0
                
                # 计算商户平均金额并排序
                for merchant_data in data['merchants'].values():
                    merchant_data['avg_amount'] = (
                        merchant_data['total_amount'] / merchant_data['transaction_count'] 
                        if merchant_data['transaction_count'] > 0 else 0
                    )
                
                # 按金额排序商户
                data['merchants'] = dict(sorted(
                    data['merchants'].items(),
                    key=lambda x: x[1]['total_amount'],
                    reverse=True
                ))
            
            # 构建返回结果
            result = {
                'categories': {},
                'summary': {
                    'total_expense': total_expense,
                    'analyzed_period': f"{start_date} to {end_date}",
                    'total_merchants': sum(len(data['merchants']) for data in category_data.values()),
                    'total_transactions': sum(data['transaction_count'] for data in category_data.values())
                }
            }
            
            # 添加分类显示信息
            for category, data in category_data.items():
                display_info = self.get_category_display_info(category)
                result['categories'][category] = {
                    **data,
                    **display_info
                }
            
            # 按金额排序分类
            result['categories'] = dict(sorted(
                result['categories'].items(),
                key=lambda x: x[1]['total_amount'],
                reverse=True
            ))
            
            self.logger.info(f"支出分析完成，共分析 {len(category_data)} 个类别")
            return result
            
        except Exception as e:
            self.logger.error(f"支出分析失败: {e}")
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
        """
        获取数据库中有交易数据的所有月份列表

        Returns:
            包含月份列表和统计信息的字典
        """
        try:
            # 使用DateUtils获取最近6个月的数据

            # 查询所有支出交易
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

            # 按月份统计交易数据
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

            # 按月份排序
            sorted_months = sorted(month_stats.keys(), reverse=True)

            # 确定最佳默认月份（最新且交易数量较多的月份）
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
        """
        获取指定月份的支出分析数据，返回单月数据和历史月度数据

        Args:
            target_month: 目标月份 (YYYY-MM格式)
            category_filter: 分类筛选
            search_term: 搜索词筛选

        Returns:
            指定月份的支出分析结果，categories为单月数据，包含monthly_data历史数据
        """
        try:
            from datetime import datetime
            from calendar import monthrange

            # 解析目标月份
            month_date = datetime.strptime(target_month, '%Y-%m').date()
            start_date = month_date.replace(day=1)
            last_day = monthrange(month_date.year, month_date.month)[1]
            end_date = month_date.replace(day=last_day)

            self.logger.info(f"开始分析 {target_month} 月份的支出数据（单月数据+历史月度数据）")

            # 获取单月的分类数据
            single_month_result = self.get_expense_analysis_by_category(
                start_date=start_date,  # 限制为目标月份
                end_date=end_date,      # 限制为目标月份
                category_filter=category_filter,
                search_term=search_term
            )

            # 获取完整历史数据用于生成monthly_data
            full_history_result = self.get_expense_analysis_by_category(
                start_date=None,  # 不限制日期以获取完整历史数据
                end_date=None,    # 不限制日期以获取完整历史数据
                category_filter=category_filter,
                search_term=search_term
            )

            # 合并单月数据和历史月度数据
            # 使用单月数据作为主要结果，但添加历史月度数据
            result = single_month_result.copy()

            # 为每个分类添加历史月度数据
            for category in result['categories']:
                if category in full_history_result['categories']:
                    # 保留单月的主要数据，但添加历史月度数据
                    result['categories'][category]['monthly_data'] = full_history_result['categories'][category].get('monthly_data', {})

            # 添加月份信息
            result['target_month'] = target_month
            result['period'] = {
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'month': target_month
            }

            # 更新汇总信息的描述
            result['summary']['analyzed_period'] = f"{start_date} to {end_date}"

            self.logger.info(f"{target_month} 月份支出分析完成，返回单月分类数据+历史月度数据")
            self.logger.info(f"单月总支出: {result['summary']['total_expense']}, 分类数: {len(result['categories'])}")

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
        """
        获取指定类别的月度趋势数据

        Args:
            category: 商户类别
            months: 月份数量

        Returns:
            月度趋势数据列表
        """
        try:
            # 使用DateUtils计算日期范围
            start_date, end_date = DateUtils.get_date_range(months)

            # 查询该类别的所有交易
            transactions = self.db.query(Transaction).filter(
                Transaction.amount < 0,
                Transaction.date >= start_date,
                Transaction.date <= end_date,
                Transaction.counterparty.isnot(None),
                Transaction.counterparty != ''
            ).all()

            # 筛选属于指定类别的交易
            category_transactions = [
                t for t in transactions
                if self.classify_merchant(t.counterparty) == category
            ]

            # 按月汇总
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

            # 转换为列表并排序
            result = list(monthly_data.values())
            result.sort(key=lambda x: x['month'])

            return result

        except Exception as e:
            self.logger.error(f"获取类别月度趋势失败: {e}")
            return []

    def get_merchant_details_by_category(self, category: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        获取指定类别下的商户详情

        Args:
            category: 商户类别
            limit: 返回商户数量限制

        Returns:
            商户详情列表
        """
        try:
            # 使用DateUtils计算最近6个月的日期范围
            start_date, end_date = DateUtils.get_date_range(6)

            # 查询所有支出交易
            transactions = self.db.query(Transaction).filter(
                Transaction.amount < 0,
                Transaction.date >= start_date,
                Transaction.date <= end_date,
                Transaction.counterparty.isnot(None),
                Transaction.counterparty != ''
            ).all()

            # 筛选属于指定类别的交易并按商户分组
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

                    # 添加交易详情
                    data['transactions'].append({
                        'date': transaction.date.strftime('%Y-%m-%d'),
                        'amount': amount,
                        'description': transaction.description or ''
                    })

            # 计算平均金额并排序
            for data in merchant_data.values():
                data['avg_amount'] = data['total_amount'] / data['transaction_count'] if data['transaction_count'] > 0 else 0
                data['last_date'] = data['last_date'].strftime('%Y-%m-%d') if data['last_date'] else None
                data['first_date'] = data['first_date'].strftime('%Y-%m-%d') if data['first_date'] else None

                # 按日期排序交易记录
                data['transactions'].sort(key=lambda x: x['date'], reverse=True)

            # 按总金额排序并限制数量
            result = sorted(merchant_data.values(), key=lambda x: x['total_amount'], reverse=True)
            return result[:limit]

        except Exception as e:
            self.logger.error(f"获取商户详情失败: {e}")
            return []

    def get_merchant_transactions(self, merchant_name: str, limit: int = 20, month: Optional[str] = None) -> Dict[str, Any]:
        """
        获取指定商户的交易记录

        Args:
            merchant_name: 商户名称
            limit: 返回交易数量限制
            month: 筛选月份 (YYYY-MM格式)，如果为None则返回所有交易

        Returns:
            商户交易详情
        """
        try:

            # 构建基础查询
            query = self.db.query(Transaction).filter(
                Transaction.amount < 0,
                Transaction.counterparty == merchant_name
            )

            # 添加月份筛选条件
            month_start = None
            month_end = None
            if month:
                try:
                    # 使用DateUtils计算月份边界
                    month_start, month_end = DateUtils.get_month_boundaries(month)

                    # 添加日期范围筛选
                    query = query.filter(
                        Transaction.date >= month_start,
                        Transaction.date <= month_end
                    )

                    self.logger.info(f"筛选商户 {merchant_name} 在 {month} 的交易记录 ({month_start} 到 {month_end})")

                except ValueError as e:
                    self.logger.error(f"月份参数格式错误: {month}, 错误: {e}")
                    # 如果月份格式错误，继续查询所有数据但记录错误

            # 执行查询
            transactions = query.order_by(Transaction.date.desc()).limit(limit).all()

            if not transactions:
                # 构建期间信息
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

            # 转换交易数据
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

            # 计算统计信息
            avg_amount = total_amount / len(transactions) if transactions else 0
            category = self.classify_merchant(merchant_name)

            # 构建期间信息
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
