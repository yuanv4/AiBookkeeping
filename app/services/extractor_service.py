# -*- coding: utf-8 -*-
"""
提取器服务模块
==============

负责从不同银行的Excel文件中提取交易数据的服务层实现。
"""

import os
import sys
import importlib
import inspect
import logging
import pandas as pd
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Type, Optional, Any, Union, Tuple
from abc import ABC, abstractmethod

from app.models import Bank, Account, Transaction, TransactionType, db
from app.services.database_service import DatabaseService
from app.services.transaction_service import TransactionService

logger = logging.getLogger(__name__)

class ExtractorInterface(ABC):
    """银行交易提取器接口"""

    @abstractmethod
    def get_bank_code(self) -> str:
        """获取银行代码，如CMB、CCB等"""
        pass

    @abstractmethod
    def get_bank_name(self) -> str:
        """获取银行名称，如招商银行、建设银行等"""
        pass

    @abstractmethod
    def get_bank_keyword(self) -> str:
        """获取银行关键词，用于文件匹配"""
        pass

    @abstractmethod
    def can_process_file(self, file_path: str) -> bool:
        """判断是否可以处理指定文件"""
        pass

    @abstractmethod
    def extract_account_info(self, df: pd.DataFrame) -> Tuple[str, str]:
        """提取账户信息
        
        Args:
            df: 包含账户信息的DataFrame
            
        Returns:
            tuple: (account_name, account_number)
        """
        pass

    @abstractmethod
    def extract_transactions(self, file_path: str) -> Optional[pd.DataFrame]:
        """提取交易数据
        
        Args:
            file_path: Excel文件路径
            
        Returns:
            DataFrame: 标准格式的交易数据或None（提取失败）
        """
        pass

class BaseTransactionExtractor(ExtractorInterface):
    """银行交易明细提取器基类"""
    
    def __init__(self, bank_code: str):
        """初始化提取器
        
        Args:
            bank_code: 银行代码，如CMB、CCB等
        """
        self.bank_code = bank_code
        self.logger = logging.getLogger(f'extractor_{bank_code.lower()}')
        self.database_service = DatabaseService()
        self.transaction_service = TransactionService()
        
    def _standardize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """标准化DataFrame格式
        
        Args:
            df: 原始DataFrame
            
        Returns:
            DataFrame: 标准化后的DataFrame
        """
        # 标准化列名
        standard_columns = {
            'transaction_date': '交易日期',
            'amount': '金额',
            'balance': '余额',
            'counterparty': '对方户名',
            'description': '摘要',
            'transaction_type': '交易类型',
            'currency': '币种'
        }
        
        # 重命名列
        for std_col, orig_col in standard_columns.items():
            if orig_col in df.columns:
                df = df.rename(columns={orig_col: std_col})
        
        # 确保必要列存在
        required_columns = ['transaction_date', 'amount', 'counterparty', 'description']
        for col in required_columns:
            if col not in df.columns:
                df[col] = None
                
        # 数据类型转换
        if 'transaction_date' in df.columns:
            df['transaction_date'] = pd.to_datetime(df['transaction_date'], errors='coerce')
        
        if 'amount' in df.columns:
            df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
            
        if 'balance' in df.columns:
            df['balance'] = pd.to_numeric(df['balance'], errors='coerce')
        
        return df
    
    def _determine_transaction_type(self, amount: float, description: str = '') -> str:
        """根据金额和描述确定交易类型
        
        Args:
            amount: 交易金额
            description: 交易描述
            
        Returns:
            str: 交易类型
        """
        if amount > 0:
            return '收入'
        else:
            return '支出'
    
    def process_file(self, file_path: str) -> Dict[str, Any]:
        """处理单个文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            dict: 处理结果
        """
        try:
            if not self.can_process_file(file_path):
                return {
                    'success': False,
                    'error': f'文件不支持: {file_path}',
                    'bank': self.get_bank_name(),
                    'record_count': 0
                }
            
            # 提取交易数据
            df = self.extract_transactions(file_path)
            if df is None or df.empty:
                return {
                    'success': False,
                    'error': '无法提取交易数据',
                    'bank': self.get_bank_name(),
                    'record_count': 0
                }
            
            # 标准化数据
            df = self._standardize_dataframe(df)
            
            # 提取账户信息
            account_name, account_number = self.extract_account_info(df)
            
            # 确保银行存在
            bank = self.database_service.get_or_create_bank(
                code=self.get_bank_code(),
                name=self.get_bank_name()
            )
            
            # 确保账户存在
            account = self.database_service.get_or_create_account(
                account_number=account_number,
                account_name=account_name,
                bank_id=bank.id
            )
            
            # 处理交易记录
            processed_count = 0
            for _, row in df.iterrows():
                try:
                    # 跳过无效记录
                    if pd.isna(row.get('transaction_date')) or pd.isna(row.get('amount')):
                        continue
                    
                    # 确定交易类型
                    type_name = self._determine_transaction_type(
                        row['amount'], 
                        row.get('description', '')
                    )
                    transaction_type = self.database_service.get_or_create_transaction_type(type_name)
                    
                    # 创建交易记录
                    transaction_data = {
                        'account_id': account.id,
                        'transaction_type_id': transaction_type.id,
                        'amount': abs(row['amount']),  # 存储绝对值
                        'transaction_date': row['transaction_date'].date(),
                        'counterparty': row.get('counterparty', ''),
                        'description': row.get('description', ''),
                        'balance': row.get('balance'),
                        'currency': row.get('currency', 'CNY')
                    }
                    
                    # 检查是否已存在相同交易
                    existing = self.transaction_service.find_duplicate_transaction(
                        account_id=account.id,
                        amount=transaction_data['amount'],
                        transaction_date=transaction_data['transaction_date'],
                        counterparty=transaction_data['counterparty']
                    )
                    
                    if not existing:
                        self.transaction_service.create_transaction(**transaction_data)
                        processed_count += 1
                    
                except Exception as e:
                    self.logger.warning(f"处理交易记录失败: {e}")
                    continue
            
            return {
                'success': True,
                'bank': self.get_bank_name(),
                'account_number': account_number,
                'account_name': account_name,
                'record_count': processed_count,
                'file_path': file_path
            }
            
        except Exception as e:
            self.logger.error(f"处理文件失败 {file_path}: {e}")
            return {
                'success': False,
                'error': str(e),
                'bank': self.get_bank_name(),
                'record_count': 0
            }

class CMBTransactionExtractor(BaseTransactionExtractor):
    """招商银行交易提取器"""
    
    def __init__(self):
        super().__init__('CMB')
    
    def get_bank_code(self) -> str:
        return 'CMB'
    
    def get_bank_name(self) -> str:
        return '招商银行'
    
    def get_bank_keyword(self) -> str:
        return '招商银行'
    
    def can_process_file(self, file_path: str) -> bool:
        """判断是否可以处理指定文件"""
        try:
            # 检查文件名是否包含招商银行关键词
            filename = os.path.basename(file_path).lower()
            keywords = ['招商', 'cmb', '一卡通']
            
            if not any(keyword in filename for keyword in keywords):
                return False
            
            # 尝试读取文件检查格式
            df = pd.read_excel(file_path, nrows=10)
            
            # 检查是否包含招商银行特有的列
            cmb_columns = ['交易日期', '交易时间', '对方户名', '对方账号', '交易金额', '余额']
            return any(col in df.columns for col in cmb_columns)
            
        except Exception:
            return False
    
    def extract_account_info(self, df: pd.DataFrame) -> Tuple[str, str]:
        """提取账户信息"""
        # 招商银行通常在前几行包含账户信息
        account_name = '招商银行账户'
        account_number = 'CMB_UNKNOWN'
        
        try:
            # 尝试从DataFrame的前几行提取账户信息
            for i in range(min(10, len(df))):
                for col in df.columns:
                    cell_value = str(df.iloc[i][col])
                    
                    # 查找账号模式
                    if '账号' in cell_value or '卡号' in cell_value:
                        # 提取数字
                        numbers = re.findall(r'\d{10,}', cell_value)
                        if numbers:
                            account_number = numbers[0]
                    
                    # 查找户名
                    if '户名' in cell_value or '姓名' in cell_value:
                        parts = cell_value.split()
                        if len(parts) > 1:
                            account_name = parts[1]
        
        except Exception as e:
            self.logger.warning(f"提取账户信息失败: {e}")
        
        return account_name, account_number
    
    def extract_transactions(self, file_path: str) -> Optional[pd.DataFrame]:
        """提取交易数据"""
        try:
            # 读取Excel文件
            df = pd.read_excel(file_path)
            
            # 查找数据开始行
            data_start_row = 0
            for i, row in df.iterrows():
                if '交易日期' in str(row.values):
                    data_start_row = i
                    break
            
            # 重新读取，跳过前面的行
            if data_start_row > 0:
                df = pd.read_excel(file_path, skiprows=data_start_row)
            
            # 清理列名
            df.columns = df.columns.str.strip()
            
            # 过滤有效数据行
            df = df.dropna(subset=['交易日期'], how='all')
            
            # 重命名列以匹配标准格式
            column_mapping = {
                '交易日期': 'transaction_date',
                '交易金额': 'amount',
                '余额': 'balance',
                '对方户名': 'counterparty',
                '摘要': 'description',
                '备注': 'description'
            }
            
            df = df.rename(columns=column_mapping)
            
            return df
            
        except Exception as e:
            self.logger.error(f"提取招商银行交易数据失败: {e}")
            return None

class CCBTransactionExtractor(BaseTransactionExtractor):
    """建设银行交易提取器"""
    
    def __init__(self):
        super().__init__('CCB')
    
    def get_bank_code(self) -> str:
        return 'CCB'
    
    def get_bank_name(self) -> str:
        return '建设银行'
    
    def get_bank_keyword(self) -> str:
        return '建设银行'
    
    def can_process_file(self, file_path: str) -> bool:
        """判断是否可以处理指定文件"""
        try:
            # 检查文件名是否包含建设银行关键词
            filename = os.path.basename(file_path).lower()
            keywords = ['建设', 'ccb', '龙卡']
            
            if not any(keyword in filename for keyword in keywords):
                return False
            
            # 尝试读取文件检查格式
            df = pd.read_excel(file_path, nrows=10)
            
            # 检查是否包含建设银行特有的列
            ccb_columns = ['交易日期', '交易时间', '对方户名', '交易金额', '账户余额']
            return any(col in df.columns for col in ccb_columns)
            
        except Exception:
            return False
    
    def extract_account_info(self, df: pd.DataFrame) -> Tuple[str, str]:
        """提取账户信息"""
        account_name = '建设银行账户'
        account_number = 'CCB_UNKNOWN'
        
        try:
            # 建设银行账户信息提取逻辑
            for i in range(min(10, len(df))):
                for col in df.columns:
                    cell_value = str(df.iloc[i][col])
                    
                    # 查找账号模式
                    if '账号' in cell_value or '卡号' in cell_value:
                        numbers = re.findall(r'\d{10,}', cell_value)
                        if numbers:
                            account_number = numbers[0]
                    
                    # 查找户名
                    if '户名' in cell_value or '姓名' in cell_value:
                        parts = cell_value.split()
                        if len(parts) > 1:
                            account_name = parts[1]
        
        except Exception as e:
            self.logger.warning(f"提取账户信息失败: {e}")
        
        return account_name, account_number
    
    def extract_transactions(self, file_path: str) -> Optional[pd.DataFrame]:
        """提取交易数据"""
        try:
            # 读取Excel文件
            df = pd.read_excel(file_path)
            
            # 查找数据开始行
            data_start_row = 0
            for i, row in df.iterrows():
                if '交易日期' in str(row.values):
                    data_start_row = i
                    break
            
            # 重新读取，跳过前面的行
            if data_start_row > 0:
                df = pd.read_excel(file_path, skiprows=data_start_row)
            
            # 清理列名
            df.columns = df.columns.str.strip()
            
            # 过滤有效数据行
            df = df.dropna(subset=['交易日期'], how='all')
            
            # 重命名列以匹配标准格式
            column_mapping = {
                '交易日期': 'transaction_date',
                '交易金额': 'amount',
                '账户余额': 'balance',
                '对方户名': 'counterparty',
                '摘要': 'description',
                '备注': 'description'
            }
            
            df = df.rename(columns=column_mapping)
            
            return df
            
        except Exception as e:
            self.logger.error(f"提取建设银行交易数据失败: {e}")
            return None

class ExtractorFactory:
    """银行提取器工厂"""
    
    def __init__(self):
        self.extractors: Dict[str, Type[ExtractorInterface]] = {}
        self.logger = logging.getLogger('extractor_factory')
        self._register_default_extractors()
    
    def _register_default_extractors(self):
        """注册默认提取器"""
        self.register('CMB', CMBTransactionExtractor)
        self.register('CCB', CCBTransactionExtractor)
    
    def register(self, bank_code: str, extractor_class: Type[ExtractorInterface]):
        """注册银行提取器"""
        self.extractors[bank_code] = extractor_class
        self.logger.info(f"注册提取器: {bank_code} -> {extractor_class.__name__}")
    
    def create(self, bank_code: str) -> Optional[ExtractorInterface]:
        """创建指定银行的提取器实例"""
        if bank_code in self.extractors:
            return self.extractors[bank_code]()
        return None
    
    def get_available_banks(self) -> List[str]:
        """获取可用的银行代码列表"""
        return list(self.extractors.keys())
    
    def find_suitable_extractor(self, file_path: str) -> Optional[ExtractorInterface]:
        """根据文件找到合适的提取器"""
        for bank_code in self.extractors:
            extractor = self.create(bank_code)
            if extractor and extractor.can_process_file(file_path):
                return extractor
        return None

class ExtractorService:
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

def get_extractor_service() -> ExtractorService:
    """获取提取器服务实例"""
    global _extractor_service
    if _extractor_service is None:
        _extractor_service = ExtractorService()
    return _extractor_service