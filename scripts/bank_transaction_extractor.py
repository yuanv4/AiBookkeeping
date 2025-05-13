import pandas as pd
import re
import os
import glob
import logging
from datetime import datetime
from pathlib import Path
import sys

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
    
    def get_bank_name_from_filename(self, file_path):
        """从文件名中提取银行名称"""
        file_name = Path(file_path).name.lower()
        
        if '招商银行' in file_name:
            return 'cmb'
        elif '建设银行' in file_name or 'ccb' in file_name:
            return 'ccb'
        elif '工商银行' in file_name or 'icbc' in file_name:
            return 'icbc'
        elif '农业银行' in file_name or 'abc' in file_name:
            return 'abc'
        elif '中国银行' in file_name or 'boc' in file_name:
            return 'boc'
        elif '交通银行' in file_name or 'bocom' in file_name:
            return 'bocom'
        else:
            # 从文件名中提取日期范围作为标识
            date_match = re.search(r'(\d{4}[-_]\d{2}[-_]\d{2})', file_name)
            if date_match:
                return f"bank_{date_match.group(1)}"
            return 'unknown_bank'
    
    def save_to_csv(self, df, file_path, data_dir):
        """将DataFrame保存为CSV文件，使用账号作为CSV文件名"""
        if df is None or df.empty:
            self.logger.warning(f"没有数据可保存: {file_path}")
            print("没有数据可保存")
            return
        
        # 检查是否有账号字段
        if '账号' not in df.columns or df['账号'].isnull().all():
            self.logger.warning(f"数据中不包含有效的账号字段，无法使用账号作为文件名")
            # 从文件路径中提取文件名（不带扩展名）作为备选
            file_name = Path(file_path).stem
            csv_file_name = f"{file_name}.csv"
        else:
            # 使用第一条记录的账号作为文件名
            # 多个账号的情况下，按账号分组保存
            account_groups = df.groupby('账号')
            if len(account_groups) > 1:
                processed_outputs = []
                for account_number, account_df in account_groups:
                    # 替换账号中的非法字符
                    safe_account_number = str(account_number).replace('*', 'x').replace('/', '_').replace('\\', '_')
                    # 为每个账号创建一个CSV文件
                    account_csv_name = f"{safe_account_number}.csv"
                    account_output_path = data_dir / account_csv_name
                    result = self._save_account_data(account_df, account_output_path, account_number)
                    if result:
                        processed_outputs.append(result)
                return processed_outputs if processed_outputs else None
            
            # 只有一个账号的情况
            account_number = df['账号'].iloc[0]
            if pd.isna(account_number) or not account_number:
                # 如果账号为空，使用文件名
                file_name = Path(file_path).stem
                csv_file_name = f"{file_name}.csv"
            else:
                # 使用账号作为文件名，替换非法字符
                safe_account_number = str(account_number).replace('*', 'x').replace('/', '_').replace('\\', '_')
                csv_file_name = f"{safe_account_number}.csv"
        
        output_path = data_dir / csv_file_name
        return self._save_account_data(df, output_path)
        
    def _save_account_data(self, df, output_path, account_number=None):
        """保存账户数据到CSV文件"""
        try:
            # 排序，让最新的交易排在前面
            if '交易日期' in df.columns:
                df['交易日期'] = pd.to_datetime(df['交易日期'], errors='coerce')
                df = df.sort_values('交易日期', ascending=False)
            
            # 去除完全相同的记录
            df = df.drop_duplicates()
            
            # 添加银行名称列
            if '银行' not in df.columns:
                # 使用提取器的银行名称
                bank_name_map = {
                    'CCB': '建设银行',
                    'ICBC': '工商银行',
                    'BOC': '中国银行',
                    'ABC': '农业银行',
                    'BOCOM': '交通银行',
                    'CMB': '招商银行'
                }
                display_bank_name = bank_name_map.get(self.bank_name, self.bank_name)
                df['银行'] = display_bank_name
                self.logger.info(f"添加银行名称列: {display_bank_name}")
            
            # 检查是否存在重复交易 - 如果CSV文件已存在，读取并合并
            new_records_count = len(df)
            if output_path.exists():
                try:
                    existing_df = pd.read_csv(output_path, encoding='utf-8-sig')
                    self.logger.info(f"现有CSV文件包含 {len(existing_df)} 条记录")
                    
                    # 确保日期格式一致
                    if '交易日期' in existing_df.columns:
                        existing_df['交易日期'] = pd.to_datetime(existing_df['交易日期'], errors='coerce')
                    
                    # 合并数据
                    combined_df = pd.concat([existing_df, df], ignore_index=True)
                    
                    # 去重 - 根据关键字段去重，而不仅仅是完全相同的记录
                    if '交易日期' in combined_df.columns and '交易金额' in combined_df.columns and '交易对象' in combined_df.columns:
                        # 使用日期、金额和交易对象作为去重键
                        dedup_keys = ['交易日期', '交易金额', '交易对象']
                        combined_df = combined_df.drop_duplicates(subset=dedup_keys)
                    else:
                        # 如果没有这些列，则使用所有列去重
                        combined_df = combined_df.drop_duplicates()
                    
                    # 更新要保存的数据
                    df = combined_df
                    
                    # 计算新增记录数
                    added_records = len(df) - len(existing_df)
                    self.logger.info(f"合并后有 {len(df)} 条记录，新增 {added_records} 条")
                    
                    # 如果没有新增记录，可以选择不更新文件
                    if added_records <= 0:
                        self.logger.info(f"没有新增记录，保持原文件不变")
                        print(f"没有新增记录，保持原文件不变")
                        return output_path
                except Exception as e:
                    self.logger.error(f"读取现有CSV文件时出错: {e}")
                    print(f"读取现有CSV文件时出错: {e}")
            
            # 保存到CSV文件
            df.to_csv(output_path, index=False, encoding='utf-8-sig')
            
            account_info = f"账号{account_number}" if account_number else ""
            self.logger.info(f"已保存 {len(df)} 条交易记录到: {output_path} {account_info}")
            print(f"已保存 {len(df)} 条交易记录到: {output_path} {account_info} (新增数据: {new_records_count}条)")
            return output_path
        except Exception as e:
            self.logger.error(f"保存CSV文件时出错: {e}")
            print(f"保存CSV文件时出错: {e}")
            return None
    
    def find_excel_files(self, upload_dir):
        """查找指定目录下的Excel文件
        
        Args:
            upload_dir: 上传目录路径
            
        Returns:
            匹配的Excel文件列表
        """
        excel_files = []
        
        # 支持多种Excel文件格式
        for ext in ['*.xlsx', '*.xls']:
            excel_files.extend(list(upload_dir.glob(ext)))
        
        # 过滤掉临时文件
        excel_files = [f for f in excel_files if not f.name.startswith('~$')]
        
        return excel_files
    
    def extract_transactions(self, file_path):
        """从Excel文件中提取交易记录（子类需要实现此方法）
        
        Args:
            file_path: Excel文件路径
            
        Returns:
            包含交易记录的DataFrame
        """
        raise NotImplementedError("子类必须实现此方法")
    
    def extract_account_info(self, df):
        """从DataFrame中提取户名和账号信息（子类需要实现此方法）
        
        Args:
            df: 含有Excel数据的DataFrame
            
        Returns:
            元组(account_name, account_number)
        """
        raise NotImplementedError("子类必须实现此方法")
    
    def can_process_file(self, file_path):
        """尝试判断文件是否能被当前提取器处理
        
        Args:
            file_path: Excel文件路径
            
        Returns:
            布尔值，True表示可以处理
        """
        try:
            # 读取Excel文件的第一个工作表
            df = pd.read_excel(file_path, header=None, nrows=30)  # 只读取前30行用于判断
            
            # 尝试提取账户信息
            account_name, account_number = self.extract_account_info(df)
            
            # 如果能提取到账户信息，则认为可以处理
            if account_name or account_number:
                self.logger.info(f"文件 {file_path} 可以由 {self.bank_name} 提取器处理")
                return True
            else:
                self.logger.info(f"文件 {file_path} 不能由 {self.bank_name} 提取器处理")
                return False
                
        except Exception as e:
            self.logger.warning(f"尝试处理文件 {file_path} 时出错: {e}")
            return False
    
    def process_files(self, upload_dir, data_dir):
        """处理匹配的Excel文件并提取交易记录
        
        Args:
            upload_dir: 上传目录路径
            data_dir: 数据保存目录
            
        Returns:
            处理结果列表
        """
        # 确保数据目录存在
        data_dir.mkdir(exist_ok=True, parents=True)
        
        # 查找Excel文件
        excel_files = self.find_excel_files(upload_dir)
        
        if not excel_files:
            self.logger.warning(f"未找到Excel文件")
            print(f"未找到Excel文件")
            return []
        
        self.logger.info(f"找到 {len(excel_files)} 个Excel文件")
        print(f"找到 {len(excel_files)} 个Excel文件: {[f.name for f in excel_files]}")
        
        # 获取已存在的CSV文件名(不含扩展名)列表，用于检查是否已处理过
        existing_csv_files = [Path(f).stem for f in data_dir.glob('*.csv')]
        print(f"已存在的CSV文件: {existing_csv_files}")
        
        # 处理每个Excel文件
        processed_files = []
        
        for file_path in excel_files:
            # 检查是否已经处理过此文件
            if file_path.stem in existing_csv_files:
                self.logger.info(f"文件 {file_path.name} 已经处理过，跳过")
                print(f"文件 {file_path.name} 已经处理过，跳过")
                continue
            
            # 检查此文件是否可以被当前提取器处理
            if not self.can_process_file(file_path):
                continue
            
            self.logger.info(f"开始处理文件: {file_path.name}")
            print(f"开始处理文件: {file_path.name}")
            
            # 提取交易记录
            transactions_df = self.extract_transactions(file_path)
            
            if transactions_df is not None and not transactions_df.empty:
                # 保存CSV
                csv_file = self.save_to_csv(transactions_df, file_path, data_dir)
                
                if csv_file:
                    processed_file = {
                        'file_name': file_path.name,
                        'record_count': len(transactions_df),
                        'csv_file': csv_file.name,
                        'bank': self.bank_name
                    }
                    processed_files.append(processed_file)
        
        return processed_files
    
    @staticmethod
    def auto_detect_bank_and_process(upload_dir, data_dir):
        """自动检测银行类型并处理交易数据
        
        Args:
            upload_dir: 上传目录路径
            data_dir: 数据保存目录
            
        Returns:
            处理结果列表
        """
        # 导入所有提取器子类
        # 注意：由于导入循环依赖问题，这里采用动态导入
        try:
            from ccb_transaction_extractor import CCBTransactionExtractor
        except ImportError:
            # 如果直接导入失败，尝试使用绝对导入
            try:
                from scripts.ccb_transaction_extractor import CCBTransactionExtractor
            except ImportError:
                # 获取当前脚本的路径
                import os, sys
                script_dir = os.path.dirname(os.path.abspath(__file__))
                if script_dir not in sys.path:
                    sys.path.append(script_dir)
                parent_dir = os.path.dirname(script_dir)
                if parent_dir not in sys.path:
                    sys.path.append(parent_dir)
                # 再次尝试导入
                from ccb_transaction_extractor import CCBTransactionExtractor

        # 创建提取器实例
        extractors = [
            CCBTransactionExtractor()
        ]

        # 尝试添加其他提取器，如果存在的话
        try:
            try:
                from icbc_transaction_extractor import ICBCTransactionExtractor
            except ImportError:
                from scripts.icbc_transaction_extractor import ICBCTransactionExtractor
            extractors.append(ICBCTransactionExtractor())
        except ImportError:
            pass

        try:
            try:
                from cmb_transaction_extractor import CMBTransactionExtractor
            except ImportError:
                from scripts.cmb_transaction_extractor import CMBTransactionExtractor
            extractors.append(CMBTransactionExtractor())
        except ImportError:
            pass

        # 查找所有Excel文件
        excel_files = []
        for ext in ['*.xlsx', '*.xls']:
            excel_files.extend(list(upload_dir.glob(ext)))
        
        # 过滤掉临时文件
        excel_files = [f for f in excel_files if not f.name.startswith('~$')]
        
        if not excel_files:
            print("未找到Excel文件")
            return []
        
        print(f"找到 {len(excel_files)} 个Excel文件: {[f.name for f in excel_files]}")
        
        # 获取已存在的CSV文件，避免重复处理
        existing_csv_files = [Path(f).stem for f in data_dir.glob('*.csv')]
        
        # 结果列表
        all_processed_files = []
        skipped_files = []
        
        # 每个文件，尝试每个提取器
        for file_path in excel_files:
            if file_path.stem in existing_csv_files:
                print(f"文件 {file_path.name} 已经处理过，跳过")
                # 记录跳过的文件信息
                skipped_files.append({
                    'file_name': file_path.name,
                    'reason': '已处理过'
                })
                continue
            
            print(f"尝试处理文件: {file_path.name}")
            
            # 先尝试通过文件名判断银行
            file_name_lower = file_path.name.lower()
            
            detected_extractor = None
            for extractor in extractors:
                keyword = extractor.get_bank_keyword().lower()
                if keyword in file_name_lower:
                    print(f"通过文件名检测到可能的银行: {extractor.bank_name}")
                    detected_extractor = extractor
                    break
                    
            # 如果通过文件名没找到匹配的银行，再尝试每个提取器来处理
            if detected_extractor is None:
                print("通过文件名未能检测到银行，尝试每个提取器...")
                for extractor in extractors:
                    if extractor.can_process_file(file_path):
                        print(f"通过文件内容检测到银行: {extractor.bank_name}")
                        detected_extractor = extractor
                        break
            
            # 如果找到合适的提取器，处理文件
            if detected_extractor:
                transactions_df = detected_extractor.extract_transactions(file_path)
                
                if transactions_df is not None and not transactions_df.empty:
                    # 保存CSV
                    csv_file = detected_extractor.save_to_csv(transactions_df, file_path, data_dir)
                    
                    if csv_file:
                        processed_file = {
                            'file_name': file_path.name,
                            'record_count': len(transactions_df),
                            'csv_file': csv_file.name,
                            'bank': detected_extractor.bank_name
                        }
                        all_processed_files.append(processed_file)
                        print(f"文件 {file_path.name} 处理成功，提取了 {len(transactions_df)} 条记录")
                    else:
                        print(f"文件 {file_path.name} 处理失败，保存CSV文件时出错")
                        skipped_files.append({
                            'file_name': file_path.name,
                            'reason': '保存CSV失败'
                        })
                else:
                    print(f"文件 {file_path.name} 处理失败，未能提取有效交易记录")
                    skipped_files.append({
                        'file_name': file_path.name,
                        'reason': '未能提取有效交易记录'
                    })
            else:
                print(f"文件 {file_path.name} 不能被任何提取器处理")
                skipped_files.append({
                    'file_name': file_path.name,
                    'reason': '无法识别的银行格式'
                })
        
        # 添加跳过文件的信息到返回结果
        if skipped_files:
            print(f"\n以下文件被跳过处理:")
            for skip_info in skipped_files:
                print(f"- {skip_info['file_name']}: {skip_info['reason']}")
        
        return all_processed_files
    
    def run(self):
        """运行提取器处理当前目录下的文件"""
        if len(sys.argv) > 1:
            # 如果提供了文件路径参数
            file_path = sys.argv[1]
            if os.path.exists(file_path):
                print(f"处理文件: {file_path}")
                
                # 创建数据目录
                data_dir = Path("data/transactions")
                data_dir.mkdir(exist_ok=True, parents=True)
                
                # 提取交易记录
                transactions_df = self.extract_transactions(file_path)
                
                if transactions_df is not None and not transactions_df.empty:
                    # 保存CSV
                    csv_file = self.save_to_csv(transactions_df, file_path, data_dir)
                    
                    if csv_file:
                        print(f"文件处理成功，保存为: {csv_file}")
                    else:
                        print("保存CSV文件失败")
                else:
                    print("未能提取有效交易记录")
            else:
                print(f"文件不存在: {file_path}")
        else:
            # 如果没有提供参数，处理当前目录下的所有文件
            print("处理当前目录下的所有文件")
            
            # 创建目录
            upload_dir = Path("uploads")
            data_dir = Path("data/transactions")
            data_dir.mkdir(exist_ok=True, parents=True)
            
            # 处理文件
            processed_files = self.process_files(upload_dir, data_dir)
            
            if processed_files:
                print(f"处理完成，共处理 {len(processed_files)} 个文件")
                for file_info in processed_files:
                    print(f"- {file_info['file_name']}: {file_info['record_count']} 条记录")
            else:
                print("没有找到可处理的文件")
    
    @staticmethod
    def run_auto_detect():
        """运行自动检测银行类型并处理文件"""
        # 如果有命令行参数，使用第一个参数作为目录
        if len(sys.argv) > 1:
            upload_dir_path = sys.argv[1]
        else:
            upload_dir_path = "uploads"
            
        # 第二个参数可以指定输出目录
        if len(sys.argv) > 2:
            data_dir_path = sys.argv[2]
        else:
            data_dir_path = "data/transactions"
        
        upload_dir = Path(upload_dir_path)
        data_dir = Path(data_dir_path)
        
        # 确保目录存在
        data_dir.mkdir(exist_ok=True, parents=True)
        
        # 自动检测并处理
        processed_files = BankTransactionExtractor.auto_detect_bank_and_process(upload_dir, data_dir)
        
        if processed_files:
            print(f"处理完成，共处理 {len(processed_files)} 个文件")
            for file_info in processed_files:
                print(f"- {file_info['file_name']}: {file_info['record_count']} 条记录 (银行: {file_info['bank']})")
        else:
            print("没有找到可处理的文件")
    
    def get_bank_keyword(self):
        """获取银行关键字用于筛选文件（子类需要实现此方法）"""
        return self.bank_name

# 程序入口点
if __name__ == "__main__":
    BankTransactionExtractor.run_auto_detect() 