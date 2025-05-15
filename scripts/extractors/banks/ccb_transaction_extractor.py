"""建设银行交易明细提取器"""
import pandas as pd
import re
import os
import logging
from datetime import datetime
import sys
from typing import Optional, Tuple, Dict, List, Any

# 添加项目根目录到PYTHONPATH
current_dir = os.path.dirname(os.path.abspath(__file__))
banks_dir = os.path.dirname(current_dir)
extractors_dir = os.path.dirname(banks_dir)
scripts_dir = os.path.dirname(extractors_dir)
root_dir = os.path.dirname(scripts_dir)
if root_dir not in sys.path:
    sys.path.append(root_dir)
if scripts_dir not in sys.path:
    sys.path.append(scripts_dir)

from scripts.extractors.base.bank_transaction_extractor import BankTransactionExtractor
from scripts.extractors.config.config_loader import get_config_loader

# 配置日志
logger = logging.getLogger('ccb_extractor')

class CCBTransactionExtractor(BankTransactionExtractor):
    """建设银行交易明细提取器"""
    
    def __init__(self):
        """初始化建设银行交易提取器"""
        super().__init__('CCB')
        self.config = get_config_loader().get_bank_config('CCB')
        
    def get_bank_code(self) -> str:
        """获取银行代码"""
        return 'CCB'
        
    def get_bank_name(self) -> str:
        """获取银行名称"""
        return '建设银行'
        
    def get_bank_keyword(self) -> str:
        """获取银行关键词，用于文件匹配"""
        return '建设银行'
    
    def can_process_file(self, file_path: str) -> bool:
        """判断是否可以处理指定文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            bool: 是否可以处理该文件
        """
        try:
            # 检查文件扩展名
            if not file_path.lower().endswith(('.xlsx', '.xls')):
                return False
            
            # 尝试读取文件的前几行
            df = pd.read_excel(file_path, header=None, nrows=20)
            
            # 检查是否包含建设银行相关关键词
            keywords = self.config.get("keywords", ["建设银行", "建行", "CCB"])
            
            # 检查每一行是否包含关键词
            for idx, row in df.iterrows():
                row_text = " ".join([str(val) for val in row if pd.notna(val)])
                if any(keyword in row_text for keyword in keywords):
                    account_name, account_number = self.extract_account_info(df)
                    if account_name or account_number:
                        self.logger.info(f"成功识别为建设银行交易明细 - 户名: {account_name}, 账号: {account_number}")
                        return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"检查文件时出错: {e}")
            return False
    
    def extract_account_info(self, df: pd.DataFrame) -> Tuple[str, str]:
        """提取账户信息
        
        Args:
            df: 包含账户信息的DataFrame
            
        Returns:
            tuple: (account_name, account_number)
        """
        account_name = ""
        account_number = ""
        
        # 尝试在前20行中提取账户信息
        for idx, row in df.iterrows():
            if idx > 20:  # 只检查前20行
                break
                
            # 将行转换为文本
            row_text = " ".join([str(val) for val in row if pd.notna(val)])
            
            # 查找账号信息
            account_patterns = [
                r'账号[：:\s]*([0-9*]{10,})',
                r'Account Number[：:\s]*([0-9*]{10,})',
                r'账户[：:\s]*([0-9*]{10,})'
            ]
            
            for pattern in account_patterns:
                matches = re.search(pattern, row_text)
                if matches:
                    account_number = matches.group(1).strip()
                    break
            
            # 查找户名信息
            name_patterns = [
                r'户名[：:\s]*([^\s]{2,})',
                r'姓名[：:\s]*([^\s]{2,})',
                r'客户姓名[：:\s]*([^\s]{2,})'
            ]
            
            for pattern in name_patterns:
                matches = re.search(pattern, row_text)
                if matches:
                    account_name = matches.group(1).strip()
                    break
            
            # 如果找到了账号和户名，就退出循环
            if account_name and account_number:
                break
        
        if account_name or account_number:
            self.logger.info(f"提取到账户信息: 户名={account_name}, 账号={account_number}")
        
        return account_name, account_number
    
    def extract_transactions(self, df: pd.DataFrame) -> pd.DataFrame:
        """提取交易数据
        
        Args:
            df: 已读取的DataFrame对象
            
        Returns:
            pandas.DataFrame: 提取的交易数据，如果提取失败返回None
        """
        # 调用基类的提取方法
        return self.extract_transactions_from_df(df) 