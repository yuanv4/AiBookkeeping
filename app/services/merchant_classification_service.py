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
    
    def classify_merchant(self, merchant_name: str) -> str:
        """
        对商户进行分类
        
        Args:
            merchant_name: 商户名称
            
        Returns:
            商户类别 ('dining', 'transport', 'shopping', 'services', 'healthcare', 'finance', 'other')
        """
        if not merchant_name:
            return 'other'
        
        merchant_lower = merchant_name.lower()
        
        # 检查是否为排除的商户类型
        for excluded in self.excluded_keywords:
            if excluded in merchant_name:
                return 'other'
        
        # 按优先级进行分类匹配
        for category, keywords in self.category_keywords.items():
            for keyword in keywords:
                if keyword in merchant_name:
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
        """
        按商户类别分析支出数据

        Args:
            start_date: 开始日期，默认为6个月前
            end_date: 结束日期，默认为今天
            category_filter: 分类筛选，只返回指定分类的数据
            search_term: 搜索词，筛选包含该词的商户

        Returns:
            按类别组织的支出分析数据
        """
        try:
            # 设置默认日期范围（最近6个月）
            if not end_date:
                end_date = date.today()
            if not start_date:
                from dateutil.relativedelta import relativedelta
                start_date = end_date - relativedelta(months=6)
            
            self.logger.info(f"开始分析支出数据，时间范围：{start_date} 到 {end_date}")
            
            # 查询所有支出交易
            transactions = self.db.query(Transaction).filter(
                Transaction.amount < 0,
                Transaction.date >= start_date,
                Transaction.date <= end_date,
                Transaction.counterparty.isnot(None),
                Transaction.counterparty != ''
            ).all()
            
            self.logger.info(f"找到 {len(transactions)} 条支出交易记录")
            
            # 按商户分类汇总
            category_data = {}
            total_expense = 0.0
            
            for transaction in transactions:
                category = self.classify_merchant(transaction.counterparty)
                merchant = transaction.counterparty
                amount = float(abs(transaction.amount))

                # 应用分类筛选
                if category_filter and category != category_filter:
                    continue

                # 应用搜索筛选
                if search_term and search_term.lower() not in merchant.lower():
                    continue

                total_expense += amount
                
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
                
                # 按商户汇总
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
            from dateutil.relativedelta import relativedelta
            end_date = date.today()
            start_date = end_date - relativedelta(months=months)

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
            from dateutil.relativedelta import relativedelta
            end_date = date.today()
            start_date = end_date - relativedelta(months=6)

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

    def get_merchant_transactions(self, merchant_name: str, limit: int = 20) -> Dict[str, Any]:
        """
        获取指定商户的交易记录

        Args:
            merchant_name: 商户名称
            limit: 返回交易数量限制

        Returns:
            商户交易详情
        """
        try:
            transactions = self.db.query(Transaction).filter(
                Transaction.amount < 0,
                Transaction.counterparty == merchant_name
            ).order_by(Transaction.date.desc()).limit(limit).all()

            if not transactions:
                return {
                    'merchant_name': merchant_name,
                    'category': 'other',
                    'transactions': [],
                    'statistics': {
                        'total_amount': 0.0,
                        'average_amount': 0.0,
                        'transaction_count': 0
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

            return {
                'merchant_name': merchant_name,
                'category': category,
                'category_info': self.get_category_display_info(category),
                'transactions': transaction_list,
                'statistics': {
                    'total_amount': total_amount,
                    'average_amount': avg_amount,
                    'transaction_count': len(transactions)
                }
            }

        except Exception as e:
            self.logger.error(f"获取商户交易记录失败 {merchant_name}: {e}")
            return {
                'merchant_name': merchant_name,
                'category': 'other',
                'transactions': [],
                'statistics': {
                    'total_amount': 0.0,
                    'average_amount': 0.0,
                    'transaction_count': 0
                }
            }
