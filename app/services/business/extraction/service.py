# -*- coding: utf-8 -*-
"""
银行对账单服务模块
==================

提供银行对账单处理的主要服务接口。
"""

import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from functools import lru_cache

from .factory import ExtractorFactory
from .models import ExtractionResult

class BankStatementExtractor:
    """提取器服务"""
    
    def __init__(self):
        self.factory = ExtractorFactory()
        self.logger = logging.getLogger('extractor_service')
    
    def process_file(self, file_path: str, bank_hint: Optional[str] = None) -> ExtractionResult:
        """处理单个文件
        
        Args:
            file_path: 文件路径
            bank_hint: 银行提示（可选，用于优化提取器选择）
            
        Returns:
            ExtractionResult: 处理结果
        """
        try:
            if not Path(file_path).exists():
                return ExtractionResult.error_result('文件不存在', file_path=file_path)

            # 如果提供了银行提示，优先使用指定的提取器
            if bank_hint:
                extractor = self.factory.create(bank_hint)
                if extractor:
                    result = extractor.process_file(file_path)
                    return ExtractionResult.success_result(
                        bank=extractor.get_bank_name(),
                        record_count=result.get('record_count', 0),
                        file_path=file_path,
                        data=result
                    )

            # 使用自动检测
            extractor_result = self.factory.find_suitable_extractor(file_path)
            if extractor_result:
                extractor, account_name, account_number = extractor_result
                result = extractor.process_file(file_path, account_name, account_number)
                return ExtractionResult.success_result(
                    bank=extractor.get_bank_name(),
                    record_count=result.get('record_count', 0),
                    file_path=file_path,
                    data=result
                )

            return ExtractionResult.error_result('未找到合适的提取器', file_path=file_path)

        except Exception as e:
            self.logger.error(f"处理文件失败 {file_path}: {e}")
            return ExtractionResult.error_result(str(e), bank_hint or '未知', file_path)
    
    def process_files(self, file_paths: List[str]) -> List[ExtractionResult]:
        """批量处理文件
        
        Args:
            file_paths: 文件路径列表
            
        Returns:
            List[ExtractionResult]: 处理结果列表
        """
        return [self.process_file(file_path) for file_path in file_paths]
    
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
                if not Path(file_path).exists():
                    results.append(ExtractionResult.error_result('文件不存在', file_path=file_path))
                    continue

                extractor_result = self.factory.find_suitable_extractor(file_path)
                if extractor_result:
                    extractor, _, _ = extractor_result
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
                    suggested_banks = [{
                        'code': bank_code,
                        'name': self.factory.create(bank_code).get_bank_name()
                    } for bank_code in self.factory.get_available_banks()[:3]]
                    
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
    return BankStatementExtractor()