# -*- coding: utf-8 -*-
"""
银行对账单服务模块
==================

提供银行对账单处理的主要服务接口。
"""

import logging
import pandas as pd
from typing import Optional
from pathlib import Path
from functools import lru_cache

from .models import ExtractedData

class ExtractionService:
    """银行对账单提取服务"""
    
    def __init__(self):
        """初始化提取服务"""
        self.logger = logging.getLogger('extraction_service')
        self._extractors = []
        self._load_extractors()
    
    def _load_extractors(self):
        """加载所有可用的提取器"""
        from .extractors import ALL_EXTRACTORS
        
        for extractor_class in ALL_EXTRACTORS:
            try:
                extractor_instance = extractor_class()
                self._extractors.append(extractor_instance)
                self.logger.info(f"加载提取器: {extractor_instance.get_bank_name()}")
            except Exception as e:
                self.logger.error(f"加载提取器失败 {extractor_class}: {e}")
    
    def extract(self, file_path: str) -> ExtractedData:
        """从文件中提取银行对账单数据
        
        Args:
            file_path: 文件路径
            
        Returns:
            ExtractedData: 提取的标准化数据
            
        Raises:
            ValueError: 未找到合适的提取器时抛出
            FileNotFoundError: 文件不存在时抛出
            Exception: 文件读取失败或数据提取失败时抛出
        """
        # 步骤1: 验证文件并读取数据
        df_raw = self._read_file_to_dataframe(file_path)

        # 步骤2: 查找合适的提取器
        extractor = self._find_suitable_extractor(df_raw, file_path)
        if not extractor:
            raise ValueError('未找到适用于该文件的提取器')

        # 步骤3: 使用提取器的extract方法进行完整提取
        return extractor.extract(df_raw)
    
    def _read_file_to_dataframe(self, file_path: str) -> pd.DataFrame:
        """读取文件为DataFrame
        
        Args:
            file_path: 文件路径
            
        Returns:
            pd.DataFrame: 原始DataFrame
            
        Raises:
            FileNotFoundError: 文件不存在时抛出
            ValueError: 文件读取失败时抛出
        """
        if not Path(file_path).exists():
            raise FileNotFoundError(f'文件不存在: {file_path}')
        
        try:
            return pd.read_excel(file_path, header=None)
        except Exception as e:
            self.logger.error(f"读取文件失败 {file_path}: {e}")
            raise ValueError(f'无法读取文件 {file_path}: {str(e)}')
    
    def _find_suitable_extractor(self, df_raw: pd.DataFrame, file_path: str):
        """查找合适的提取器
        
        Args:
            df_raw: 原始DataFrame
            file_path: 文件路径（用于日志）
            
        Returns:
            提取器实例或None
        """
        for extractor in self._extractors:
            try:
                if extractor.is_applicable(df_raw):
                    self.logger.info(f"为文件 {file_path} 选择了提取器: {extractor.get_bank_name()}")
                    return extractor
            except Exception as e:
                # 如果提取器检查失败，继续尝试下一个
                self.logger.debug(f"提取器 {extractor.get_bank_name()} 检查数据时出错: {e}")
                continue
        
        self.logger.warning(f"未找到适用于文件 {file_path} 的提取器")
        return None

@lru_cache(maxsize=1)
def get_extraction_service() -> ExtractionService:
    """获取提取服务实例
    
    Returns:
        ExtractionService: 提取服务实例
    """
    return ExtractionService()