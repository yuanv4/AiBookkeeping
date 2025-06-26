# -*- coding: utf-8 -*-
"""
银行对账单服务模块
==================

提供银行对账单处理的主要服务接口。
"""

import logging
import pandas as pd
from typing import List, Dict, Any, Optional
from pathlib import Path
from functools import lru_cache

from .factory import ExtractorFactory
from .models import ExtractionResult, ExtractedData

class BankStatementExtractor:
    """提取器服务"""
    
    def __init__(self, factory: ExtractorFactory = None):
        """初始化提取器服务
        
        Args:
            factory: 提取器工厂实例，如果为None则创建默认工厂
        """
        self.factory = factory or ExtractorFactory()
        self.logger = logging.getLogger('extractor_service')
    
    def extract_data_from_file(self, file_path: str) -> ExtractedData:
        """从文件中提取数据
        
        Args:
            file_path: 文件路径
            
        Returns:
            ExtractedData: 提取的数据
            
        Raises:
            Exception: 提取失败时抛出异常
        """
        # 步骤1: 验证文件并读取数据
        df_raw = self._read_file_to_dataframe(file_path)
        if df_raw is None:
            raise Exception('文件不存在或无法读取')

        # 步骤2: 查找合适的提取器
        extractor = self._find_extractor(df_raw, file_path)
        if not extractor:
            raise Exception('未找到合适的提取器')

        # 步骤3: 提取数据
        extraction_data = self._extract_data(df_raw, extractor, file_path)
        if not extraction_data['success']:
            raise Exception(extraction_data['error'])

        # 步骤4: 转换交易数据为字典列表
        transactions_df = extraction_data['transactions_df']
        transactions_list = []
        
        for _, row in transactions_df.iterrows():
            transaction_dict = {
                'date': row['date'].date() if hasattr(row['date'], 'date') else row['date'],
                'amount': row['amount'],
                'balance_after': row['balance_after'],
                'currency': row['currency'],
                'description': row['description'],
                'counterparty': row['counterparty'],
            }
            transactions_list.append(transaction_dict)
        
        # 返回标准化的提取数据
        return ExtractedData(
            bank_name=extractor.get_bank_name(),
            bank_code=extractor.get_bank_code(),
            account_name=extraction_data['account_name'],
            account_number=extraction_data['account_number'],
            transactions=transactions_list
        )
    
    def _read_file_to_dataframe(self, file_path: str) -> Optional[pd.DataFrame]:
        """读取文件为DataFrame
        
        Args:
            file_path: 文件路径
            
        Returns:
            Optional[pd.DataFrame]: 原始DataFrame或None（读取失败）
        """
        try:
            if not Path(file_path).exists():
                return None
            return pd.read_excel(file_path, header=None)
        except Exception as e:
            self.logger.error(f"读取文件失败 {file_path}: {e}")
            return None
    
    def _find_extractor(self, df_raw: pd.DataFrame, file_path: str) -> Optional['BaseTransactionExtractor']:
        """查找合适的提取器
        
        Args:
            df_raw: 原始DataFrame
            file_path: 文件路径（用于日志）
            
        Returns:
            Optional[BaseTransactionExtractor]: 提取器实例或None
        """
        extractor = self.factory.find_suitable_extractor(df_raw)
        if extractor:
            self.logger.info(f"为文件 {file_path} 选择了提取器: {extractor.get_bank_name()}")
        return extractor
    
    def _extract_data(self, df_raw: pd.DataFrame, extractor, file_path: str) -> Dict[str, Any]:
        """提取数据
        
        Args:
            df_raw: 原始DataFrame
            extractor: 提取器实例
            file_path: 文件路径（用于日志）
            
        Returns:
            Dict: 包含提取结果的字典
        """
        try:
            # 提取交易数据
            transactions_df = extractor.extract_transactions(df_raw)
            if transactions_df is None or transactions_df.empty:
                return {
                    'success': False,
                    'error': '无法提取交易数据'
                }

            # 提取账户信息
            account_name, account_number = extractor.extract_account_info(df_raw)
            if not account_name or not account_number:
                return {
                    'success': False,
                    'error': '无法提取账户信息'
                }

            return {
                'success': True,
                'transactions_df': transactions_df,
                'account_name': account_name,
                'account_number': account_number
            }
            
        except Exception as e:
            self.logger.error(f"数据提取失败 {file_path}: {e}")
            return {
                'success': False,
                'error': f'数据提取失败: {str(e)}'
            }
    

    
    def validate_files(self, file_paths: List[str]) -> List[ExtractionResult]:
        """验证文件列表
        
        Args:
            file_paths: 文件路径列表
            
        Returns:
            List[ExtractionResult]: 验证结果列表
        """
        results = []
        for file_path in file_paths:
            try:
                # 读取文件数据
                df_raw = self._read_file_to_dataframe(file_path)
                if df_raw is None:
                    results.append(ExtractionResult.error_result('文件不存在或无法读取', file_path=file_path))
                    continue

                # 查找合适的提取器
                extractor = self.factory.find_suitable_extractor(df_raw)
                if extractor:
                    results.append(ExtractionResult.success_result(
                        bank=extractor.get_bank_name(),
                        record_count=0,  # 验证阶段不处理记录
                        file_path=file_path,
                        data={'detected_bank': {
                            'code': extractor.get_bank_code(),
                            'name': extractor.get_bank_name()
                        }}
                    ))
                else:
                    # 提供可能的银行建议
                    suggested_banks = []
                    for bank_code in self.factory.get_available_banks()[:3]:
                        extractor_instance = self.factory.create(bank_code)
                        if extractor_instance:
                            suggested_banks.append({
                                'code': bank_code,
                                'name': extractor_instance.get_bank_name()
                            })
                    
                    results.append(ExtractionResult.error_result(
                        '未找到合适的提取器',
                        file_path=file_path,
                        data={'suggested_banks': suggested_banks}
                    ))

            except Exception as e:
                self.logger.error(f"文件验证失败 {file_path}: {e}")
                results.append(ExtractionResult.error_result(str(e), file_path=file_path))

        return results

@lru_cache(maxsize=1)
def get_extractor_service() -> BankStatementExtractor:
    """获取提取器服务实例
    
    Returns:
        BankStatementExtractor: 提取器服务实例
    """
    # 创建提取器工厂
    factory = ExtractorFactory()
    
    # 返回不带数据库依赖的提取器服务
    return BankStatementExtractor(factory=factory)