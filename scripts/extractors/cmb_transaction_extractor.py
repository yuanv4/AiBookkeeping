import pandas as pd
import re
import os
import glob
import logging
from datetime import datetime
from pathlib import Path
import sys

# 添加项目根目录到PYTHONPATH以解决导入问题
current_dir = os.path.dirname(os.path.abspath(__file__))
scripts_dir = os.path.dirname(current_dir)
root_dir = os.path.dirname(scripts_dir)
if root_dir not in sys.path:
    sys.path.append(root_dir)
if scripts_dir not in sys.path:
    sys.path.append(scripts_dir)

from scripts.extractors.bank_transaction_extractor import BankTransactionExtractor

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('cmb_extractor')

class CMBTransactionExtractor(BankTransactionExtractor):
    """招商银行交易明细提取器"""
    
    def __init__(self):
        """初始化招商银行交易提取器"""
        super().__init__('CMB')
    
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
            
            # 如果能提取到账户信息，说明是招商银行的交易明细
            if account_name and account_number:
                self.logger.info(f"成功识别为招商银行交易明细 - 户名: {account_name}, 账号: {account_number}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"检查文件时出错: {e}")
            return False
    
    def is_date_format(self, value):
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
    
    def extract_account_info(self, df):
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
    
    def extract_transactions(self, file_path):
        """提取交易数据"""
        try:
            # 先尝试读取Excel文件获取基本信息
            df_info = pd.read_excel(file_path, header=None, nrows=20)
            
            # 提取账户信息
            account_name, account_number = self.extract_account_info(df_info)
            if not account_name or not account_number:
                self.logger.error("无法提取账户信息")
                return None
            
            # 查找标题行
            header_row_idx = self.find_header_row(df_info)
            if header_row_idx is None:
                self.logger.error("无法找到标题行")
                return None
                
            self.logger.info(f"找到标题行，索引为 {header_row_idx}")
            
            # 重新读取Excel文件，正确处理标题行
            try:
                # 尝试使用多级标题（招商银行特殊格式）
                df = pd.read_excel(file_path, header=[header_row_idx, header_row_idx+1])
                self.logger.info(f"使用多级标题格式读取数据，列名: {df.columns.tolist()}")
            except Exception as e:
                self.logger.warning(f"使用多级标题读取失败: {e}，尝试单级标题")
                # 如果多级标题读取失败，尝试使用单级标题
                df = pd.read_excel(file_path, header=header_row_idx)
                self.logger.info(f"使用单级标题格式读取数据，列名: {df.columns.tolist()}")
            
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
            
            # 处理交易日期和其他字段
            for col in df.columns:
                col_name = col[0] if isinstance(col, tuple) else col
                col_name_str = str(col_name).lower()
                
                # 日期列
                if '日期' in col_name_str or 'date' in col_name_str.lower():
                    self.logger.info(f"找到日期列: {col}")
                    result_df['transaction_date'] = df[col].apply(lambda x: self.standardize_date(x))
                    found_fields['date'] = True
                
                # 金额列
                elif '金额' in col_name_str or 'amount' in col_name_str.lower() or 'transaction' in col_name_str.lower():
                    self.logger.info(f"找到金额列: {col}")
                    result_df['amount'] = df[col].apply(lambda x: self.clean_numeric(x))
                    found_fields['amount'] = True
                
                # 余额列
                elif '余额' in col_name_str or 'balance' in col_name_str.lower():
                    self.logger.info(f"找到余额列: {col}")
                    result_df['balance'] = df[col].apply(lambda x: self.clean_numeric(x))
                
                # 交易类型列
                elif '摘要' in col_name_str or '交易类型' in col_name_str or 'type' in col_name_str.lower():
                    self.logger.info(f"找到交易类型列: {col}")
                    result_df['transaction_type'] = df[col].fillna('其他')
                
                # 交易对象列
                elif '对手' in col_name_str or '对方' in col_name_str or 'counter' in col_name_str.lower() or 'party' in col_name_str.lower():
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
            
            # 确保所有字段都有值
            # 货币默认为CNY
            if result_df['currency'].isnull().all():
                result_df['currency'] = 'CNY'
                
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
            
            # 检查日期是否全部为空，如有需要尝试从文件名提取年份
            if valid_transactions['transaction_date'].isna().all():
                self.logger.warning("所有交易记录的日期字段为空")
                # 尝试从文件名提取年份
                try:
                    file_name = os.path.basename(file_path)
                    year_match = re.search(r'(\d{4})', file_name)
                    if year_match:
                        default_date = f"{year_match.group(1)}-01-01"
                        self.logger.warning(f"未能提取有效日期，无法推断交易日期")
                        return None
                except:
                    self.logger.warning("未能提取有效日期，无法推断交易日期")
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
    
    def find_header_row(self, df):
        """查找标题行"""
        # 尝试在前20行找到包含标题关键字的行
        for idx in range(min(20, len(df))):
            row = df.iloc[idx]
            # 将行转为字符串后合并
            row_text = " ".join([str(val) for val in row if pd.notna(val)]).lower()
            # 检查是否包含常见的标题关键字
            if any(keyword in row_text for keyword in ["记账日期", "交易日期", "账务日期", "交易金额", "发生额"]):
                return idx
        return None
    
    def standardize_date(self, date_value):
        """将各种日期格式标准化为YYYY-MM-DD"""
        if pd.isna(date_value):
            return None
        
        # 已经是datetime对象
        if isinstance(date_value, datetime):
            # 确保日期不在未来
            today = datetime.today()
            if date_value > today:
                self.logger.warning(f"发现未来日期: {date_value}，替换为当前日期")
                return today.strftime('%Y-%m-%d')
            return date_value.strftime('%Y-%m-%d')
        
        # 处理字符串格式
        if isinstance(date_value, str):
            # 检查是否包含关键词：这些可能是列标题，不是真正的日期
            if any(keyword in date_value.lower() for keyword in ['date', 'amount', 'transaction', 'balance']):
                self.logger.debug(f"跳过日期列标题: {date_value}")
                return None
                
            # 已经是标准格式
            if re.match(r'^\d{4}-\d{2}-\d{2}$', date_value):
                # 检查是否是未来日期
                try:
                    parsed_date = datetime.strptime(date_value, '%Y-%m-%d')
                    if parsed_date > datetime.today():
                        self.logger.warning(f"发现未来日期: {date_value}，替换为当前日期")
                        return datetime.today().strftime('%Y-%m-%d')
                except:
                    pass
                return date_value
            
            # 处理YYYY/MM/DD格式
            if re.match(r'^\d{4}/\d{1,2}/\d{1,2}$', date_value):
                parts = date_value.split('/')
                year = parts[0]
                month = parts[1].zfill(2)
                day = parts[2].zfill(2)
                date_str = f"{year}-{month}-{day}"
                
                # 检查是否是未来日期
                try:
                    parsed_date = datetime.strptime(date_str, '%Y-%m-%d')
                    if parsed_date > datetime.today():
                        self.logger.warning(f"发现未来日期: {date_str}，替换为当前日期")
                        return datetime.today().strftime('%Y-%m-%d')
                except:
                    pass
                return date_str
        
        # 其他情况，尝试转换为datetime然后格式化
        try:
            parsed_date = pd.to_datetime(date_value)
            # 检查是否是未来日期
            if parsed_date > pd.Timestamp.today():
                self.logger.warning(f"发现未来日期: {parsed_date}，替换为当前日期")
                return pd.Timestamp.today().strftime('%Y-%m-%d')
            return parsed_date.strftime('%Y-%m-%d')
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
                self.logger.warning(f"无法转换为数值: {value}")
                return 0.0
        
        return 0.0
    
    def get_bank_keyword(self):
        """获取银行关键字用于筛选文件"""
        return '招商银行'

def main():
    try:
        logger.info("开始处理银行交易明细")
        
        # 获取脚本的根目录
        root_dir = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        # 指定uploads子目录
        upload_dir = root_dir / "uploads"
        
        # 检查uploads目录是否存在
        if not upload_dir.exists() or not upload_dir.is_dir():
            logger.error(f"错误：{upload_dir} 目录不存在")
            return
        
        # 处理uploads目录下的所有Excel文件，排除以~$开头的临时文件
        excel_files = []
        
        # 支持多种Excel文件格式
        for ext in ['*.xlsx', '*.xls']:
            excel_files.extend(list(upload_dir.glob(ext)))
        
        # 过滤掉临时文件
        excel_files = [f for f in excel_files if not f.name.startswith('~$')]
        
        if not excel_files:
            logger.warning(f"在 {upload_dir} 目录下没有找到Excel文件")
            return
        
        logger.info(f"找到 {len(excel_files)} 个Excel文件待处理")
        
        # 处理结果统计
        processed_files = []
        total_records = 0
        
        # 处理每个Excel文件并保存到数据库
        for excel_file in excel_files:
            extractor = CMBTransactionExtractor()
            # 调用修改后的extract_transactions方法
            result_df = extractor.extract_transactions(excel_file)
            if result_df is not None and not result_df.empty:
                # 使用save_to_database方法保存到数据库
                record_count = extractor.save_to_database(result_df, excel_file)
                if record_count > 0:
                    processed_files.append({
                        'file': excel_file.name,
                        'bank': extractor.bank_name,
                        'record_count': record_count,
                        'original_row_count': len(result_df)
                    })
                    total_records += record_count
                    logger.info(f"成功导入 {excel_file.name} 的 {record_count} 条交易记录到数据库")
        
        # 输出处理结果汇总
        if processed_files:
            logger.info(f"已处理 {len(processed_files)} 个文件，共导入 {total_records} 条交易记录")
            logger.info("处理结果汇总:")
            for i, file_info in enumerate(processed_files, 1):
                logger.info(f"  {i}. {file_info['file']} -> {file_info['record_count']} 条记录")
        else:
            logger.warning("没有找到符合条件的数据")
        
        logger.info("银行交易明细处理完成")
        
    except Exception as e:
        logger.error(f"处理过程中发生未预期的错误: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main() 