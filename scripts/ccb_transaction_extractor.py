import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import re
import glob
import logging
from datetime import datetime
from pathlib import Path
import numpy as np

from scripts.bank_transaction_extractor import BankTransactionExtractor

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('ccb_extractor')

class CCBTransactionExtractor(BankTransactionExtractor):
    """建设银行交易明细提取器"""
    
    def __init__(self):
        """初始化建设银行交易提取器"""
        super().__init__('CCB')
    
    def can_process_file(self, file_path):
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
            
            # 如果能提取到账户信息，说明是建设银行的交易明细
            if account_name and account_number:
                self.logger.info(f"成功识别为建设银行交易明细 - 户名: {account_name}, 账号: {account_number}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"检查文件时出错: {e}")
            return False

    def standardize_date(self, date_str):
        """标准化日期格式"""
        if pd.isna(date_str):
            return None
        try:
            # 尝试解析日期
            date_obj = pd.to_datetime(date_str)
            return date_obj.strftime('%Y-%m-%d')
        except:
            return None

    def standardize_time(self, time_str):
        """标准化时间格式"""
        if pd.isna(time_str):
            return None
        try:
            # 尝试解析时间
            time_obj = pd.to_datetime(time_str)
            return time_obj.strftime('%H:%M:%S')
        except:
            return None

    def clean_numeric(self, value):
        """清理数值数据"""
        if pd.isna(value):
            return None
        try:
            # 如果是字符串，移除所有非数字字符（保留小数点和负号）
            if isinstance(value, str):
                # 移除所有空格
                value = value.strip()
                # 移除所有非数字字符（保留小数点和负号）
                value = ''.join(c for c in value if c.isdigit() or c in '.-')
            return float(value)
        except:
            return None

    def extract_account_info(self, df):
        """从DataFrame中提取户名和账号信息"""
        account_name = ""
        account_number = ""
        
        self.logger.info("开始提取建设银行账户信息")
        # 打印前5行数据用于调试
        for idx, row in df.head(5).iterrows():
            self.logger.info(f"检查行 {idx}: {row.tolist()}")
        
        # 尝试从数据框中查找特定模式或关键字
        for idx, row in df.iterrows():
            for col_idx in range(min(len(row), 10)):  # 只检查前10列
                if pd.isna(row[col_idx]):
                    continue
                
                cell_value = str(row[col_idx])
                self.logger.info(f"检查单元格 [{idx},{col_idx}]: {cell_value}")
                
                # 检查是否包含账号信息
                if '卡号/账号' in cell_value:
                    self.logger.info(f"找到包含卡号/账号的单元格: {cell_value}")
                    # 尝试提取账号 - 建设银行账号通常是19位数字
                    account_match = re.search(r'[0-9]{16,19}', cell_value)
                    if account_match:
                        account_number = account_match.group(0)
                        self.logger.info(f"提取到卡号/账号: {account_number}")
                
                # 检查是否包含户名信息
                if '客户名称' in cell_value:
                    self.logger.info(f"找到包含客户名称的单元格: {cell_value}")
                    # 提取姓名，使用冒号分隔
                    parts = cell_value.split("客户名称:")
                    if len(parts) > 1:
                        possible_name = parts[1].strip().split()[0].strip()
                        self.logger.info(f"按冒号分割后: {parts}, 可能的姓名: {possible_name}")
                        if 1 <= len(possible_name) <= 10:  # 合理的姓名长度
                            account_name = possible_name
                            self.logger.info(f"提取到客户名称: {account_name}")
                    else:
                        # 尝试使用空格分隔
                        parts = cell_value.split("客户名称")
                        if len(parts) > 1:
                            name_part = parts[1].strip()
                            # 去掉可能的前导符号如冒号
                            if name_part.startswith(':') or name_part.startswith('：'):
                                name_part = name_part[1:].strip()
                            # 如果有多个部分，取第一部分作为姓名
                            possible_name = name_part.split()[0].strip() if name_part.split() else name_part
                            self.logger.info(f"按空格分割后: {name_part}, 可能的姓名: {possible_name}")
                            if 1 <= len(possible_name) <= 10:  # 合理的姓名长度
                                account_name = possible_name
                                self.logger.info(f"提取到客户名称: {account_name}")
        
        # 如果没有找到任何信息，可以使用默认值
        if not account_name and not account_number:
            self.logger.warning("未能提取到建设银行账户信息")
            return "", ""
            
        self.logger.info(f"建设银行账户信息 - 户名: '{account_name}', 账号: '{account_number}'")
        return account_name, account_number
    
    def extract_transactions(self, file_path):
        """从Excel文件中提取交易数据"""
        try:
            # 先读取前几行数据用于提取账户信息
            df_meta = pd.read_excel(file_path, header=None, nrows=10)
            account_name, account_number = self.extract_account_info(df_meta)
            
            if not account_name or not account_number:
                self.logger.error("无法提取账户信息")
                return None
            
            # 找到真正的数据标题行（通常包含"序号"、"摘要"、"交易日期"等字段）
            header_row_idx = None
            for idx, row in df_meta.iterrows():
                # 查找包含"序号"或"交易日期"的行作为标题行
                row_values = [str(val).strip() if not pd.isna(val) else "" for val in row]
                row_text = " ".join(row_values).lower()
                if "序号" in row_text and "交易日期" in row_text:
                    header_row_idx = idx
                    self.logger.info(f"找到标题行：索引={header_row_idx}, 内容={row_values}")
                    break
            
            if header_row_idx is None:
                self.logger.error("无法找到标题行")
                return None
            
            # 重新读取Excel文件，使用找到的标题行作为列名
            df = pd.read_excel(file_path, header=header_row_idx)
            
            # 打印列名，用于调试
            print(f"\n找到的列名: {df.columns.tolist()}")
            
            # 尝试标准化列名
            rename_map = {}
            for col in df.columns:
                if not isinstance(col, str):
                    continue
                    
                col_str = str(col).strip().lower()
                
                if "序号" in col_str:
                    rename_map[col] = "row_index"
                elif "交易日期" in col_str:
                    rename_map[col] = "transaction_date"
                elif "摘要" in col_str:
                    rename_map[col] = "transaction_type"
                elif "币别" in col_str:
                    rename_map[col] = "currency"
                elif "交易金额" in col_str:
                    rename_map[col] = "amount"
                elif "账户余额" in col_str:
                    rename_map[col] = "balance"
                elif "交易地点/附言" in col_str:
                    rename_map[col] = "counterparty"
                elif "对方账号与户名" in col_str:
                    rename_map[col] = "counterparty_account"
            
            # 重命名列
            df = df.rename(columns=rename_map)
            print(f"\n标准化后的列名: {df.columns.tolist()}")
            
            # 使用基类方法创建标准格式的DataFrame
            result_df = self.create_standard_dataframe(df, account_name, account_number, header_row_idx)
            
            # 如果创建标准DataFrame失败，则返回None
            if result_df is None:
                self.logger.error("创建标准格式DataFrame失败")
                return None
            
            # 初始化变量，用于跟踪是否找到必要字段
            found_date = False
            found_amount = False
            
            # 填充必要的数据
            if "transaction_date" in df.columns:
                # 处理交易日期列
                try:
                    # 转换为日期格式
                    print(f"交易日期列原始数据样例: {df['transaction_date'].head().tolist()}")
                    df['transaction_date'] = df['transaction_date'].astype(str)
                    df['transaction_date'] = pd.to_datetime(df['transaction_date'], errors='coerce')
                    
                    # 检查并填充无效日期
                    mask = pd.isna(df['transaction_date'])
                    if mask.any():
                        self.logger.warning(f"发现{mask.sum()}条无效的交易日期")
                    
                    # 标准化为字符串格式的日期 (YYYY-MM-DD)
                    result_df['transaction_date'] = df['transaction_date'].dt.strftime('%Y-%m-%d')
                    found_date = True
                except Exception as e:
                    self.logger.error(f"处理交易日期时出错: {str(e)}")
            
            # 如果未找到交易日期字段，返回提取失败
            if not found_date:
                self.logger.error("未找到交易日期字段，提取失败")
                return None
            
            # 处理金额和余额
            if "amount" in df.columns:
                result_df['amount'] = df['amount'].apply(self.clean_numeric)
                found_amount = True
            
            # 如果未找到金额字段，返回提取失败
            if not found_amount:
                self.logger.error("未找到交易金额字段，提取失败")
                return None
            
            if "balance" in df.columns:
                result_df['balance'] = df['balance'].apply(self.clean_numeric)
            else:
                # 尝试计算余额（虽然不完全准确）
                self.logger.warning("未找到余额字段，将使用交易金额累计计算")
                # 按日期排序
                result_df = result_df.sort_values('transaction_date')
                # 计算累计余额
                result_df['balance'] = result_df['amount'].cumsum()
            
            # 处理交易类型
            if "transaction_type" in df.columns:
                result_df['transaction_type'] = df['transaction_type'].fillna('其他')
            else:
                result_df['transaction_type'] = '其他'

            if "counterparty" in df.columns:
                result_df['counterparty'] = df['counterparty'].fillna('')
            else:
                result_df['counterparty'] = ''
                
            # 处理货币
            if "currency" in df.columns:
                result_df['currency'] = df['currency'].fillna('CNY')
            else:
                result_df['currency'] = 'CNY'
            
            # 过滤掉无效行（如金额为0或日期为空的行）
            invalid_rows = []
            for idx, row in result_df.iterrows():
                if pd.isna(row['transaction_date']) or pd.isna(row['amount']) or row['amount'] == 0:
                    invalid_rows.append(idx)
            
            if invalid_rows:
                self.logger.info(f"过滤掉 {len(invalid_rows)} 条无效数据行")
                result_df = result_df.drop(invalid_rows)
            
            # 检查是否有有效的交易记录
            if len(result_df) == 0:
                self.logger.warning("过滤后没有有效的交易记录")
                return None
            
            return result_df
            
        except Exception as e:
            self.logger.error(f"提取交易数据时出错: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return None
    
    def get_bank_keyword(self):
        """获取银行关键字用于筛选文件"""
        return '建设银行'


if __name__ == "__main__":
    extractor = CCBTransactionExtractor()
    extractor.run() 