# -*- coding: utf-8 -*-
"""
可配置的交易提取器
==================

通用的、由配置驱动的银行交易提取器实现。
取代了原有的为每家银行编写重复子类的做法。
"""

import pandas as pd
from datetime import datetime
from typing import Optional

from .base_extractor import BaseTransactionExtractor, ExtractionConfig

class ConfigurableTransactionExtractor(BaseTransactionExtractor):
    """可配置的交易提取器
    
    通过配置信息驱动的通用提取器，支持多种银行的数据提取需求。
    """
    
    def __init__(self, bank_code: str, bank_config: dict):
        """初始化可配置提取器
        
        Args:
            bank_code: 银行代码，如 'CCB', 'CMB'
            bank_config: 银行配置字典，包含日期格式、验证方式等信息
        """
        super().__init__(bank_code)
        self.bank_config = bank_config
        self.date_format = bank_config['date_format']
        self.date_validation = bank_config['date_validation']
        self.extraction_config = bank_config['config']
    
    def _convert_date(self, date_str: str) -> Optional[datetime]:
        """将银行日期字符串转换为标准datetime对象
        
        根据配置中指定的日期格式和验证方式进行转换。
        
        Args:
            date_str: 银行日期字符串
            
        Returns:
            datetime: 转换后的标准日期时间对象，转换失败返回None
        """
        if pd.isna(date_str):
            return None
            
        date_str = str(date_str).strip()
        
        # 根据配置的验证方式进行预处理
        if self.date_validation == 'digit':
            # 建设银行类型：纯数字格式验证
            if not date_str.isdigit():
                return None
        elif self.date_validation == 'datetime':
            # 招商银行类型：标准日期时间格式，无需特殊验证
            pass
            
        try:
            return pd.to_datetime(date_str, format=self.date_format)
        except Exception as e:
            self.logger.warning(f"无法解析{self.bank_code}银行日期格式: {date_str}, 错误: {e}")
            return None
    
    def get_extraction_config(self) -> ExtractionConfig:
        """获取银行特定的数据提取配置
        
        Returns:
            ExtractionConfig: 提取配置对象
        """
        return self.extraction_config 