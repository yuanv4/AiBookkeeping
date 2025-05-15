"""银行交易提取器基类，提供通用功能"""
import pandas as pd
import re
import os
import glob
import logging
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Union

# 添加项目根目录到PYTHONPATH
current_dir = os.path.dirname(os.path.abspath(__file__))
extractors_dir = os.path.dirname(current_dir)
scripts_dir = os.path.dirname(extractors_dir)
root_dir = os.path.dirname(scripts_dir)
if root_dir not in sys.path:
    sys.path.append(root_dir)
if scripts_dir not in sys.path:
    sys.path.append(scripts_dir)

# 导入接口和配置
from scripts.extractors.interfaces.extractor_interface import ExtractorInterface
from scripts.extractors.config.config_loader import get_config_loader
from scripts.db.db_manager import DBManager

# 设置日志格式
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class BankTransactionExtractor(ExtractorInterface):
    """银行交易明细提取器基类"""
    
    def __init__(self, bank_code: str):
        """初始化提取器
        
        Args:
            bank_code: 银行代码，如CMB、CCB等
        """
        self.bank_code = bank_code
        self.logger = logging.getLogger(f'{bank_code}_extractor')
        self.db_manager = DBManager()
        
        # 加载配置
        self.config_loader = get_config_loader()
        self.bank_config = self.config_loader.get_bank_config(bank_code)
        
        if not self.bank_config:
            self.logger.warning(f"未找到银行配置: {bank_code}")
    
    def get_bank_code(self) -> str:
        """获取银行代码"""
        return self.bank_code
    
    def get_bank_name(self) -> str:
        """获取银行名称"""
        if self.bank_config:
            return self.bank_config.get("bank_name", self.bank_code)
        return self.bank_code
    
    def get_bank_keyword(self) -> str:
        """获取银行关键词用于匹配"""
        if self.bank_config and "keywords" in self.bank_config:
            # 返回第一个关键词
            return self.bank_config["keywords"][0]
        return self.bank_code
    
    def standardize_date(self, date_value: Any) -> Optional[str]:
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
    
    def clean_numeric(self, value: Any) -> float:
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
        try:
            self.logger.info(f"创建标准格式的DataFrame，原始列: {df.columns.tolist()}")
            
            # 创建一个空的标准格式DataFrame
            result_df = pd.DataFrame(columns=[
                'transaction_date',  # 交易日期
                'transaction_id',    # 交易ID（可能为空）
                'amount',            # 交易金额
                'balance',           # 余额
                'transaction_type',  # 交易类型
                'counterparty',      # 交易对手方
                'currency',          # 币种
                'remarks',           # 备注
                'account_number',    # 账号
                'account_name',      # 户名
                'bank_code',         # 银行代码
                'bank_name',         # 银行名称
                'original_data'      # 原始数据
            ])
            
            # 添加原始数据
            result_df['original_data'] = [df.to_dict(orient='records')] * len(df)
            
            # 添加账户和银行信息
            result_df['account_number'] = account_number
            result_df['account_name'] = account_name
            result_df['bank_code'] = self.get_bank_code()
            result_df['bank_name'] = self.get_bank_name()
            
            # 默认初始化其他字段
            result_df['transaction_date'] = None
            result_df['transaction_id'] = None
            result_df['amount'] = None
            result_df['balance'] = None
            result_df['transaction_type'] = None
            result_df['counterparty'] = None
            result_df['currency'] = None
            result_df['remarks'] = None
            
            # 返回待填充的标准格式DataFrame
            return result_df
            
        except Exception as e:
            self.logger.error(f"创建标准格式DataFrame失败: {str(e)}")
            return None
    
    def save_to_database(self, df: pd.DataFrame, account_number: str, account_name: str) -> int:
        """将交易数据保存到SQLite数据库
        
        Args:
            df: 包含交易数据的DataFrame
            account_number: 账户号码
            account_name: 账户名称
            
        Returns:
            导入的记录数量
        """
        if df is None or df.empty:
            self.logger.warning(f"没有数据可保存: {account_number}")
            print("没有数据可保存")
            return 0
            
        # 数据验证 - 严格校验所有字段
        validation_result = self.validate_transaction_data(df)
        if not validation_result['valid']:
            self.logger.error(f"数据验证未通过: {validation_result['reason']}, 账号: {account_number}")
            return 0
        
        # 检查是否有账号字段 (已在验证方法中检查，这里保留作为额外安全检查)
        if 'account_number' not in df.columns or df['account_number'].isnull().all():
            self.logger.warning(f"数据中不包含有效的账号字段，无法导入到数据库")
            return 0
        
        # 转换日期格式
        if 'transaction_date' in df.columns:
            df['transaction_date'] = pd.to_datetime(df['transaction_date'], errors='coerce')
            
        # 去除完全相同的记录
        df = df.drop_duplicates()
        
        # 检测可能的重复交易（同一天、相同金额但对手方略有不同）
        if 'amount' in df.columns:
            potential_duplicates = df[df.duplicated(subset=['transaction_date', 'amount'], keep=False)]
            if not potential_duplicates.empty:
                self.logger.warning(f"检测到{len(potential_duplicates)}条潜在重复交易（相同日期和金额）")
                for _, group in potential_duplicates.groupby(['transaction_date', 'amount']):
                    self.logger.debug(f"潜在重复: {group[['transaction_date', 'amount', 'counterparty']].to_dict('records')}")
        
        # 检测完全相同的交易（除了row_index外所有字段都相同）
        columns_to_check = [col for col in df.columns if col != 'row_index']
        if len(columns_to_check) > 0:
            # 找出除row_index外其他所有字段都相同的记录
            exact_duplicates = df[df.duplicated(subset=columns_to_check, keep=False)]
            if not exact_duplicates.empty:
                self.logger.warning(f"检测到{len(exact_duplicates)}条重复交易（除row_index外所有数据相同）")
                for _, group in exact_duplicates.groupby(columns_to_check):
                    self.logger.debug(f"完全重复: {group[['transaction_date', 'amount', 'counterparty', 'row_index']].to_dict('records')}")
                    # 仅保留row_index值最小的一条记录（通常是原始Excel中最先出现的记录）
                    duplicate_indices = group.index[1:]  # 保留第一条，删除其余记录
                    df = df.drop(duplicate_indices)
                    self.logger.info(f"移除了{len(duplicate_indices)}条重复交易记录")
        
        # 添加银行名称列
        if 'bank' not in df.columns:
            # 使用配置中的显示名称
            if self.bank_config and "display_name" in self.bank_config:
                display_bank_name = self.bank_config["display_name"]
            else:
                # 使用提取器的银行名称
                bank_name_map = {
                    'CCB': '建设银行',
                    'ICBC': '工商银行',
                    'BOC': '中国银行',
                    'ABC': '农业银行',
                    'BOCOM': '交通银行',
                    'CMB': '招商银行'
                }
                display_bank_name = bank_name_map.get(self.bank_code.upper(), self.bank_code)
            
            df['bank'] = display_bank_name
            self.logger.info(f"添加银行名称列: {display_bank_name}")
        
        # 根据账号分组导入到数据库
        total_imported = 0
        account_groups = df.groupby('account_number')
        
        for account_number, account_df in account_groups:
            try:
                # 获取银行代码
                bank_code = self.bank_code.upper()
                bank_name = self.get_bank_name()
                
                # 1. 先插入银行数据
                try:
                    self.db_manager.init_db()  # 确保表结构和基础数据存在
                    # 确保银行记录存在
                    bank_id = self.db_manager.get_or_create_bank(bank_code, bank_name)
                    self.logger.info(f"获取银行ID成功: {bank_code} -> {bank_id}")
                except Exception as e:
                    self.logger.error(f"获取银行ID时出错: {str(e)}")
                    # 如果无法获取银行ID，直接返回失败，不使用默认值
                    return 0
                
                # 导入到数据库
                batch_id = f"import_{datetime.now().strftime('%Y%m%d%H%M%S')}_{Path(account_number).stem}"
                imported_count = self.db_manager.import_transactions(account_df, bank_id, batch_id)
                
                if imported_count > 0:
                    self.logger.info(f"成功导入账号 {account_number} 的 {imported_count} 条交易记录到数据库")
                    total_imported += imported_count
                else:
                    self.logger.warning(f"账号 {account_number} 的交易记录导入失败或无新数据")
            except Exception as e:
                self.logger.error(f"处理账号 {account_number} 时出错: {str(e)}")
                continue
        
        self.logger.info(f"总共导入 {total_imported} 条交易记录到数据库")
        return total_imported
    
    def find_excel_files(self, upload_dir: str) -> List[str]:
        """查找给定目录中的Excel文件"""
        # 支持的Excel文件类型
        excel_patterns = ['*.xlsx', '*.xls']
        
        excel_files = []
        for pattern in excel_patterns:
            excel_files.extend(glob.glob(os.path.join(upload_dir, pattern)))
        
        return excel_files
    
    def extract_transactions(self, file_path: str) -> Optional[pd.DataFrame]:
        """从文件中提取交易明细，由子类实现"""
        raise NotImplementedError("子类必须实现extract_transactions方法")
    
    def standardize_row_index(self, df: pd.DataFrame, 
                             header_row_idx: Optional[int] = None, 
                             id_column_name: str = "row_index") -> pd.Series:
        """标准化处理行号，确保每条记录有唯一的row_index
        
        Args:
            df: 要处理的DataFrame
            header_row_idx: 表头行索引，如果提供，则用于计算实际Excel行号
            id_column_name: 表示序号的列名，默认为"row_index"
            
        Returns:
            处理后的row_index Series
        """
        if id_column_name in df.columns and not df[id_column_name].isnull().all():
            # 如果有序号列，直接使用
            return df[id_column_name]
        else:
            # 如果没有序号列，使用DataFrame的索引
            if header_row_idx is not None:
                # 如果提供了表头行索引，加上偏移量得到实际Excel行号
                return df.index + header_row_idx + 2  # +2是因为Excel从1开始计数，且表头行之后开始是数据行
            else:
                # 否则直接使用索引作为row_index
                return df.index
    
    def extract_account_info(self, df: pd.DataFrame) -> Tuple[str, str]:
        """从DataFrame中提取账户信息，可由子类重写
        
        Args:
            df: 包含账户信息的DataFrame
            
        Returns:
            tuple: (account_name, account_number) 元组，如果无法提取则返回("", "")
        """
        # 默认实现尝试从DataFrame中提取账号信息
        account_name = ""
        account_number = ""
        
        if df is not None and not df.empty and 'account_number' in df.columns:
            account_number = df['account_number'].iloc[0]
            
        if df is not None and not df.empty and 'account_name' in df.columns:
            account_name = df['account_name'].iloc[0]
            
        return account_name, account_number
    
    def can_process_file(self, file_path: str) -> bool:
        """检查是否可以处理给定的文件，子类应重写此方法"""
        # 默认实现返回False，子类应根据文件特征判断是否可以处理
        return False
    
    def process_files(self, upload_dir: str) -> List[Dict[str, Any]]:
        """处理上传目录中的所有Excel文件
        
        Args:
            upload_dir: 上传文件目录
            
        Returns:
            处理结果信息列表
        """
        # 查找所有Excel文件
        excel_files = self.find_excel_files(upload_dir)
        if not excel_files:
            self.logger.warning(f"在目录 {upload_dir} 中未找到Excel文件")
            return []
        
        # 处理结果
        processed_files = []
        
        # 遍历处理每个文件
        for file_path in excel_files:
            try:
                # 检查是否能处理此文件
                if not self.can_process_file(file_path):
                    self.logger.info(f"跳过不支持的文件: {file_path}")
                    continue
                
                # 提取交易明细
                self.logger.info(f"开始处理文件: {file_path}")
                transactions_df = self.extract_transactions(file_path)
                
                if transactions_df is None or transactions_df.empty:
                    self.logger.warning(f"未能提取任何交易明细: {file_path}")
                    continue
                
                # 记录原始行数
                original_row_count = len(transactions_df)
                
                # 提取账户信息
                account_name, account_number = self.extract_account_info(transactions_df)
                
                # 保存到数据库
                try:
                    record_count = self.save_to_database(transactions_df, account_number, account_name)
                    self.logger.info(f"成功保存 {record_count} 条交易记录到数据库")
                    
                    processed_files.append({
                        'file': os.path.basename(file_path),
                        'bank': self.get_bank_name(),
                        'record_count': record_count,
                        'original_row_count': original_row_count
                    })
                except Exception as e:
                    self.logger.error(f"保存数据到数据库时出错: {str(e)}")
                    processed_files.append({
                        'file': os.path.basename(file_path),
                        'bank': self.get_bank_name(),
                        'record_count': 0,
                        'original_row_count': original_row_count
                    })
            
            except Exception as e:
                self.logger.error(f"处理文件 {file_path} 时出错: {str(e)}")
                self.logger.error(f"错误详情: {traceback.format_exc()}")
        
        return processed_files
    
    def validate_transaction_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """对交易数据进行严格校验
        
        Args:
            df: 标准格式的交易数据DataFrame
            
        Returns:
            dict: 包含validation_result['valid']和validation_result['reason']的字典
        """
        result = {'valid': True, 'reason': ''}
        
        # 1. 检查DataFrame是否为空
        if df is None or df.empty:
            result['valid'] = False
            result['reason'] = '数据为空'
            return result
            
        # 2. 检查必要字段是否存在
        required_fields = ['transaction_date', 'amount', 'account_number']
        for field in required_fields:
            if field not in df.columns:
                result['valid'] = False
                result['reason'] = f'缺少必要字段: {field}'
                return result
                
        # 3. 检查必要字段是否都有有效值
        # 交易日期
        if df['transaction_date'].isnull().any():
            result['valid'] = False
            result['reason'] = '存在交易记录缺少交易日期'
            return result
            
        # 交易金额
        if df['amount'].isnull().any():
            result['valid'] = False
            result['reason'] = '存在交易记录缺少交易金额'
            return result
            
        # 检查是否有无效(0)金额
        if (df['amount'] == 0).any():
            result['valid'] = False
            result['reason'] = '存在金额为0的交易记录'
            return result
            
        # 账号
        if df['account_number'].isnull().any():
            result['valid'] = False
            result['reason'] = '存在交易记录缺少账号'
            return result
            
        # 4. 检查其他字段是否有有效值
        # 交易类型
        if 'transaction_type' in df.columns and df['transaction_type'].isnull().any():
            result['valid'] = False
            result['reason'] = '存在交易记录缺少交易类型'
            return result
            
        # 5. 检查日期格式
        try:
            pd.to_datetime(df['transaction_date'], errors='raise')
        except Exception:
            result['valid'] = False
            result['reason'] = '交易日期格式无效'
            return result
            
        # 6. 检查余额是否为数值
        if 'balance' in df.columns and not pd.api.types.is_numeric_dtype(df['balance']):
            result['valid'] = False
            result['reason'] = '余额不是数值类型'
            return result
            
        # 7. 检查金额是否为数值
        if not pd.api.types.is_numeric_dtype(df['amount']):
            result['valid'] = False
            result['reason'] = '金额不是数值类型'
            return result
            
        # 所有检查都通过
        return result
    
    def process_file(self, file_path: str) -> Dict[str, Any]:
        """处理单个文件，提取交易数据并保存到数据库
        
        Args:
            file_path: 文件路径
            
        Returns:
            dict: 处理结果，包含如下字段:
                - success: 是否成功
                - message: 处理消息
                - record_count: 提取的记录数量
                - account_number: 账户号码
                - bank_name: 银行名称
        """
        self.logger.info(f"处理文件: {file_path}")
        
        try:
            # 检查文件是否可以处理
            if not self.can_process_file(file_path):
                self.logger.warning(f"该文件不适用于 {self.get_bank_name()} 提取器: {file_path}")
                return {
                    'success': False,
                    'message': f"该文件不适用于 {self.get_bank_name()} 提取器",
                    'record_count': 0
                }
                
            # 读取Excel文件
            try:
                df = self.read_excel_file(file_path)
                if df is None or df.empty:
                    self.logger.warning(f"读取文件失败或文件为空: {file_path}")
                    return {
                        'success': False,
                        'message': "读取文件失败或文件为空",
                        'record_count': 0
                    }
            except Exception as e:
                self.logger.error(f"读取Excel文件时出错: {str(e)}")
                return {
                    'success': False,
                    'message': f"读取Excel文件时出错: {str(e)}",
                    'record_count': 0
                }
                
            # 提取账户信息
            try:
                account_name, account_number = self.extract_account_info(df)
            except Exception as e:
                self.logger.error(f"提取账户信息时出错: {str(e)}")
                account_name = "unknown"
                account_number = "unknown"
                
            # 提取交易数据
            try:
                transactions_df = self.extract_transactions(df)
                if transactions_df is None or transactions_df.empty:
                    self.logger.warning(f"未提取到任何交易数据: {file_path}")
                    return {
                        'success': False,
                        'message': "未提取到任何交易数据",
                        'record_count': 0,
                        'account_number': account_number,
                        'bank_name': self.get_bank_name()
                    }
            except Exception as e:
                self.logger.error(f"提取交易数据时出错: {str(e)}")
                return {
                    'success': False,
                    'message': f"提取交易数据时出错: {str(e)}",
                    'record_count': 0,
                    'account_number': account_number,
                    'bank_name': self.get_bank_name()
                }
                
            # 保存到数据库
            try:
                record_count = self.save_to_database(transactions_df, account_number, account_name)
                self.logger.info(f"成功保存 {record_count} 条交易记录到数据库")
                
                return {
                    'success': True,
                    'message': "处理成功",
                    'record_count': record_count,
                    'account_number': account_number,
                    'bank_name': self.get_bank_name()
                }
            except Exception as e:
                self.logger.error(f"保存数据到数据库时出错: {str(e)}")
                return {
                    'success': False,
                    'message': f"保存数据到数据库时出错: {str(e)}",
                    'record_count': 0,
                    'account_number': account_number,
                    'bank_name': self.get_bank_name()
                }
                
        except Exception as e:
            self.logger.error(f"处理文件时出错: {str(e)}")
            self.logger.error(traceback.format_exc())
            return {
                'success': False,
                'message': f"处理文件时出错: {str(e)}",
                'record_count': 0,
                'bank_name': self.get_bank_name()
            }
    
    def read_excel_file(self, file_path: str) -> pd.DataFrame:
        """读取Excel文件，返回DataFrame
        
        Args:
            file_path: Excel文件路径
            
        Returns:
            pandas.DataFrame: 读取的数据
        """
        try:
            self.logger.info(f"读取Excel文件: {file_path}")
            
            # 尝试不同的sheet和header配置
            try:
                # 首先尝试自动检测
                df = pd.read_excel(file_path)
                
                if df is not None and not df.empty:
                    return df
                    
                # 如果自动检测失败，尝试不同的sheet和header配置
                for sheet_name in [0, 'Sheet1', 'Sheet']:
                    for header_row in [0, 1, 2, 3]:
                        try:
                            df = pd.read_excel(file_path, sheet_name=sheet_name, header=header_row)
                            if df is not None and not df.empty:
                                self.logger.info(f"成功使用sheet={sheet_name}, header={header_row}读取文件")
                                return df
                        except Exception:
                            continue
            except Exception as e:
                self.logger.error(f"读取Excel文件时出错: {str(e)}")
                
            # 如果所有尝试都失败，返回None
            self.logger.warning(f"无法读取Excel文件: {file_path}")
            return None
            
        except Exception as e:
            self.logger.error(f"读取Excel文件时出错: {str(e)}")
            self.logger.error(traceback.format_exc())
            return None 