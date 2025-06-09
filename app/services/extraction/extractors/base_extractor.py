# -*- coding: utf-8 -*-
"""
基础提取器模块
==============

定义银行对账单提取器的接口和基础实现。
"""

import logging
import pandas as pd
import re
from datetime import datetime
from typing import Dict, List, Type, Optional, Any, Union, Tuple
from abc import ABC, abstractmethod

from app.models import Bank, Account, Transaction, TransactionTypeEnum, db
from app.services.core.database_service import DatabaseService
from app.services.core.transaction_service import TransactionService

logger = logging.getLogger(__name__)

class BankStatementExtractorInterface(ABC):
    """银行对账单提取器接口"""

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

    def extract_account_info(self, df: pd.DataFrame) -> Tuple[str, str]:
        """模板方法：提取账户信息
        
        Args:
            df: 包含账户信息的DataFrame
            
        Returns:
            tuple: (account_name, account_number)
        """
        account_name = None
        account_number = None
        
        try:
            # 遍历前10行查找账户信息
            for i in range(min(10, len(df))):
                for j in range(len(df.columns)):
                    cell_value = str(df.iloc[i, j])
                    
                    # 使用子类定义的匹配规则
                    if account_name is None:
                        account_name = self._extract_account_name(cell_value)
                    
                    if account_number is None:
                        account_number = self._extract_account_number(cell_value)
                    
                    # 如果都找到了就可以提前退出
                    if account_name and account_number:
                        break
                
                if account_name and account_number:
                    break
            
            # 记录提取结果
            self.logger.info(f"账户信息提取结果 - 户名: {account_name}, 账号: {account_number}")
            
            # 验证结果
            if account_name and account_number:
                return account_name, account_number
            else:
                return None, None
        
        except Exception as e:
            self.logger.warning(f"提取账户信息失败: {e}")
            return None, None
    
    @abstractmethod
    def _extract_account_name(self, cell_value: str) -> Optional[str]:
        """从单元格值中提取账户名称
        
        Args:
            cell_value: 单元格字符串值
            
        Returns:
            str: 提取到的账户名称，未找到返回None
        """
        pass
    
    @abstractmethod
    def _extract_account_number(self, cell_value: str) -> Optional[str]:
        """从单元格值中提取账户号码
        
        Args:
            cell_value: 单元格字符串值
            
        Returns:
            str: 提取到的账户号码，未找到返回None
        """
        pass

    def extract_transactions(self, file_path: str) -> Optional[pd.DataFrame]:
        """提取交易数据 - 模板方法
        
        Args:
            file_path: Excel文件路径
            
        Returns:
            DataFrame: 标准格式的交易数据或None（提取失败）
        """
        try:
            # 调用子类实现的具体提取逻辑
            df = self._extract_transactions_impl(file_path)
            
            if df is not None and len(df) > 0:
                self.logger.info(f"成功提取{len(df)}条交易记录")
                return df
            else:
                self.logger.warning("未提取到任何交易记录")
                return None
                
        except Exception as e:
            self.logger.error(f"提取交易数据失败: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return None
    
    @abstractmethod
    def _extract_transactions_impl(self, file_path: str) -> Optional[pd.DataFrame]:
        """提取交易数据的具体实现 - 由子类实现
        
        Args:
            file_path: Excel文件路径
            
        Returns:
            DataFrame: 标准格式的交易数据或None（提取失败）
        """
        pass

class BaseTransactionExtractor(BankStatementExtractorInterface):
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
            'balance_after': '余额',
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
            df['transaction_date'] = pd.to_datetime(df['transaction_date'].astype(str), format='%Y%m%d', errors='coerce')
        
        if 'amount' in df.columns:
            # 清理amount列中的逗号和其他非数字字符
            df['amount'] = df['amount'].astype(str).str.replace(',', '').str.replace('，', '')
            df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
            
        if 'balance_after' in df.columns:
            # 清理balance_after列中的逗号和其他非数字字符
            df['balance_after'] = df['balance_after'].astype(str).str.replace(',', '').str.replace('，', '')
            df['balance_after'] = pd.to_numeric(df['balance_after'], errors='coerce')
        
        return df
    
    def process_file(self, file_path: str, account_name: str = None, account_number: str = None) -> Dict[str, Any]:
        """处理单个文件
        
        Args:
            file_path: 文件路径
            account_name: 账户名称（可选，如果提供则不重复提取）
            account_number: 账户号码（可选，如果提供则不重复提取）
            
        Returns:
            dict: 处理结果
        """ 
        try:
            # 提取交易数据
            df = self.extract_transactions(file_path)
            if df is None or df.empty:
                return {
                    'success': False,
                    'error': '无法提取交易数据',
                    'bank': self.get_bank_name(),
                    'record_count': 0,
                    'file_path': file_path
                }
            
            # 标准化数据
            df = self._standardize_dataframe(df)
            
            # 如果没有提供账户信息，则从原始文件提取
            if not account_name or not account_number:
                # 使用原始文件数据提取账户信息
                raw_df = pd.read_excel(file_path, header=None)
                account_name, account_number = self.extract_account_info(raw_df)
            
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
                    # 确定交易类型
                    if row['amount'] > 0:
                        transaction_type = TransactionTypeEnum.OTHER_INCOME
                    else:
                        transaction_type = TransactionTypeEnum.OTHER_EXPENSE
                    
                    # 创建交易记录
                    transaction_data = {
                        'account_id': account.id,
                        'transaction_type': transaction_type,
                        'amount': abs(row['amount']),  # 存储绝对值
                        'date': row['transaction_date'].date(),  # 修正参数名：transaction_date -> date
                        'counterparty': row.get('counterparty', ''),
                        'description': row.get('description', ''),
                        'original_description': row.get('original_description', ''),  # 添加缺失字段
                        'notes': row.get('notes', ''),  # 添加notes字段
                        'balance_after': row.get('balance_after'),
                        'currency': row.get('currency', 'CNY')
                    }
                    
                    # 检查是否已存在相同交易（直接使用transaction_data的相关字段）
                    is_duplicate = self.transaction_service.is_duplicate_transaction(transaction_data)
                    
                    if not is_duplicate:
                        # 使用process_transaction方法，直接传入transaction_data
                        transaction, is_new = self.transaction_service.process_transaction(**transaction_data)
                        if is_new:
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
                'record_count': 0,
                'file_path': file_path
            }