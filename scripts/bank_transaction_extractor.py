import pandas as pd
import re
import os
import glob
import logging
from datetime import datetime
from pathlib import Path
import sys

# 添加项目根目录到PYTHONPATH，以便导入相关模块
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
if root_dir not in sys.path:
    sys.path.append(root_dir)

# 导入数据库管理模块
from scripts.db_manager import DBManager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class BankTransactionExtractor:
    """银行交易明细提取器基类"""
    
    def __init__(self, bank_name):
        """初始化提取器
        
        Args:
            bank_name: 银行名称，用于日志和文件名
        """
        self.bank_name = bank_name
        self.logger = logging.getLogger(f'{bank_name}_extractor')
        self.db_manager = DBManager()
    
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
    
    def save_to_database(self, df, file_path):
        """将交易数据保存到SQLite数据库
        
        Args:
            df: 包含交易数据的DataFrame
            file_path: 原始文件路径，用于日志记录
            
        Returns:
            导入的记录数量
        """
        if df is None or df.empty:
            self.logger.warning(f"没有数据可保存: {file_path}")
            print("没有数据可保存")
            return 0
        
        # 检查是否有账号字段
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
            # 使用提取器的银行名称
            bank_name_map = {
                'CCB': '建设银行',
                'ICBC': '工商银行',
                'BOC': '中国银行',
                'ABC': '农业银行',
                'BOCOM': '交通银行',
                'CMB': '招商银行'
            }
            display_bank_name = bank_name_map.get(self.bank_name.upper(), self.bank_name)
            df['bank'] = display_bank_name
            self.logger.info(f"添加银行名称列: {display_bank_name}")
        
        # 根据账号分组导入到数据库
        total_imported = 0
        account_groups = df.groupby('account_number')
        
        for account_number, account_df in account_groups:
            try:
                # 获取银行代码
                bank_code = self.bank_name.upper()
                bank_name = bank_name_map.get(bank_code, self.bank_name)
                
                # 1. 先插入银行数据
                try:
                    self.db_manager.init_db()  # 确保表结构和基础数据存在
                    # 确保银行记录存在
                    bank_id = self.db_manager.get_or_create_bank(bank_code, bank_name)
                    self.logger.info(f"获取银行ID成功: {bank_code} -> {bank_id}")
                except Exception as e:
                    self.logger.error(f"获取银行ID时出错: {str(e)}")
                    # 如果无法获取银行ID，设置为1（假设ID=1的银行记录已存在）
                    bank_id = 1
                    self.logger.warning(f"使用默认银行ID: {bank_id}")
                
                # 导入到数据库
                batch_id = f"import_{datetime.now().strftime('%Y%m%d%H%M%S')}_{Path(file_path).stem}"
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
        
    def find_excel_files(self, upload_dir):
        """查找给定目录中的Excel文件"""
        # 支持的Excel文件类型
        excel_patterns = ['*.xlsx', '*.xls']
        
        excel_files = []
        for pattern in excel_patterns:
            excel_files.extend(glob.glob(os.path.join(upload_dir, pattern)))
        
        return excel_files
    
    def extract_transactions(self, file_path):
        """从文件中提取交易明细，由子类实现"""
        raise NotImplementedError("子类必须实现extract_transactions方法")
    
    def standardize_row_index(self, df, header_row_idx=None, id_column_name="row_index"):
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
                return df.index + header_row_idx + 1
            else:
                # 否则直接使用索引作为row_index
                return df.index
    
    def extract_account_info(self, df):
        """从DataFrame中提取账户信息，可由子类重写"""
        # 默认实现是从df中获取账号字段的第一个值
        if df is not None and not df.empty and 'account_number' in df.columns:
            account_number = df['account_number'].iloc[0]
            return {'account_number': account_number}
        return None
    
    def can_process_file(self, file_path):
        """检查是否可以处理给定的文件，由子类实现"""
        # 默认实现返回False，子类应根据文件特征判断是否可以处理
        return False
    
    def process_files(self, upload_dir, data_dir=None):
        """处理上传目录中的所有Excel文件
        
        Args:
            upload_dir: 上传文件目录
            data_dir: 已弃用参数，保留是为了向后兼容
            
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
                
                # 保存提取的交易明细到数据库
                record_count = self.save_to_database(transactions_df, file_path)
                
                if record_count > 0:
                    # 添加处理结果
                    processed_files.append({
                        'file': os.path.basename(file_path),
                        'bank': self.bank_name,
                        'record_count': record_count,
                        'original_row_count': original_row_count
                    })
                    self.logger.info(f"成功处理文件: {file_path}，导入 {record_count} 条交易记录")
                else:
                    self.logger.warning(f"处理文件但未导入新记录: {file_path}")
            
            except Exception as e:
                self.logger.error(f"处理文件 {file_path} 时出错: {str(e)}")
                self.logger.error(f"错误详情: {logging.traceback.format_exc()}")
        
        return processed_files
    
    @staticmethod
    def auto_detect_bank_and_process(upload_dir, data_dir=None):
        """自动检测银行类型并处理交易数据
        
        Args:
            upload_dir: 上传文件目录
            data_dir: 已弃用参数，保留是为了向后兼容
            
        Returns:
            处理结果信息列表
        """
        # 查找所有Excel文件
        excel_patterns = ['*.xlsx', '*.xls']
        excel_files = []
        
        for pattern in excel_patterns:
            excel_files.extend(glob.glob(os.path.join(upload_dir, pattern)))
        
        if not excel_files:
            logging.warning(f"在目录 {upload_dir} 中未找到Excel文件")
            return []
        
        # 导入所有银行的提取器
        # 由于循环导入问题，这里使用动态导入
        from scripts.cmb_transaction_extractor import CMBTransactionExtractor
        from scripts.ccb_transaction_extractor import CCBTransactionExtractor
        
        # 所有可用的提取器实例
        extractors = [
            CMBTransactionExtractor(),
            CCBTransactionExtractor(),
            # 在这里添加更多银行的提取器
        ]
        
        # 处理结果
        all_processed_files = []
        
        # 遍历处理每个文件
        for file_path in excel_files:
            logging.info(f"尝试自动检测并处理文件: {file_path}")
            file_processed = False
            
            # 尝试所有提取器
            for extractor in extractors:
                if extractor.can_process_file(file_path):
                    try:
                        # 提取交易明细
                        logging.info(f"使用 {extractor.bank_name} 提取器处理文件: {file_path}")
                        transactions_df = extractor.extract_transactions(file_path)
                        
                        if transactions_df is None or transactions_df.empty:
                            logging.warning(f"使用 {extractor.bank_name} 提取器未能提取任何交易明细: {file_path}")
                            continue
                            
                        # 记录原始行数
                        original_row_count = len(transactions_df)
                        
                        # 保存提取的交易明细到数据库
                        record_count = extractor.save_to_database(transactions_df, file_path)
                        
                        if record_count > 0:
                            # 添加处理结果
                            all_processed_files.append({
                                'file': os.path.basename(file_path),
                                'bank': extractor.bank_name,
                                'record_count': record_count,
                                'original_row_count': original_row_count
                            })
                            logging.info(f"成功使用 {extractor.bank_name} 提取器处理文件: {file_path}，导入 {record_count} 条交易记录")
                            file_processed = True
                            break
                        else:
                            logging.warning(f"使用 {extractor.bank_name} 提取器处理文件但未导入新记录: {file_path}")
                    
                    except Exception as e:
                        logging.error(f"使用 {extractor.bank_name} 提取器处理文件 {file_path} 时出错: {str(e)}")
                        logging.error(f"错误详情: {logging.traceback.format_exc()}")
            
            if not file_processed:
                logging.warning(f"未找到合适的提取器处理文件: {file_path}")
        
        return all_processed_files
    
    def run(self):
        """运行交易明细提取器"""
        try:
            # 获取上传目录
            root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            upload_dir = os.path.join(root_dir, 'uploads')
            
            # 确保目录存在
            os.makedirs(upload_dir, exist_ok=True)
            
            # 处理上传目录中的文件
            processed_files = self.process_files(upload_dir)
            
            if processed_files:
                # 统计处理结果
                total_records = sum(f['record_count'] for f in processed_files)
                self.logger.info(f"处理完成。共处理 {len(processed_files)} 个文件，提取 {total_records} 条交易记录。")
                
                # 按银行分组统计
                bank_summary = {}
                for file_info in processed_files:
                    bank = file_info['bank']
                    if bank not in bank_summary:
                        bank_summary[bank] = {'files': 0, 'records': 0}
                    bank_summary[bank]['files'] += 1
                    bank_summary[bank]['records'] += file_info['record_count']
                
                self.logger.info("按银行分组统计：")
                for bank, stats in bank_summary.items():
                    self.logger.info(f"- {bank}: {stats['files']} 个文件, {stats['records']} 条记录")
                
                return processed_files
            else:
                self.logger.info("处理完成，但未能成功提取任何交易记录。请确保文件格式正确。")
                return []
                
        except Exception as e:
            self.logger.error(f"运行过程中出错: {str(e)}")
            self.logger.error(f"错误详情: {logging.traceback.format_exc()}")
            return []
    
    @staticmethod
    def run_auto_detect():
        """运行自动检测银行类型并处理交易数据"""
        try:
            # 获取上传目录
            root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            upload_dir = os.path.join(root_dir, 'uploads')
            
            # 确保目录存在
            os.makedirs(upload_dir, exist_ok=True)
            
            # 自动检测并处理
            processed_files = BankTransactionExtractor.auto_detect_bank_and_process(upload_dir)
            
            if processed_files:
                # 统计处理结果
                total_records = sum(f['record_count'] for f in processed_files)
                logging.info(f"处理完成。共处理 {len(processed_files)} 个文件，提取 {total_records} 条交易记录。")
                
                # 按银行分组统计
                bank_summary = {}
                for file_info in processed_files:
                    bank = file_info['bank']
                    if bank not in bank_summary:
                        bank_summary[bank] = {'files': 0, 'records': 0}
                    bank_summary[bank]['files'] += 1
                    bank_summary[bank]['records'] += file_info['record_count']
                
                logging.info("按银行分组统计：")
                for bank, stats in bank_summary.items():
                    logging.info(f"- {bank}: {stats['files']} 个文件, {stats['records']} 条记录")
                
                return processed_files
            else:
                logging.info("处理完成，但未能成功提取任何交易记录。请确保文件格式正确。")
                return []
                
        except Exception as e:
            logging.error(f"运行过程中出错: {str(e)}")
            logging.error(f"错误详情: {traceback.format_exc()}")
            return []
    
    def get_bank_keyword(self):
        """获取银行关键词，用于文件匹配"""
        return self.bank_name

# 程序入口点
if __name__ == "__main__":
    BankTransactionExtractor.run_auto_detect() 