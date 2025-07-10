#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
支出分析算法模块
基于优化的固定支出识别算法，提供智能的支出分类和分析功能
"""

import math
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime, date
from app.models import Transaction


class ExpenseAlgorithm:
    """优化的支出分析算法类"""
    
    def __init__(self):
        """初始化算法参数"""
        self.excluded_keywords = [
            '京东', '淘宝', '天猫', '拼多多', '平台商户', '网络科技', '电子商务',
            '游戏', '娱乐', 'ktv', '酒吧', '电影', '健身', '运动'
        ]
    
    def get_merchant_category_and_necessity(self, merchant_name: str) -> Tuple[str, float, bool]:
        """
        获取商户类别和生活必需性评分
        
        Args:
            merchant_name: 商户名称
            
        Returns:
            Tuple[category, necessity_score, is_excluded]
        """
        merchant_lower = merchant_name.lower()
        
        # 排除的商户类型（不算固定支出）
        for pattern in self.excluded_keywords:
            if pattern in merchant_name:
                return 'excluded', 0, True
        
        # 餐饮类固定支出 - 对应前端第一列
        if any(keyword in merchant_name for keyword in ['餐厅', '咖啡', '早餐', '午餐', '晚餐', '肠粉', '面', '饭', '茶', '奶茶', '食堂', '麦当劳', '肯德基', '星巴克', '喜茶', '蜜雪冰城', '沙县', '兰州拉面', '黄焖鸡', '煲仔饭', '盖浇饭', '快餐', '外卖', '美食', '小吃', '烧烤', '火锅', '川菜', '粤菜', '湘菜']):
            return 'dining', 90, False
        # 交通类固定支出 - 对应前端第二列
        elif any(keyword in merchant_name for keyword in ['深圳通', '地铁', '公交', '打车', '高德', '滴滴', '出租', '停车', '加油', '中石油', '中石化', '共享单车', '摩拜', '哈啰', '青桔', '网约车', '出行', '租车', '代驾']):
            return 'transport', 95, False
        # 通信类 - 归入其他类
        elif any(keyword in merchant_name for keyword in ['移动', '联通', '电信', '宽带', '网络', '话费', '流量']):
            return 'communication', 95, False
        # 日常购物类 - 归入其他类
        elif any(keyword in merchant_name for keyword in ['超市', '便利店', '7-11', 'ace', '全家', '罗森', '华润万家', '沃尔玛', '家乐福', '永辉', '大润发']):
            return 'daily_shopping', 85, False
        
        # 中等必需性商户 - 归入其他类
        elif any(keyword in merchant_name for keyword in ['商场', '天虹', '万象城', '海岸城', '购物中心']):
            return 'shopping', 70, False
        elif any(keyword in merchant_name for keyword in ['理发', '美容', '洗衣', '维修', '快递', '顺丰', '圆通', '中通', '申通', '韵达']):
            return 'services', 75, False
        elif any(keyword in merchant_name for keyword in ['药店', '体检', '牙科', '眼科', '医疗', '诊所']):
            return 'healthcare', 80, False
        
        # 大额固定支出（需要特殊处理）
        elif any(keyword in merchant_name for keyword in ['保险', '人寿', '平安', '太平洋', '中国人寿', '泰康']):
            return 'insurance', 85, False
        elif any(keyword in merchant_name for keyword in ['医院', '住院', '三甲医院', '人民医院', '中医院']):
            return 'medical', 70, False
        elif '微信转账' in merchant_name:
            return 'transfer', 60, False

        # 其他商户 - 对应前端第三列
        else:
            return 'other', 50, False

    def get_display_category(self, category: str) -> str:
        """
        将内部分类转换为前端显示分类

        Args:
            category: 内部分类标识

        Returns:
            前端显示分类 ('dining', 'transport', 'other')
        """
        # 餐饮类
        if category == 'dining':
            return 'dining'
        # 交通类
        elif category == 'transport':
            return 'transport'
        # 其他类（包含通信、购物、服务、医疗等）
        else:
            return 'other'
    
    def analyze_transfer_pattern(self, transactions: List[Transaction]) -> Tuple[bool, str, float]:
        """
        分析微信转账等转账类交易的模式
        
        Args:
            transactions: 交易记录列表
            
        Returns:
            Tuple[is_fixed, transfer_type, confidence]
        """
        amounts = [float(abs(t.amount)) for t in transactions]
        intervals = []
        
        for i in range(1, len(transactions)):
            interval = (transactions[i].date - transactions[i-1].date).days
            intervals.append(interval)
        
        # 分析金额模式
        unique_amounts = list(set(amounts))
        avg_amount = sum(amounts) / len(amounts)
        
        # 分析时间模式
        avg_interval = sum(intervals) / len(intervals) if intervals else 0
        
        # 判断是否为房租等固定转账
        if len(unique_amounts) <= 2 and avg_amount >= 1000:  # 金额固定且较大
            if 25 <= avg_interval <= 35:  # 月度间隔
                return True, 'rent', 90  # 很可能是房租
            elif avg_interval >= 60:  # 季度或更长间隔
                return True, 'periodic_large', 70  # 可能是季度费用
        
        # 判断是否为生活费等定期转账
        elif 500 <= avg_amount <= 3000:
            if 25 <= avg_interval <= 35:  # 月度间隔
                return True, 'living_expense', 80  # 可能是生活费
            elif 7 <= avg_interval <= 14:  # 双周间隔
                return True, 'biweekly_expense', 75
        
        # 判断是否为偶发大额支出
        elif avg_amount >= 5000:
            if avg_interval >= 90:  # 间隔很长
                return False, 'occasional_large', 30  # 偶发大额，不算固定支出
        
        # 其他情况
        return False, 'irregular', 40
    
    def calculate_optimized_score(self, transactions: List[Transaction]) -> Optional[Dict[str, Any]]:
        """
        优化的固定支出评分算法
        
        Args:
            transactions: 交易记录列表
            
        Returns:
            评分结果字典或None
        """
        if len(transactions) < 3:
            return None
        
        merchant_name = transactions[0].counterparty
        category, necessity_score, is_excluded = self.get_merchant_category_and_necessity(merchant_name)
        
        # 排除的商户直接返回0分
        if is_excluded:
            return {
                'total_score': 0,
                'category': category,
                'reason': 'excluded_merchant'
            }
        
        # 计算各项评分
        intervals = []
        amounts = [float(abs(t.amount)) for t in transactions]
        
        for i in range(1, len(transactions)):
            interval = (transactions[i].date - transactions[i-1].date).days
            intervals.append(interval)
        
        avg_amount = sum(amounts) / len(amounts)
        avg_interval = sum(intervals) / len(intervals) if intervals else 0
        
        # 特殊处理转账类交易
        if category == 'transfer':
            is_fixed, transfer_type, transfer_confidence = self.analyze_transfer_pattern(transactions)
            if not is_fixed:
                return {
                    'total_score': transfer_confidence,
                    'category': f'transfer_{transfer_type}',
                    'reason': 'not_fixed_transfer',
                    'transfer_analysis': f'{transfer_type} (confidence: {transfer_confidence})',
                    'avg_amount': avg_amount,
                    'transaction_count': len(transactions),
                    'avg_interval': avg_interval
                }
            else:
                # 是固定转账，调整必需性评分
                necessity_score = transfer_confidence
                category = f'transfer_{transfer_type}'
        
        # 1. 时间规律性评分 (25% 权重，降低)
        if intervals:
            mean_interval = sum(intervals) / len(intervals)
            if mean_interval > 0:
                variance = sum((x - mean_interval) ** 2 for x in intervals) / len(intervals)
                std_dev = math.sqrt(variance)
                
                # 对高频消费放宽时间规律性要求
                if mean_interval <= 7:  # 高频消费
                    time_regularity = max(40, 100 - (std_dev / mean_interval * 60))
                else:  # 低频消费
                    time_regularity = max(0, 100 - (std_dev / mean_interval * 100))
            else:
                time_regularity = 0
        else:
            time_regularity = 0
        
        # 2. 生活必需性评分 (35% 权重，新增)
        necessity_score_final = necessity_score
        
        # 3. 金额合理性评分 (25% 权重)
        # 根据金额范围评分
        if avg_amount <= 20:  # 小额高频消费
            amount_reasonableness = 90
        elif avg_amount <= 100:  # 中等金额消费
            amount_reasonableness = 85
        elif avg_amount <= 500:  # 较大金额消费
            amount_reasonableness = 70
        elif avg_amount <= 2000:  # 大额消费（可能是房租等）
            amount_reasonableness = 60
        else:  # 超大额消费
            amount_reasonableness = 30
        
        # 金额稳定性加分
        if amounts:
            mean_amount = sum(amounts) / len(amounts)
            variance = sum((x - mean_amount) ** 2 for x in amounts) / len(amounts)
            std_dev = math.sqrt(variance)
            stability_bonus = max(0, 20 - (std_dev / mean_amount * 20)) if mean_amount > 0 else 0
            amount_reasonableness = min(100, amount_reasonableness + stability_bonus)
        
        # 4. 频率适中性评分 (15% 权重)
        if avg_interval <= 0:
            frequency_score = 0
        elif avg_interval <= 3:  # 过于频繁
            frequency_score = 70
        elif avg_interval <= 7:  # 高频，合理
            frequency_score = 95
        elif avg_interval <= 30:  # 中频，合理
            frequency_score = 90
        elif avg_interval <= 60:  # 低频，可能固定
            frequency_score = 75
        else:  # 过于稀少
            frequency_score = 40
        
        # 综合评分
        total_score = (
            time_regularity * 0.25 +
            necessity_score_final * 0.35 +
            amount_reasonableness * 0.25 +
            frequency_score * 0.15
        )
        
        return {
            'total_score': round(total_score, 1),
            'time_regularity': round(time_regularity, 1),
            'necessity_score': round(necessity_score_final, 1),
            'amount_reasonableness': round(amount_reasonableness, 1),
            'frequency_score': round(frequency_score, 1),
            'category': category,
            'display_category': self.get_display_category(category),  # 添加前端显示分类
            'avg_interval': round(avg_interval, 1),
            'avg_amount': round(avg_amount, 2),
            'transaction_count': len(transactions),
            'intervals': intervals,
            'amounts': amounts
        }
    
    def classify_fixed_expenses(self, results: List[Dict[str, Any]]) -> Tuple[List[str], List[str]]:
        """
        分类固定支出商户
        
        Args:
            results: 算法评分结果列表
            
        Returns:
            Tuple[daily_fixed_merchants, large_fixed_merchants]
        """
        daily_fixed_merchants = []
        large_fixed_merchants = []
        
        for result in results:
            if result['total_score'] >= 50:
                # 日常固定支出：高频小额，生活必需
                if result['category'] in ['dining', 'transport', 'daily_shopping', 'communication'] and result['avg_amount'] <= 200:
                    daily_fixed_merchants.append(result['merchant'])
                # 大额固定支出：房租、保险、医疗等
                elif result['category'] in ['insurance', 'medical', 'transfer_rent', 'transfer_living_expense', 'transfer_periodic_large']:
                    large_fixed_merchants.append(result['merchant'])
                # 根据金额判断
                elif result['avg_amount'] > 500:
                    large_fixed_merchants.append(result['merchant'])
                else:
                    daily_fixed_merchants.append(result['merchant'])
            # 中等置信度的转账也可能是固定支出
            elif 40 <= result['total_score'] < 50 and 'transfer' in result['category']:
                if 'avg_amount' in result and result['avg_amount'] >= 1000:  # 大额转账
                    large_fixed_merchants.append(result['merchant'])
        
        return daily_fixed_merchants, large_fixed_merchants
