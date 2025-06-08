# -*- coding: utf-8 -*-
"""
银行对账单服务模块
==================

提供银行对账单处理的主要服务接口。
"""

import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from .extraction_factory import ExtractorFactory

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
    
    def process_single_file(self, file_path: str, bank_hint: Optional[str] = None) -> Dict[str, Any]:
        """处理单个文件。
        
        Args:
            file_path: 文件路径
            bank_hint: 银行提示（可选，用于优化提取器选择）
            
        Returns:
            Dict[str, Any]: 处理结果
        """
        try:
            # 如果提供了银行提示，优先使用指定的提取器
            if bank_hint:
                extractor = self.factory.create(bank_hint)
                if extractor:
                    return extractor.process_file(file_path)
            
            # 否则使用自动检测
            extractor = self.factory.find_suitable_extractor(file_path)
            
            if extractor:
                return extractor.process_file(file_path)
            else:
                return {
                    'success': False,
                    'error': '未找到合适的提取器',
                    'bank': bank_hint or '未知',
                    'record_count': 0,
                    'file_path': file_path
                }
                
        except Exception as e:
            self.logger.error(f"处理单个文件失败 {file_path}: {e}")
            return {
                'success': False,
                'error': str(e),
                'bank': bank_hint or '未知',
                'record_count': 0,
                'file_path': file_path
            }
    
    def validate_file_compatibility(self, file_path: str) -> Dict[str, Any]:
        """验证文件兼容性。
        
        Args:
            file_path: 文件路径
            
        Returns:
            Dict[str, Any]: 兼容性验证结果
        """
        try:
            # 检查文件是否存在
            if not Path(file_path).exists():
                return {
                    'compatible': False,
                    'reason': '文件不存在',
                    'suggested_banks': []
                }
            
            # 查找合适的提取器
            extractor = self.factory.find_suitable_extractor(file_path)
            
            if extractor:
                return {
                    'compatible': True,
                    'detected_bank': {
                        'code': extractor.get_bank_code(),
                        'name': extractor.get_bank_name()
                    },
                    'confidence': 'high'
                }
            else:
                # 提供可能的银行建议
                suggested_banks = [{
                    'code': bank_code,
                    'name': self.factory.create(bank_code).get_bank_name()
                } for bank_code in self.factory.get_available_banks()[:3]]  # 前3个作为建议
                
                return {
                    'compatible': False,
                    'reason': '未找到合适的提取器',
                    'suggested_banks': suggested_banks
                }
                
        except Exception as e:
            self.logger.error(f"文件兼容性验证失败 {file_path}: {e}")
            return {
                'compatible': False,
                'reason': f'验证过程出错: {str(e)}',
                'suggested_banks': []
            }
    
    def validate_files(self, file_paths: List[str]) -> List[str]:
        """验证文件列表，返回存在的文件。
        
        Args:
            file_paths: 文件路径列表
            
        Returns:
            List[str]: 存在的文件路径列表
        """
        valid_files = []
        for file_path in file_paths:
            if Path(file_path).exists():
                valid_files.append(file_path)
            else:
                self.logger.warning(f"文件不存在，跳过: {file_path}")
        return valid_files

# 全局实例
_extractor_service = None

def get_extractor_service() -> BankStatementExtractor:
    """获取提取器服务实例"""
    global _extractor_service
    if _extractor_service is None:
        _extractor_service = BankStatementExtractor()
    return _extractor_service