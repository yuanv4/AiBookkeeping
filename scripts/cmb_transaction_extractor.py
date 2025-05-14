import pandas as pd
import re
import os
import glob
import logging
from datetime import datetime
from pathlib import Path

from scripts.bank_transaction_extractor import BankTransactionExtractor

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
            # 读取Excel文件
            df = pd.read_excel(file_path)
            
            # 找到标题行（招商银行通常在前几行有标题）
            header_row_idx = self.find_header_row(df)
            if header_row_idx is not None:
                # 重新读取Excel文件，使用找到的标题行
                df = pd.read_excel(file_path, header=header_row_idx)
            
            # 提取账户信息
            account_name, account_number = self.extract_account_info(df)
            if not account_name or not account_number:
                self.logger.error("无法提取账户信息")
                return None
            
            # 创建标准格式的DataFrame
            result_columns = ['交易日期', '货币', '交易金额', '账户余额', '交易类型', '交易对象', '户名', '账号', 'row_index']
            result_df = pd.DataFrame(index=df.index)
            
            # 标准化列名（根据招商银行的特定格式进行映射）
            column_mapping = self.get_column_mapping(df.columns)
            
            # 填充必要的数据
            # 处理交易日期
            if "交易日期" in column_mapping and column_mapping["交易日期"] in df.columns:
                date_column = column_mapping["交易日期"]
                result_df['交易日期'] = df[date_column].apply(self.standardize_date)
            else:
                # 使用当前日期作为默认值
                self.logger.warning(f"没有找到交易日期列，使用今天的日期")
                result_df['交易日期'] = pd.Timestamp.today().strftime('%Y-%m-%d')
            
            # 处理金额
            if "交易金额" in column_mapping and column_mapping["交易金额"] in df.columns:
                amount_column = column_mapping["交易金额"]
                result_df['交易金额'] = df[amount_column].apply(self.clean_numeric)
            else:
                result_df['交易金额'] = 0.0
            
            # 处理余额
            if "账户余额" in column_mapping and column_mapping["账户余额"] in df.columns:
                balance_column = column_mapping["账户余额"]
                result_df['账户余额'] = df[balance_column].apply(self.clean_numeric)
            else:
                result_df['账户余额'] = 0.0
            
            # 处理交易类型
            if "交易类型" in column_mapping and column_mapping["交易类型"] in df.columns:
                type_column = column_mapping["交易类型"]
                result_df['交易类型'] = df[type_column].fillna('其他')
            else:
                result_df['交易类型'] = '其他'
            
            # 处理交易对象
            if "交易对象" in column_mapping and column_mapping["交易对象"] in df.columns:
                obj_column = column_mapping["交易对象"]
                result_df['交易对象'] = df[obj_column].fillna('')
            else:
                result_df['交易对象'] = ''
            
            # 处理货币
            if "货币" in column_mapping and column_mapping["货币"] in df.columns:
                currency_column = column_mapping["货币"]
                result_df['货币'] = df[currency_column].fillna('CNY')
            else:
                result_df['货币'] = 'CNY'
            
            # 处理row_index - 使用父类的标准化方法
            result_df['row_index'] = self.standardize_row_index(df, header_row_idx)
            
            # 添加账户信息
            result_df['户名'] = account_name
            result_df['账号'] = account_number
            
            return result_df
            
        except Exception as e:
            self.logger.error(f"提取交易数据时出错: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return None
    
    def find_header_row(self, df):
        """查找标题行"""
        # 尝试在前10行找到包含标题关键字的行
        for idx in range(min(10, len(df))):
            row = df.iloc[idx]
            # 将行转为字符串后合并
            row_text = " ".join([str(val) for val in row if pd.notna(val)]).lower()
            # 检查是否包含常见的标题关键字
            if "交易日期" in row_text and ("金额" in row_text or "发生额" in row_text):
                return idx
        return None
    
    def get_column_mapping(self, columns):
        """根据招商银行的特定格式获取列名映射"""
        mapping = {}
        
        for col in columns:
            col_str = str(col).lower()
            
            if "日期" in col_str or "时间" in col_str:
                mapping["交易日期"] = col
            elif "金额" in col_str or "发生额" in col_str:
                mapping["交易金额"] = col
            elif "余额" in col_str:
                mapping["账户余额"] = col
            elif "摘要" in col_str or "描述" in col_str:
                mapping["交易类型"] = col
            elif "对方" in col_str or "收款人" in col_str or "付款人" in col_str:
                mapping["交易对象"] = col
            elif "币种" in col_str:
                mapping["货币"] = col
        
        return mapping
    
    def get_bank_keyword(self):
        """获取银行关键字用于筛选文件"""
        return '招商银行'

def standardize_date(date_value):
    """将各种日期格式标准化为YYYY-MM-DD"""
    if pd.isna(date_value):
        return None
    
    # 已经是datetime对象
    if isinstance(date_value, datetime):
        return date_value.strftime('%Y-%m-%d')
    
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
        logger.warning(f"无法标准化日期: {date_value}")
        return None

def clean_numeric(value):
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