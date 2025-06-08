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

from app.models import Bank, Account, Transaction, TransactionType, db
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
                'record_count': 0,
                'file_path': file_path
            }