# -*- coding: utf-8 -*-
"""
综合提取服务模块
================

提供银行对账单提取的综合门面服务。
参考分析服务的门面模式，为提取功能提供统一的接口。
"""

from typing import List, Dict, Any, Optional, Tuple
import logging
from datetime import datetime
from pathlib import Path

from .extractor_factory import ExtractorFactory
from .extractors.base_extractor import BankStatementExtractorInterface
from app.utils.performance_monitor import monitor_performance
from app.utils.cache_manager import optimized_cache

logger = logging.getLogger(__name__)


class ComprehensiveExtractionService:
    """综合提取服务门面类。
    
    提供统一的接口来管理所有银行对账单提取相关的功能，
    包括文件处理、银行管理、结果格式化等。
    """
    
    def __init__(self):
        """初始化综合提取服务。"""
        self._factory = ExtractorFactory()
        self._logger = logging.getLogger('comprehensive_extraction_service')
    
    @monitor_performance("batch_file_processing")
    def process_files_batch(self, file_paths: List[str], 
                           validate_files: bool = True,
                           include_metadata: bool = True) -> Dict[str, Any]:
        """批量处理文件的增强版本。
        
        Args:
            file_paths: 文件路径列表
            validate_files: 是否验证文件存在性
            include_metadata: 是否包含处理元数据
            
        Returns:
            Dict[str, Any]: 包含处理结果和统计信息的字典
        """
        try:
            # 文件验证
            if validate_files:
                file_paths = self._validate_files(file_paths)
            
            # 处理文件
            results = []
            processing_stats = {
                'total_files': len(file_paths),
                'successful': 0,
                'failed': 0,
                'start_time': datetime.now(),
                'banks_detected': set()
            }
            
            for file_path in file_paths:
                result = self._process_single_file(file_path)
                results.append(result)
                
                # 更新统计信息
                if result.get('success', False):
                    processing_stats['successful'] += 1
                    processing_stats['banks_detected'].add(result.get('bank', '未知'))
                else:
                    processing_stats['failed'] += 1
            
            processing_stats['end_time'] = datetime.now()
            processing_stats['duration'] = (
                processing_stats['end_time'] - processing_stats['start_time']
            ).total_seconds()
            processing_stats['banks_detected'] = list(processing_stats['banks_detected'])
            
            response = {
                'results': results,
                'success': True
            }
            
            if include_metadata:
                response['metadata'] = processing_stats
            
            return response
            
        except Exception as e:
            self._logger.error(f"批量文件处理失败: {e}")
            return {
                'results': [],
                'success': False,
                'error': str(e),
                'metadata': {'total_files': len(file_paths), 'successful': 0, 'failed': len(file_paths)}
            }
    
    def process_single_file(self, file_path: str, 
                           bank_hint: Optional[str] = None) -> Dict[str, Any]:
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
                extractor = self._factory.create(bank_hint)
                if extractor:
                    return extractor.process_file(file_path)
            
            # 否则使用自动检测
            return self._process_single_file(file_path)
            
        except Exception as e:
            self._logger.error(f"处理单个文件失败 {file_path}: {e}")
            return {
                'success': False,
                'error': str(e),
                'bank': bank_hint or '未知',
                'record_count': 0,
                'file_path': file_path
            }
    
    @optimized_cache('supported_banks_info', expire_minutes=60, priority=3)
    def get_supported_banks_info(self, include_capabilities: bool = False) -> Dict[str, Any]:
        """获取支持的银行详细信息。
        
        Args:
            include_capabilities: 是否包含提取器能力信息
            
        Returns:
            Dict[str, Any]: 银行信息字典
        """
        try:
            banks_info = {
                'banks': [],
                'total_count': 0,
                'last_updated': datetime.now().isoformat()
            }
            
            for bank_code in self._factory.get_available_banks():
                extractor = self._factory.create(bank_code)
                if extractor:
                    bank_info = {
                        'code': extractor.get_bank_code(),
                        'name': extractor.get_bank_name(),
                        'keyword': extractor.get_bank_keyword()
                    }
                    
                    if include_capabilities:
                        bank_info['capabilities'] = self._get_extractor_capabilities(extractor)
                    
                    banks_info['banks'].append(bank_info)
            
            banks_info['total_count'] = len(banks_info['banks'])
            return banks_info
            
        except Exception as e:
            self._logger.error(f"获取银行信息失败: {e}")
            return {
                'banks': [],
                'total_count': 0,
                'error': str(e),
                'last_updated': datetime.now().isoformat()
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
            extractor = self._factory.find_suitable_extractor(file_path)
            
            if extractor:
                return {
                    'compatible': True,
                    'detected_bank': {
                        'code': extractor.get_bank_code(),
                        'name': extractor.get_bank_name()
                    },
                    'confidence': 'high'  # 可以扩展为实际的置信度计算
                }
            else:
                # 提供可能的银行建议
                suggested_banks = [{
                    'code': bank_code,
                    'name': self._factory.create(bank_code).get_bank_name()
                } for bank_code in self._factory.get_available_banks()[:3]]  # 前3个作为建议
                
                return {
                    'compatible': False,
                    'reason': '未找到合适的提取器',
                    'suggested_banks': suggested_banks
                }
                
        except Exception as e:
            self._logger.error(f"文件兼容性验证失败 {file_path}: {e}")
            return {
                'compatible': False,
                'reason': f'验证过程出错: {str(e)}',
                'suggested_banks': []
            }
    
    def get_extraction_statistics(self) -> Dict[str, Any]:
        """获取提取统计信息。
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        try:
            return {
                'available_extractors': len(self._factory.get_available_banks()),
                'supported_banks': [{
                    'code': bank_code,
                    'name': self._factory.create(bank_code).get_bank_name()
                } for bank_code in self._factory.get_available_banks()],
                'service_status': 'active',
                'last_check': datetime.now().isoformat()
            }
        except Exception as e:
            self._logger.error(f"获取统计信息失败: {e}")
            return {
                'available_extractors': 0,
                'supported_banks': [],
                'service_status': 'error',
                'error': str(e),
                'last_check': datetime.now().isoformat()
            }
    
    def _validate_files(self, file_paths: List[str]) -> List[str]:
        """验证文件列表。"""
        valid_files = []
        for file_path in file_paths:
            if Path(file_path).exists():
                valid_files.append(file_path)
            else:
                self._logger.warning(f"文件不存在，跳过: {file_path}")
        return valid_files
    
    def _process_single_file(self, file_path: str) -> Dict[str, Any]:
        """处理单个文件的内部方法。"""
        try:
            extractor = self._factory.find_suitable_extractor(file_path)
            
            if extractor:
                return extractor.process_file(file_path)
            else:
                return {
                    'success': False,
                    'error': '未找到合适的提取器',
                    'bank': '未知',
                    'record_count': 0,
                    'file_path': file_path
                }
                
        except Exception as e:
            self._logger.error(f"处理文件失败 {file_path}: {e}")
            return {
                'success': False,
                'error': str(e),
                'bank': '未知',
                'record_count': 0,
                'file_path': file_path
            }
    
    def _get_extractor_capabilities(self, extractor: BankStatementExtractorInterface) -> Dict[str, Any]:
        """获取提取器能力信息。"""
        try:
            return {
                'supports_csv': True,  # 可以扩展为实际的能力检测
                'supports_excel': True,
                'encoding_support': ['utf-8', 'gbk'],  # 示例
                'version': '1.0'  # 可以从提取器获取版本信息
            }
        except Exception:
            return {
                'supports_csv': True,
                'supports_excel': False,
                'encoding_support': ['utf-8'],
                'version': 'unknown'
            }


# 全局实例
_comprehensive_extraction_service = None


def get_comprehensive_extraction_service() -> ComprehensiveExtractionService:
    """获取综合提取服务实例。
    
    Returns:
        ComprehensiveExtractionService: 综合提取服务实例
    """
    global _comprehensive_extraction_service
    if _comprehensive_extraction_service is None:
        _comprehensive_extraction_service = ComprehensiveExtractionService()
    return _comprehensive_extraction_service