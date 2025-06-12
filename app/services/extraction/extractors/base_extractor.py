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
from dataclasses import dataclass

from app.models import Bank, Account, Transaction, db
from app.services.core.bank_service import BankService
from app.services.core.account_service import AccountService
from app.services.core.transaction_service import TransactionService

logger = logging.getLogger(__name__)

@dataclass
class AccountExtractionPattern:
    """账户信息提取模式配置"""
    keyword: str        # 关键词，如 "户    名：" 或 "客户名称:"
    regex_pattern: str  # 正则表达式模式，如 r'户    名：(.+)'

@dataclass
class BankInfo:
    """银行基本信息配置"""
    code: str          # 银行代码，如 'CMB', 'CCB'
    name: str          # 银行名称，如 '招商银行'
    keyword: str       # 银行关键词，用于文件匹配

@dataclass
class ExtractionConfig:
    """银行数据提取配置"""
    date_column_keyword: str  # 日期列关键词，如'交易日期'、'记账日期'
    column_mapping: Dict[str, str]  # 列名映射字典
    use_skiprows: bool = False  # 是否使用skiprows而不是header参数
    # 账户信息提取配置
    account_name_pattern: 'AccountExtractionPattern'  # 账户名称提取模式
    account_number_pattern: 'AccountExtractionPattern'  # 账户号码提取模式
    bank_info: Optional[BankInfo] = None

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
    
    @abstractmethod
    def get_extraction_config(self) -> ExtractionConfig:
        """获取银行特定的数据提取配置
        
        Returns:
            ExtractionConfig: 银行特定的提取配置
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
        self.transaction_service = TransactionService()
    
    def _extract_transactions_impl(self, file_path: str) -> Optional[pd.DataFrame]:
        """提取交易数据的具体实现 - 使用配置化方法
        
        Args:
            file_path: Excel文件路径
            
        Returns:
            DataFrame: 标准格式的交易数据或None（提取失败）
        """
        config = self.get_extraction_config()
        return self._extract_transactions_with_config(file_path, config)
        
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
            'currency': '币种',
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
    
    def _extract_transactions_with_config(self, file_path: str, config: ExtractionConfig) -> Optional[pd.DataFrame]:
        """使用配置提取交易数据的通用实现
        
        Args:
            file_path: Excel文件路径
            config: 银行特定的提取配置
            
        Returns:
            DataFrame: 标准格式的交易数据或None（提取失败）
        """
        try:
            # 读取Excel文件，不设置header，先分析结构
            df_raw = pd.read_excel(file_path, header=None)
            
            # 查找包含日期列关键词的行作为表头
            header_row = None
            for i, row in df_raw.iterrows():
                row_values = row.values
                if any(config.date_column_keyword in str(val) for val in row_values):
                    header_row = i
                    self.logger.info(f"找到表头行在第{i}行: {row_values}")
                    break
            
            if header_row is None:
                self.logger.error("未找到有效的表头行")
                return None
            
            # 使用找到的行作为表头重新读取
            if config.use_skiprows:
                df = pd.read_excel(file_path, skiprows=header_row)
            else:
                df = pd.read_excel(file_path, header=header_row)
            self.logger.info(f"使用第{header_row+1}行作为表头，数据形状: {df.shape}")
            
            # 清理列名
            df.columns = df.columns.str.strip()

            # 过滤有效数据行（排除空的日期列）
            if config.date_column_keyword in df.columns:
                df = df.dropna(subset=[config.date_column_keyword], how='all')
                # 进一步过滤：确保日期列不是字符串关键词本身
                df = df[df[config.date_column_keyword] != config.date_column_keyword]
                self.logger.info(f"过滤后数据行数: {len(df)}")
            else:
                self.logger.error(f"未找到'{config.date_column_keyword}'列，可用列: {df.columns.tolist()}")
                return None
            
            # 重命名列以匹配标准格式
            df = df.rename(columns=config.column_mapping)
            return df
            
        except Exception as e:
            self.logger.error(f"提取{config.bank_info.name}交易数据失败: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return None
    
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
            bank = BankService.get_or_create_bank(
                code=self.get_bank_code(),
                name=self.get_bank_name()
            )
            
            # 确保账户存在
            account = AccountService.get_or_create_account(
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
                        transaction_type = 'income'
                    else:
                        transaction_type = 'expense'
                    
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
                        # 使用TransactionService创建交易记录
                        transaction = TransactionService.create_transaction(**transaction_data)
                        if transaction:
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
    
    def _extract_account_name(self, cell_value: str) -> Optional[str]:
        """通用账户名称提取实现
        
        Args:
            cell_value: 单元格字符串值
            
        Returns:
            str: 提取到的账户名称，未找到返回None
        """
        config = self.get_extraction_config()
        pattern = config.account_name_pattern
        
        if pattern.keyword in cell_value:
            name_match = re.search(pattern.regex_pattern, cell_value)
            if name_match:
                account_name = name_match.group(1).strip()
                self.logger.info(f"找到户名: {account_name}")
                return account_name
        return None
    
    def _extract_account_number(self, cell_value: str) -> Optional[str]:
        """通用账户号码提取实现
        
        Args:
            cell_value: 单元格字符串值
            
        Returns:
            str: 提取到的账户号码，未找到返回None
        """
        config = self.get_extraction_config()
        pattern = config.account_number_pattern
        
        if pattern.keyword in cell_value:
            number_match = re.search(pattern.regex_pattern, cell_value)
            if number_match:
                account_number = number_match.group(1).strip()
                self.logger.info(f"找到账号: {account_number}")
                return account_number
        return None
    
    def get_bank_code(self) -> str:
        """获取银行代码 - 通用实现"""
        config = self.get_extraction_config()
        if config.bank_info:
            return config.bank_info.code
        # 向后兼容：如果没有配置 bank_info，使用原有的抽象方法
        raise NotImplementedError("bank_info not configured in ExtractionConfig")
    
    def get_bank_name(self) -> str:
        """获取银行名称 - 通用实现"""
        config = self.get_extraction_config()
        if config.bank_info:
            return config.bank_info.name
        # 向后兼容：如果没有配置 bank_info，使用原有的抽象方法
        raise NotImplementedError("bank_info not configured in ExtractionConfig")
    
    def get_bank_keyword(self) -> str:
        """获取银行关键词 - 通用实现"""
        config = self.get_extraction_config()
        if config.bank_info:
            return config.bank_info.keyword
        # 向后兼容：如果没有配置 bank_info，使用原有的抽象方法
        raise NotImplementedError("bank_info not configured in ExtractionConfig")