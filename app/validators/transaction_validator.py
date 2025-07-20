"""交易数据验证器

将Transaction模型中的复杂验证逻辑提取到专门的验证器中，
遵循单一职责原则，使模型专注于数据结构。
"""

from typing import Any, Dict, Optional
from decimal import Decimal, InvalidOperation
from datetime import date, datetime
import logging

logger = logging.getLogger(__name__)


class TransactionValidator:
    """交易数据验证器
    
    提供交易数据的验证和标准化功能。
    """
    
    @staticmethod
    def validate_amount(amount: Any) -> Decimal:
        """验证交易金额
        
        Args:
            amount: 待验证的金额
            
        Returns:
            Decimal: 标准化后的金额
            
        Raises:
            ValueError: 当金额无效时抛出异常
        """
        if amount is None:
            raise ValueError('交易金额不能为空')
        
        try:
            # 转换为Decimal类型
            if isinstance(amount, str):
                # 移除可能的货币符号和空格
                amount = amount.strip().replace('¥', '').replace('$', '').replace(',', '')
            
            decimal_amount = Decimal(str(amount))
            
            # 检查金额范围（避免极端值）
            if abs(decimal_amount) > Decimal('999999999.99'):
                raise ValueError('交易金额超出允许范围')
            
            # 标准化为2位小数
            return decimal_amount.quantize(Decimal('0.01'))
            
        except (InvalidOperation, ValueError) as e:
            raise ValueError(f'无效的交易金额: {amount}') from e
    
    @staticmethod
    def validate_date(date_value: Any) -> date:
        """验证交易日期
        
        Args:
            date_value: 待验证的日期
            
        Returns:
            date: 标准化后的日期
            
        Raises:
            ValueError: 当日期无效时抛出异常
        """
        if date_value is None:
            raise ValueError('交易日期不能为空')
        
        if isinstance(date_value, date):
            return date_value
        
        if isinstance(date_value, datetime):
            return date_value.date()
        
        if isinstance(date_value, str):
            try:
                # 尝试多种日期格式
                date_formats = [
                    '%Y-%m-%d',
                    '%Y/%m/%d',
                    '%d/%m/%Y',
                    '%d-%m-%Y',
                    '%Y%m%d'
                ]
                
                for fmt in date_formats:
                    try:
                        return datetime.strptime(date_value.strip(), fmt).date()
                    except ValueError:
                        continue
                
                raise ValueError(f'无法解析日期格式: {date_value}')
                
            except Exception as e:
                raise ValueError(f'无效的交易日期: {date_value}') from e
        
        raise ValueError(f'不支持的日期类型: {type(date_value)}')
    
    @staticmethod
    def validate_counterparty(counterparty: Any) -> Optional[str]:
        """验证交易对手
        
        Args:
            counterparty: 待验证的交易对手
            
        Returns:
            str: 标准化后的交易对手名称，如果为空则返回None
        """
        if counterparty is None:
            return None
        
        if not isinstance(counterparty, str):
            counterparty = str(counterparty)
        
        # 清理和标准化
        counterparty = counterparty.strip()
        
        if not counterparty:
            return None
        
        # 限制长度
        if len(counterparty) > 200:
            counterparty = counterparty[:200]
        
        return counterparty
    
    @staticmethod
    def validate_currency(currency: Any) -> str:
        """验证货币类型
        
        Args:
            currency: 待验证的货币类型
            
        Returns:
            str: 标准化后的货币代码
        """
        if currency is None:
            return 'CNY'  # 默认人民币
        
        if not isinstance(currency, str):
            currency = str(currency)
        
        currency = currency.strip().upper()
        
        # 支持的货币类型
        supported_currencies = ['CNY', 'USD', 'EUR', 'GBP', 'JPY', 'HKD']
        
        if currency not in supported_currencies:
            logger.warning(f'不支持的货币类型: {currency}，使用默认值CNY')
            return 'CNY'
        
        return currency
    
    @staticmethod
    def validate_category(category: Any) -> Optional[str]:
        """验证商户分类
        
        Args:
            category: 待验证的分类
            
        Returns:
            str: 标准化后的分类，如果为空则返回None
        """
        if category is None:
            return None
        
        if not isinstance(category, str):
            category = str(category)
        
        category = category.strip()
        
        if not category:
            return None
        
        # 限制长度
        if len(category) > 100:
            category = category[:100]
        
        return category
    
    @staticmethod
    def validate_description(description: Any) -> Optional[str]:
        """验证交易描述
        
        Args:
            description: 待验证的描述
            
        Returns:
            str: 标准化后的描述，如果为空则返回None
        """
        if description is None:
            return None
        
        if not isinstance(description, str):
            description = str(description)
        
        description = description.strip()
        
        if not description:
            return None
        
        # 限制长度
        if len(description) > 500:
            description = description[:500]
        
        return description
    
    @classmethod
    def validate_all(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """验证所有交易数据
        
        Args:
            data: 包含交易数据的字典
            
        Returns:
            Dict[str, Any]: 验证和标准化后的数据
            
        Raises:
            ValueError: 当必要字段验证失败时抛出异常
        """
        validated_data = {}
        
        # 验证必要字段
        if 'amount' in data:
            validated_data['amount'] = cls.validate_amount(data['amount'])
        
        if 'date' in data:
            validated_data['date'] = cls.validate_date(data['date'])
        
        # 验证可选字段
        if 'balance_after' in data and data['balance_after'] is not None:
            validated_data['balance_after'] = cls.validate_amount(data['balance_after'])
        
        if 'counterparty' in data:
            validated_data['counterparty'] = cls.validate_counterparty(data['counterparty'])
        
        if 'currency' in data:
            validated_data['currency'] = cls.validate_currency(data['currency'])
        
        if 'category' in data:
            validated_data['category'] = cls.validate_category(data['category'])
        
        if 'description' in data:
            validated_data['description'] = cls.validate_description(data['description'])
        
        # 复制其他字段
        for key, value in data.items():
            if key not in validated_data:
                validated_data[key] = value
        
        return validated_data
