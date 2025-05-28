"""招商银行交易明细提取器"""
import pandas as pd
import re
import os
import logging
from datetime import datetime
import sys
from typing import Optional

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

from core.extractors.base.bank_transaction_extractor import BankTransactionExtractor
from core.extractors.config.config_loader import get_config_loader

# 配置日志
logger = logging.getLogger('cmb_extractor')

class CMBTransactionExtractor(BankTransactionExtractor):
    """招商银行交易明细提取器"""
    
    def __init__(self):
        """初始化招商银行交易提取器"""
        super().__init__('CMB')
        self.config = get_config_loader().get_bank_config('CMB')
    
    def can_process_file(self, file_path: str) -> bool:
        """检查是否可以处理给定的文件
        
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
            
            # 使用extract_account_info方法尝试提取账户信息
            account_name, account_number = self.extract_account_info(df)
            
            # 如果能提取到账户信息，说明是招商银行的交易明细
            if account_name and account_number:
                self.logger.info(f"成功识别为招商银行交易明细 - 户名: {account_name}, 账号: {account_number}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"检查文件时出错: {e}")
            return False
    
    def is_date_format(self, value) -> bool:
        """检查值是否符合日期格式（支持多种格式）"""
        if pd.isna(value):
            return False
        
        # 如果是datetime对象，直接返回True
        if isinstance(value, datetime):
            return True
        
        # 如果是字符串，检查多种格式
        if isinstance(value, str):
            # 支持的格式: YYYY-MM-DD, YYYY/MM/DD
            patterns = [
                r'^\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
                r'^\d{4}/\d{1,2}/\d{1,2}',  # YYYY/MM/DD
            ]
            for pattern in patterns:
                if re.match(pattern, value):
                    return True
        
        return False
    
    def extract_account_info(self, df: pd.DataFrame) -> tuple:
        """从DataFrame中提取户名和账号信息"""
        account_name = ""
        account_number = ""
        
        # 遍历DataFrame的每一行
        for idx, row in df.iterrows():
            # 检查是否有足够的列
            if len(row) == 0:
                continue
                
            # 获取第一列的值
            first_cell_value = str(row[0]) if pd.notna(row[0]) else ""
            
            # 查找户名行
            if '户    名：' in first_cell_value or '户名：' in first_cell_value:
                account_name = first_cell_value.replace('户    名：', '').replace('户名：', '').strip()
            
            # 查找账号行 - 检查多个可能的列
            for col_idx in range(min(len(row), 5)):  # 只检查前5列
                cell_value = str(row[col_idx]) if pd.notna(row[col_idx]) else ""
                if '账号：' in cell_value or '账    号：' in cell_value:
                    account_number = cell_value.replace('账号：', '').replace('账    号：', '').strip()
                    break
                
            # 如果已经找到户名和账号，就可以返回了
            if account_name and account_number:
                break
        
        if not account_name or not account_number:
            self.logger.warning(f"未能完全提取账户信息 - 户名: '{account_name}', 账号: '{account_number}'")
        else:
            self.logger.info(f"成功提取账户信息 - 户名: '{account_name}', 账号: '{account_number}'")
            
        return account_name, account_number
    
    def find_header_row(self, df: pd.DataFrame) -> Optional[int]:
        """查找标题行索引
        
        Args:
            df: DataFrame对象
            
        Returns:
            int: 标题行索引，如果未找到返回None
        """
        # 获取配置中的标题关键字
        header_keywords = self.config.get("header_keywords", ["记账日期", "交易日期", "账务日期", "交易金额", "发生额"])
        
        # 尝试在前20行找到包含标题关键字的行
        for idx in range(min(20, len(df))):
            row = df.iloc[idx]
            # 将行转为字符串后合并
            row_text = " ".join([str(val) for val in row if pd.notna(val)]).lower()
            # 检查是否包含常见的标题关键字
            if any(keyword.lower() in row_text for keyword in header_keywords):
                return idx
        return None
    
    def extract_transactions(self, df: pd.DataFrame) -> pd.DataFrame:
        """提取交易数据
        
        Args:
            df: 已读取的DataFrame对象
            
        Returns:
            pandas.DataFrame: 提取的交易数据，如果提取失败返回None
        """
        # 调用基类的提取方法
        return self.extract_transactions_from_df(df)
    
    def create_standard_dataframe(self, df: pd.DataFrame, account_name: str, account_number: str, header_row_idx: int) -> pd.DataFrame:
        """创建标准格式的交易数据DataFrame
        
        Args:
            df: 原始DataFrame
            account_name: 账户名称
            account_number: 账户号码
            header_row_idx: 标题行索引
            
        Returns:
            pandas.DataFrame: 标准格式的DataFrame
        """
        # 先调用基类方法创建标准框架
        result_df = super().create_standard_dataframe(df, account_name, account_number, header_row_idx)
        if result_df is None:
            return None
            
        # 将标准DataFrame的索引设置为与原始DataFrame相同
        result_df = pd.DataFrame(index=df.index, columns=result_df.columns)
        
        # 添加账户和银行信息
        result_df['account_number'] = account_number
        result_df['account_name'] = account_name
        result_df['bank_code'] = self.get_bank_code()
        result_df['bank_name'] = self.get_bank_name()
        
        return result_df