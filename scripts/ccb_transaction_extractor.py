import pandas as pd
import re
import os
import glob
import logging
import sys
from datetime import datetime
from pathlib import Path

from bank_transaction_extractor import BankTransactionExtractor

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

    def standardize_date(self, date_value):
        """将各种日期格式标准化为YYYY-MM-DD"""
        if pd.isna(date_value):
            return None
        
        # 尝试将数字格式转换为日期格式 (YYYYMMDD -> YYYY-MM-DD)
        if isinstance(date_value, (int, float)) or (isinstance(date_value, str) and date_value.isdigit()):
            try:
                date_str = str(int(date_value))
                if len(date_str) == 8:  # YYYYMMDD
                    return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
            except:
                pass
        
        # 处理字符串格式
        if isinstance(date_value, str):
            # 已经是标准格式
            if re.match(r'^\d{4}-\d{2}-\d{2}$', date_value):
                return date_value
            
            # 处理YYYY/MM/DD格式
            if re.match(r'^\d{4}/\d{1,2}/\d{1,2}$', date_value):
                parts = date_value.split('/')
                year = parts[0]
                month = parts[1].zfill(2)
                day = parts[2].zfill(2)
                return f"{year}-{month}-{day}"
        
        # 其他情况，尝试转换为datetime然后格式化
        try:
            return pd.to_datetime(date_value).strftime('%Y-%m-%d')
        except:
            self.logger.warning(f"无法标准化日期: {date_value}")
            return None

    def clean_numeric(self, value):
        """清理并转换数值型数据"""
        if pd.isna(value):
            return 0.0
        
        if isinstance(value, (int, float)):
            return float(value)
        
        if isinstance(value, str):
            # 移除货币符号、逗号和空白
            cleaned = re.sub(r'[,¥$€£\s]', '', value)
            # 处理带括号的负数
            if cleaned.startswith('(') and cleaned.endswith(')'):
                cleaned = '-' + cleaned[1:-1]
            
            try:
                return float(cleaned)
            except:
                return 0.0
        
        return 0.0

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
        """从建设银行Excel文件中提取交易记录"""
        self.logger.info(f"处理建设银行文件: {file_path}")
        print(f"处理文件: {file_path}")  # 添加控制台输出
        
        try:
            # 尝试读取Excel文件
            print(f"尝试读取Excel文件...")
            print(f"文件路径: {os.path.abspath(file_path)}")
            print(f"文件是否存在: {os.path.exists(file_path)}")
            
            # 尝试不同的引擎
            for engine in ['openpyxl', 'xlrd']:
                try:
                    print(f"尝试使用 {engine} 引擎读取...")
                    if engine == 'xlrd':
                        df = pd.read_excel(file_path, header=None, engine=engine)
                    else:
                        df = pd.read_excel(file_path, header=None, engine=engine)
                    print(f"使用 {engine} 引擎成功读取，行数: {len(df)}")
                    break
                except Exception as e:
                    print(f"使用 {engine} 引擎失败: {e}")
            else:
                raise Exception("所有引擎都失败了")
            
            # 如果文件为空，返回空DataFrame
            if df.empty:
                self.logger.warning(f"文件为空: {file_path}")
                print("文件为空")
                return None
            
            # 打印前10行数据用于调试
            print("\n前10行数据:")
            for i, row in df.head(10).iterrows():
                print(f"行 {i}: {row.tolist()}")
            
            # 检查文件内容，找到表头行
            header_row_idx = None
            print("\n查找表头行...")
            for idx, row in df.iterrows():
                # 检查是否包含典型的表头字段
                row_values = [str(val).strip() for val in row if pd.notna(val)]
                row_text = ' '.join(row_values).lower()
                print(f"行 {idx} 文本: {row_text}")
                
                # 直接打印该行的值
                print(f"行 {idx} 值: {row.tolist()}")
                
                # 检查是否包含多个关键字段
                keywords = ['序号', '摘要', '交易日期', '交易金额']
                keyword_count = sum(1 for keyword in keywords if keyword.lower() in row_text)
                
                if keyword_count >= 3:  # 如果至少包含3个关键字段
                    header_row_idx = idx
                    print(f"找到表头行 {idx}: {row_text}")
                    break
                
                # 只检查前20行
                if idx >= 20:
                    break
            
            if header_row_idx is None:
                self.logger.warning(f"无法找到表头行: {file_path}")
                print("无法找到表头行，尝试查找具有更多列的行...")
                
                # 查找具有最多非空值的行作为表头
                max_columns = 0
                for idx, row in df.iterrows():
                    non_na_count = row.notna().sum()
                    if non_na_count > max_columns:
                        max_columns = non_na_count
                        header_row_idx = idx
                    
                    # 只检查前20行
                    if idx >= 20:
                        break
                
                print(f"选择行 {header_row_idx} 作为表头，该行有 {max_columns} 个非空值")
            
            # 使用找到的表头行作为列名
            headers = []
            for col in df.iloc[header_row_idx]:
                if pd.isna(col):
                    headers.append('')
                else:
                    headers.append(str(col).strip())
            
            print(f"\n使用的表头: {headers}")
            
            # 创建新的DataFrame，使用表头下的数据
            data_df = df.iloc[header_row_idx+1:].reset_index(drop=True)
            data_df.columns = headers
            
            print(f"\n数据行数: {len(data_df)}")
            if not data_df.empty:
                print("数据前5行:")
                for i, row in data_df.head(5).iterrows():
                    print(f"行 {i}: {dict(zip(headers, row.tolist()))}")
            
            # 查找必要的列
            required_columns = ['交易日期', '摘要', '交易金额', '账户余额', '币别', '对方账号与户名']
            print(f"\n需要查找的列: {required_columns}")
            print(f"现有的列: {[col for col in data_df.columns if col]}")
            
            # 将'交易地点/附言'保留为单独的列，避免映射冲突
            column_mapping = {}
            for col in data_df.columns:
                if not col or not isinstance(col, str):
                    continue
                    
                col_lower = col.lower()
                
                print(f"检查列: '{col}'")
                
                if '日期' in col_lower or '时间' in col_lower:
                    column_mapping[col] = '交易日期'
                    print(f"  '{col}' -> '交易日期'")
                elif '摘要' in col_lower or '类型' in col_lower:
                    column_mapping[col] = '交易类型'
                    print(f"  '{col}' -> '交易类型'")
                elif ('金额' in col_lower or '发生额' in col_lower) and ('交易' in col_lower or not '余额' in col_lower):
                    column_mapping[col] = '交易金额'
                    print(f"  '{col}' -> '交易金额'")
                elif '余额' in col_lower:
                    column_mapping[col] = '账户余额'
                    print(f"  '{col}' -> '账户余额'")
                elif '币' in col_lower or '币别' in col_lower:
                    column_mapping[col] = '货币'
                    print(f"  '{col}' -> '货币'")
                # 不要在此处映射交易地点/附言，保持原样
                # 也不要在此处映射对方账号与户名，以避免冲突
            
            print(f"\n列映射: {column_mapping}")
            
            # 重命名列
            data_df = data_df.rename(columns=column_mapping)
            
            print(f"\n重命名后的列: {data_df.columns.tolist()}")
            
            # 提取账户信息
            account_name, account_number = self.extract_account_info(df)
            
            # 创建标准格式的DataFrame
            result_columns = ['交易日期', '货币', '交易金额', '账户余额', '交易类型', '交易对象', '户名', '账号']
            result_df = pd.DataFrame(columns=result_columns)
            
            # 赋值数据
            if '交易日期' in data_df.columns:
                print(f"\n交易日期样例: {data_df['交易日期'].head().tolist()}")
                result_df['交易日期'] = data_df['交易日期'].apply(self.standardize_date)
                print(f"标准化后的交易日期样例: {result_df['交易日期'].head().tolist()}")
            else:
                self.logger.warning("未找到交易日期列")
                print("\n未找到交易日期列。所有列名: ", [col for col in data_df.columns if col])
                
                # 检查是否有其他列可能包含日期
                date_cols = []
                for col in data_df.columns:
                    if col and any(keyword in str(col).lower() for keyword in ['日期', '时间', 'date', 'time']):
                        date_cols.append(col)
                
                if date_cols:
                    print(f"可能包含日期的其他列: {date_cols}")
                    # 尝试第一个可能的日期列
                    result_df['交易日期'] = data_df[date_cols[0]].apply(self.standardize_date)
                    print(f"使用列 {date_cols[0]} 作为交易日期")
                else:
                    print("未找到任何可能包含日期的列")
                    return None
            
            # 处理货币列
            if '货币' in data_df.columns:
                result_df['货币'] = data_df['货币'].apply(lambda x: 'CNY' if pd.isna(x) or '人民币' in str(x) else str(x)[:3])
            else:
                # 默认使用人民币
                result_df['货币'] = 'CNY'
            
            # 处理金额和余额
            if '交易金额' in data_df.columns:
                print(f"\n交易金额样例: {data_df['交易金额'].head().tolist()}")
                result_df['交易金额'] = data_df['交易金额'].apply(self.clean_numeric)
                print(f"清理后的交易金额样例: {result_df['交易金额'].head().tolist()}")
            else:
                # 查找可能包含金额的列
                amount_cols = []
                for col in data_df.columns:
                    if col and any(keyword in str(col).lower() for keyword in ['金额', '发生额', 'amount']):
                        amount_cols.append(col)
                
                if amount_cols:
                    print(f"可能包含交易金额的其他列: {amount_cols}")
                    result_df['交易金额'] = data_df[amount_cols[0]].apply(self.clean_numeric)
                else:
                    result_df['交易金额'] = 0.0
            
            if '账户余额' in data_df.columns:
                result_df['账户余额'] = data_df['账户余额'].apply(self.clean_numeric)
            else:
                # 查找可能包含余额的列
                balance_cols = []
                for col in data_df.columns:
                    if col and any(keyword in str(col).lower() for keyword in ['余额', 'balance']):
                        balance_cols.append(col)
                
                if balance_cols:
                    print(f"可能包含账户余额的其他列: {balance_cols}")
                    result_df['账户余额'] = data_df[balance_cols[0]].apply(self.clean_numeric)
                else:
                    result_df['账户余额'] = 0.0
            
            # 处理交易类型和交易对象
            if '交易类型' in data_df.columns:
                result_df['交易类型'] = data_df['交易类型']
            elif '摘要' in data_df.columns:
                result_df['交易类型'] = data_df['摘要']
            else:
                result_df['交易类型'] = '未知'
            
            # 处理交易对象 - 明确使用交易地点/附言作为交易对象
            if '交易地点/附言' in data_df.columns:
                print("使用'交易地点/附言'列作为交易对象")
                result_df['交易对象'] = data_df['交易地点/附言'].astype(str)
            elif '对方账号与户名' in data_df.columns:
                print("使用'对方账号与户名'列作为交易对象")
                result_df['交易对象'] = data_df['对方账号与户名'].astype(str)
            else:
                print("未找到合适的交易对象列，使用空值")
                result_df['交易对象'] = ''
            
            # 添加户名和账号
            result_df['户名'] = account_name
            result_df['账号'] = account_number
            
            # 过滤掉无效记录
            result_df = result_df[result_df['交易日期'].notna()]
            
            print(f"\n提取的交易记录数: {len(result_df)}")
            if not result_df.empty:
                print("提取的数据前5行:")
                print(result_df.head().to_string())
            
            self.logger.info(f"从文件中提取了 {len(result_df)} 条交易记录")
            return result_df
        
        except Exception as e:
            self.logger.error(f"处理文件时出错: {e}")
            print(f"处理文件时出错: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def get_bank_keyword(self):
        """获取银行关键字用于筛选文件"""
        return '建设银行'


if __name__ == "__main__":
    extractor = CCBTransactionExtractor()
    extractor.run() 