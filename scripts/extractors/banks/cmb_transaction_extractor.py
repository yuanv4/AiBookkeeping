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

from scripts.extractors.base.bank_transaction_extractor import BankTransactionExtractor
from scripts.extractors.config.config_loader import get_config_loader

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
        try:
            # 提取账户信息
            account_name, account_number = self.extract_account_info(df)
            if not account_name or not account_number:
                self.logger.error("无法提取账户信息")
                return None
            
            # 查找标题行
            header_row_idx = self.find_header_row(df)
            if header_row_idx is None:
                self.logger.error("无法找到标题行")
                return None
                
            self.logger.info(f"找到标题行，索引为 {header_row_idx}")
            
            # 使用基类方法创建标准格式的DataFrame
            result_df = self.create_standard_dataframe(df, account_name, account_number, header_row_idx)
            
            # 如果创建标准DataFrame失败，则返回None
            if result_df is None:
                self.logger.error("创建标准格式DataFrame失败")
                return None
            
            # 初始化跟踪变量，用于检查是否找到所有必要字段
            found_fields = {
                'date': False,
                'amount': False
            }
            
            # 从配置获取列映射
            column_mappings = self.config.get("column_mappings", {})
            
            # 处理交易日期和其他字段
            for col in df.columns:
                col_name = col[0] if isinstance(col, tuple) else col
                col_name_str = str(col_name).lower()
                
                # 序号列 - 新增处理
                if self._match_column_name(col_name_str, column_mappings.get("row_index", [])):
                    self.logger.info(f"找到序号列: {col}")
                    result_df['row_index'] = df[col]
                    found_fields['row_index'] = True
                
                # 日期列
                elif self._match_column_name(col_name_str, column_mappings.get("date", [])):
                    self.logger.info(f"找到日期列: {col}")
                    result_df['transaction_date'] = df[col].apply(lambda x: self.standardize_date(x))
                    found_fields['date'] = True
                
                # 金额列
                elif self._match_column_name(col_name_str, column_mappings.get("amount", [])):
                    self.logger.info(f"找到金额列: {col}")
                    result_df['amount'] = df[col].apply(lambda x: self.clean_numeric(x))
                    found_fields['amount'] = True
                
                # 余额列
                elif self._match_column_name(col_name_str, column_mappings.get("balance", [])):
                    self.logger.info(f"找到余额列: {col}")
                    result_df['balance'] = df[col].apply(lambda x: self.clean_numeric(x))
                
                # 交易类型列
                elif self._match_column_name(col_name_str, column_mappings.get("transaction_type", [])):
                    self.logger.info(f"找到交易类型列: {col}")
                    result_df['transaction_type'] = df[col].fillna('其他')
                
                # 交易对象列
                elif self._match_column_name(col_name_str, column_mappings.get("counterparty", [])):
                    self.logger.info(f"找到交易对象列: {col}")
                    result_df['counterparty'] = df[col].fillna('')
                
                # 货币列
                elif '货币' in col_name_str or '币种' in col_name_str or 'currency' in col_name_str.lower():
                    self.logger.info(f"找到货币列: {col}")
                    result_df['currency'] = df[col].fillna('CNY')
            
            # 检查是否找到了必要的字段
            if not found_fields['date']:
                self.logger.error("未找到交易日期列，提取失败")
                return None
                
            if not found_fields['amount']:
                self.logger.error("未找到交易金额列，提取失败")
                return None
            
            # 如果没有找到序号列，使用基类的standardize_row_index方法生成序号
            if 'row_index' not in found_fields or not found_fields.get('row_index', False):
                self.logger.info("未找到序号列，将自动生成")
                result_df['row_index'] = self.standardize_row_index(df, header_row_idx)
                
            # 确保所有字段都有值
            # 货币默认为CNY
            if result_df['currency'].isnull().all():
                result_df['currency'] = self.config.get("default_currency", "CNY")
                
            # 交易类型默认为其他
            if result_df['transaction_type'].isnull().all():
                result_df['transaction_type'] = '其他'
                
            # 交易对手方默认为空字符串
            if result_df['counterparty'].isnull().all():
                result_df['counterparty'] = ''
            
            # 余额如果没有则计算累计（不完全准确但比没有好）
            if result_df['balance'].isnull().all():
                self.logger.warning("未找到余额列，将使用交易金额累计计算")
                # 按日期排序
                result_df = result_df.sort_values('transaction_date')
                # 计算累计余额
                result_df['balance'] = result_df['amount'].cumsum()
            
            # 过滤掉无用数据：表头、空行、或含有"Amount"、"Date"、"Transaction"、"Balance"等关键词的行
            # 这些可能是Excel中的列名或子标题
            invalid_rows = []
            keywords = ['amount', 'date', 'transaction', 'balance', 'currency', 'counter party', 'type']
            
            for idx, row in result_df.iterrows():
                # 检查是否是表头或含有关键词的行
                is_header_row = False
                
                # 检查交易对象是否是列标题
                if pd.notna(row['counterparty']):
                    counterparty_lower = str(row['counterparty']).lower()
                    if any(keyword in counterparty_lower for keyword in keywords):
                        is_header_row = True
                
                # 检查金额是否为0/None和日期是否缺失
                if (pd.isna(row['transaction_date']) or 
                    pd.isna(row['amount']) or 
                    row['amount'] == 0 or 
                    is_header_row):
                    invalid_rows.append(idx)
            
            # 移除无效行
            if invalid_rows:
                self.logger.info(f"过滤掉 {len(invalid_rows)} 条无效数据行")
                result_df = result_df.drop(invalid_rows)
            
            # 检查是否有有效的交易记录
            valid_transactions = result_df[(~result_df['amount'].isna()) & (~result_df['transaction_date'].isna())]
            
            if len(valid_transactions) == 0:
                self.logger.warning("过滤后没有有效的交易记录")
                return None
            
            # 确保所有数值字段都是数值型
            result_df['amount'] = result_df['amount'].apply(lambda x: float(x) if pd.notna(x) else None)
            result_df['balance'] = result_df['balance'].apply(lambda x: float(x) if pd.notna(x) else None)
            
            # 删除空行（金额和日期都为空的行）
            result_df = result_df.dropna(subset=['transaction_date', 'amount'], how='all')
            
            # 记录提取结果
            self.logger.info(f"共提取 {len(result_df)} 条交易记录")
            if not result_df.empty:
                self.logger.info(f"提取的第一条记录: {result_df.iloc[0].to_dict()}")
            
            return result_df
            
        except Exception as e:
            self.logger.error(f"提取交易数据时出错: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return None
    
    def _match_column_name(self, col_name: str, patterns: list) -> bool:
        """匹配列名是否符合给定的模式
        
        Args:
            col_name: 列名，已转换为小写
            patterns: 模式列表，来自配置
            
        Returns:
            bool: 是否匹配
        """
        if not patterns:
            return False
            
        for pattern in patterns:
            if pattern.lower() in col_name:
                return True
                
        return False
    
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