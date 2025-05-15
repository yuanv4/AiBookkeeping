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
    
    def find_header_row(self, df: pd.DataFrame) -> Optional[int]:
        """查找标题行索引
        
        Args:
            df: DataFrame对象
            
        Returns:
            int: 标题行索引，如果未找到返回None
        """
        # 获取配置中的标题关键字
        header_keywords = self.config.get("header_keywords", ["交易日期", "金额", "余额", "摘要", "交易地点", "对方账号"])
        
        # 尝试在前30行找到包含至少3个标题关键字的行
        for idx in range(min(30, len(df))):
            row = df.iloc[idx]
            row_text = " ".join([str(val) for val in row if pd.notna(val)]).lower()
            
            keyword_count = sum(1 for keyword in header_keywords if keyword.lower() in row_text)
            if keyword_count >= 3:  # 至少包含3个关键字
                self.logger.info(f"在第{idx}行找到标题行，包含{keyword_count}个关键字")
                return idx
                
        return None
    
    def extract_transactions(self, df: pd.DataFrame) -> pd.DataFrame:
        """提取交易数据
        
        Args:
            df: 已读取的DataFrame对象
            
        Returns:
            pandas.DataFrame: 提取的交易数据
        """
        try:
            # 提取账户信息
            account_name, account_number = self.extract_account_info(df)
            
            # 查找标题行
            header_row_idx = self.find_header_row(df)
            if header_row_idx is None:
                self.logger.error("无法找到标题行")
                return None
                
            self.logger.info(f"找到标题行，索引为 {header_row_idx}")
            
            # 重新读取数据，使用标题行作为列名
            data_df = df.iloc[(header_row_idx+1):].reset_index(drop=True)
            header_df = df.iloc[header_row_idx]
            
            # 创建列名映射
            column_names = {}
            for i, column_value in enumerate(header_df):
                if pd.notna(column_value):
                    column_names[i] = str(column_value).strip()
                else:
                    column_names[i] = f"Column_{i}"
            
            # 重命名列
            data_df.columns = [column_names.get(i, f"Column_{i}") for i in range(len(data_df.columns))]
            self.logger.info(f"重命名后的列名: {data_df.columns.tolist()}")
            
            # 处理row_index - 使用"序号"列或者生成行索引
            if '序号' in data_df.columns:
                data_df['row_index'] = data_df['序号'].apply(lambda x: int(x) if pd.notna(x) and str(x).isdigit() else None)
            else:
                # 使用standardize_row_index方法标准化行索引
                data_df['row_index'] = self.standardize_row_index(data_df, header_row_idx)
                
            # 创建标准格式DataFrame
            result_df = self.create_standard_dataframe(data_df, account_name, account_number, header_row_idx)
            
            # 确保row_index被正确传递
            if 'row_index' in data_df.columns:
                result_df['row_index'] = data_df['row_index']
            
            # 修复：将original_data列转换为JSON字符串，而不是列表对象
            if 'original_data' in result_df.columns:
                result_df['original_data'] = result_df['original_data'].apply(lambda x: str(x) if isinstance(x, list) else x)
            
            # 从配置获取列映射
            column_mappings = self.config.get("column_mappings", {})
            
            # 映射列名
            mapped_columns = False
            for col in data_df.columns:
                col_lower = str(col).lower()
                
                # 日期列
                if any(pattern.lower() in col_lower for pattern in column_mappings.get("date", [])):
                    self.logger.info(f"找到日期列: {col}")
                    result_df['transaction_date'] = data_df[col].apply(lambda x: self.standardize_date(x))
                    mapped_columns = True
                
                # 金额列
                elif any(pattern.lower() in col_lower for pattern in column_mappings.get("amount", [])):
                    self.logger.info(f"找到金额列: {col}")
                    result_df['amount'] = data_df[col].apply(lambda x: self.clean_numeric(x))
                    mapped_columns = True
                
                # 余额列
                elif any(pattern.lower() in col_lower for pattern in column_mappings.get("balance", [])):
                    self.logger.info(f"找到余额列: {col}")
                    result_df['balance'] = data_df[col].apply(lambda x: self.clean_numeric(x))
                    mapped_columns = True
                
                # 交易类型/摘要列
                elif any(pattern.lower() in col_lower for pattern in column_mappings.get("transaction_type", [])):
                    self.logger.info(f"找到交易类型列: {col}")
                    result_df['transaction_type'] = data_df[col]
                    mapped_columns = True
                
                # 对方账户/交易对手列
                elif any(pattern.lower() in col_lower for pattern in column_mappings.get("counterparty", [])):
                    self.logger.info(f"找到交易对手列: {col}")
                    result_df['counterparty'] = data_df[col]
                    mapped_columns = True
            
            # 如果没有成功映射任何列，则尝试智能猜测
            if not mapped_columns:
                self.logger.warning("未能通过配置映射任何列，尝试智能猜测...")
                
                # 常见的列名模式
                date_patterns = ["日期", "交易日期", "time", "date"]
                amount_patterns = ["金额", "发生额", "交易金额", "金额(收入)", "金额(支出)", "amount"]
                balance_patterns = ["余额", "账户余额", "balance"]
                type_patterns = ["摘要", "交易类型", "交易摘要", "type", "description"]
                party_patterns = ["对方账号", "对方户名", "交易对手", "收款人", "付款人", "counterparty"]
                
                # 遍历所有列尝试匹配
                for col in data_df.columns:
                    col_lower = str(col).lower()
                    
                    if any(pattern in col_lower for pattern in date_patterns):
                        self.logger.info(f"猜测日期列: {col}")
                        result_df['transaction_date'] = data_df[col].apply(lambda x: self.standardize_date(x))
                    
                    elif any(pattern in col_lower for pattern in amount_patterns):
                        self.logger.info(f"猜测金额列: {col}")
                        result_df['amount'] = data_df[col].apply(lambda x: self.clean_numeric(x))
                    
                    elif any(pattern in col_lower for pattern in balance_patterns):
                        self.logger.info(f"猜测余额列: {col}")
                        result_df['balance'] = data_df[col].apply(lambda x: self.clean_numeric(x))
                    
                    elif any(pattern in col_lower for pattern in type_patterns):
                        self.logger.info(f"猜测交易类型列: {col}")
                        result_df['transaction_type'] = data_df[col]
                    
                    elif any(pattern in col_lower for pattern in party_patterns):
                        self.logger.info(f"猜测交易对手列: {col}")
                        result_df['counterparty'] = data_df[col]
            
            # 检查是否提取到必要字段
            if result_df['transaction_date'].isnull().all():
                self.logger.error("未能提取交易日期字段")
                return None
                
            if result_df['amount'].isnull().all():
                self.logger.error("未能提取交易金额字段")
                return None
            
            # 默认设置
            if result_df['currency'].isnull().all():
                result_df['currency'] = self.config.get("default_currency", "CNY")
                
            if result_df['transaction_type'].isnull().all():
                result_df['transaction_type'] = "其他"
                
            if result_df['counterparty'].isnull().all():
                result_df['counterparty'] = ""
            
            # 过滤无效数据
            valid_df = result_df.dropna(subset=['transaction_date', 'amount'])
            
            # 检查是否有有效数据
            if valid_df.empty:
                self.logger.warning("过滤后没有有效的交易数据")
                return None
                
            self.logger.info(f"成功提取 {len(valid_df)} 条交易记录")
            return valid_df
            
        except Exception as e:
            self.logger.error(f"提取交易数据时出错: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return None 