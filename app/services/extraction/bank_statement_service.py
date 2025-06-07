# -*- coding: utf-8 -*-
"""
银行对账单服务模块
==================

提供银行对账单处理的主要服务接口。
"""

import logging
from typing import List, Dict, Any

from .extractor_factory import ExtractorFactory

class BankStatementExtractor:
    """提取器服务"""
    
    def __init__(self):
        self.factory = ExtractorFactory()
        self.logger = logging.getLogger('extractor_service')
    
    def process_files(self, file_paths: List[str]) -> List[Dict[str, Any]]:
        """批量处理文件
        
        Args:
            file_paths: 文件路径列表
            
        Returns:
            list: 处理结果列表
        """
        results = []
        
        for file_path in file_paths:
            try:
                # 查找合适的提取器
                extractor = self.factory.find_suitable_extractor(file_path)
                
                if extractor:
                    result = extractor.process_file(file_path)
                    results.append(result)
                else:
                    results.append({
                        'success': False,
                        'error': '未找到合适的提取器',
                        'bank': '未知',
                        'record_count': 0,
                        'file_path': file_path
                    })
                    
            except Exception as e:
                self.logger.error(f"处理文件失败 {file_path}: {e}")
                results.append({
                    'success': False,
                    'error': str(e),
                    'bank': '未知',
                    'record_count': 0,
                    'file_path': file_path
                })
        
        return results
    
    def get_supported_banks(self) -> List[Dict[str, str]]:
        """获取支持的银行列表"""
        banks = []
        for bank_code in self.factory.get_available_banks():
            extractor = self.factory.create(bank_code)
            if extractor:
                banks.append({
                    'code': extractor.get_bank_code(),
                    'name': extractor.get_bank_name(),
                    'keyword': extractor.get_bank_keyword()
                })
        return banks

# 全局实例
_extractor_service = None

def get_extractor_service() -> BankStatementExtractor:
    """获取提取器服务实例"""
    global _extractor_service
    if _extractor_service is None:
        _extractor_service = BankStatementExtractor()
    return _extractor_service