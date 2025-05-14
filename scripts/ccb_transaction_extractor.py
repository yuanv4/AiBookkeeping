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
                    rename_map[col] = "序号"
                elif "交易日期" in col_str:
                    rename_map[col] = "交易日期"
                elif "摘要" in col_str:
                    rename_map[col] = "交易类型"
                elif "币别" in col_str:
                    rename_map[col] = "货币"
                elif "交易金额" in col_str:
                    rename_map[col] = "交易金额"
                elif "账户余额" in col_str:
                    rename_map[col] = "账户余额"
            
            # 重命名列
            df = df.rename(columns=rename_map)
            print(f"\n标准化后的列名: {df.columns.tolist()}")
            
            # 创建标准格式的DataFrame
            result_columns = ['交易日期', '货币', '交易金额', '账户余额', '交易类型', '交易对象', '户名', '账号', 'row_index']
            result_df = pd.DataFrame(index=df.index)
            
            # 填充必要的数据
            if "交易日期" in df.columns:
                # 处理交易日期列
                try:
                    # 转换为日期格式
                    print(f"交易日期列原始数据样例: {df['交易日期'].head().tolist()}")
                    df['交易日期'] = df['交易日期'].astype(str)
                    df['交易日期'] = pd.to_datetime(df['交易日期'], errors='coerce')
                    
                    # 检查并填充无效日期
                    mask = pd.isna(df['交易日期'])
                    if mask.any():
                        self.logger.warning(f"发现{mask.sum()}条无效的交易日期，将使用当前日期替代")
                        df.loc[mask, '交易日期'] = pd.Timestamp.today().normalize()
                    
                    # 标准化为字符串格式的日期 (YYYY-MM-DD)
                    result_df['交易日期'] = df['交易日期'].dt.strftime('%Y-%m-%d')
                except Exception as e:
                    self.logger.error(f"处理交易日期时出错: {str(e)}")
                    # 使用当前日期作为默认值
                    today = pd.Timestamp.today().strftime('%Y-%m-%d')
                    self.logger.warning(f"由于处理错误，所有交易日期将使用今天的日期: {today}")
                    result_df['交易日期'] = today
            else:
                self.logger.warning(f"没有找到交易日期列，所有交易日期将使用今天的日期: {pd.Timestamp.today().strftime('%Y-%m-%d')}")
                result_df['交易日期'] = pd.Timestamp.today().strftime('%Y-%m-%d')
            
            # 处理序号作为row_index
            result_df['row_index'] = self.standardize_row_index(df, header_row_idx, "序号")
            
            # 处理货币列
            if "货币" in df.columns:
                result_df['货币'] = df['货币'].fillna('CNY')
            else:
                result_df['货币'] = 'CNY'
            
            # 处理金额和余额
            if "交易金额" in df.columns:
                result_df['交易金额'] = df['交易金额'].apply(self.clean_numeric)
            else:
                result_df['交易金额'] = 0.0
            
            if "账户余额" in df.columns:
                result_df['账户余额'] = df['账户余额'].apply(self.clean_numeric)
            else:
                result_df['账户余额'] = 0.0
            
            # 处理交易类型
            if "交易类型" in df.columns:
                result_df['交易类型'] = df['交易类型'].fillna('其他')
            else:
                result_df['交易类型'] = '其他'

            if "交易地点/附言" in df.columns:
                result_df['交易对象'] = df['交易地点/附言'].fillna('')
            else:
                result_df['交易对象'] = ''
            
            # 添加账户信息
            result_df['户名'] = account_name
            result_df['账号'] = account_number
            
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