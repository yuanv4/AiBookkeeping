import pandas as pd
import re
import os
import glob
import logging
from datetime import datetime
from pathlib import Path

from bank_transaction_extractor import BankTransactionExtractor

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
    
    def extract_transactions(self, file_path, data_dir):
        """提取交易数据"""
        try:
            # 读取Excel文件
            df = pd.read_excel(file_path)
            
            # 提取账户信息
            account_info = self.extract_account_info(df)
            if not account_info:
                logger.error("无法提取账户信息")
                return None
                
            # 提取交易记录
            transactions = self.extract_transaction_records(df)
            if not transactions:
                logger.error("无法提取交易记录")
                return None
                
            # 创建结果DataFrame
            result_df = pd.DataFrame(transactions)
            
            # 添加账户信息
            result_df['account_name'] = account_info['account_name']
            result_df['account_number'] = account_info['account_number']
            result_df['bank_name'] = self.bank_name
            
            # 保存到数据库
            try:
                # 获取数据库连接
                conn = self.db_manager.get_connection()
                if conn:
                    # 导入数据到数据库
                    success = self.db_manager.import_dataframe(result_df, conn=conn)
                    if success:
                        logger.info(f"成功将{len(result_df)}条交易记录保存到数据库")
                        return {
                            'bank': self.bank_name,
                            'account_name': account_info['account_name'],
                            'account_number': account_info['account_number'],
                            'record_count': len(result_df)
                        }
                    else:
                        logger.error("保存到数据库失败")
                else:
                    logger.error("无法获取数据库连接")
            except Exception as e:
                logger.error(f"保存到数据库时出错: {e}")
                import traceback
                logger.error(traceback.format_exc())
            
            return None
            
        except Exception as e:
            logger.error(f"提取交易数据时出错: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
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

def get_bank_name_from_filename(file_path):
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

def save_to_csv(df, file_path, data_dir):
    """将DataFrame保存为CSV文件，使用文件名作为CSV文件名"""
    if df is None or df.empty:
        logger.warning(f"没有数据可保存: {file_path}")
        return
    
    # 从文件路径中提取文件名（不带扩展名）
    file_name = Path(file_path).stem
    
    # 创建CSV文件名 - 使用原始文件名作为基础
    csv_file_name = f"{file_name}.csv"
    output_path = data_dir / csv_file_name
    
    try:
        # 排序，让最新的交易排在前面
        if '交易日期' in df.columns:
            df['交易日期'] = pd.to_datetime(df['交易日期'], errors='coerce')
            df = df.sort_values('交易日期', ascending=False)
        
        # 去除当前数据中的完全相同的记录
        df = df.drop_duplicates()
        
        # 保存到CSV文件
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
        logger.info(f"已保存 {len(df)} 条交易记录到: {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"保存CSV文件时出错: {e}")
        return None

def main():
    try:
        logger.info("开始处理银行交易明细")
        
        # 获取脚本的根目录
        root_dir = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        # 指定uploads子目录和数据输出目录
        upload_dir = root_dir / "uploads"
        data_dir = root_dir / "data" / "transactions"
        
        # 确保数据目录存在
        data_dir.mkdir(exist_ok=True, parents=True)
        
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
        
        # 获取已存在的CSV文件名(不含扩展名)列表，用于检查是否已处理过
        existing_csv_files = [Path(f).stem for f in data_dir.glob('*.csv')]
        
        # 处理结果统计
        processed_files = []
        total_records = 0
        
        # 处理每个Excel文件并单独保存
        for excel_file in excel_files:
            # 检查是否已经处理过此文件
            if excel_file.stem in existing_csv_files:
                logger.info(f"文件 {excel_file.name} 已经处理过，跳过")
                continue
                
            extractor = CMBTransactionExtractor()
            result_df = extractor.extract_transactions(excel_file)
            if result_df is not None and not result_df.empty:
                output_path = save_to_csv(result_df, excel_file, data_dir)
                if output_path:
                    processed_files.append({
                        'input_file': str(excel_file),
                        'output_file': str(output_path),
                        'record_count': len(result_df)
                    })
                    total_records += len(result_df)
        
        # 输出处理结果汇总
        if processed_files:
            logger.info(f"已处理 {len(processed_files)} 个文件，共 {total_records} 条交易记录")
            logger.info("处理结果汇总:")
            for i, file_info in enumerate(processed_files, 1):
                logger.info(f"  {i}. {Path(file_info['input_file']).name} -> {Path(file_info['output_file']).name} ({file_info['record_count']} 条记录)")
        else:
            logger.warning("没有找到符合条件的数据")
        
        logger.info("银行交易明细处理完成")
        
        # 在控制台显示保存的数据文件路径
        print("\n保存的交易数据文件:")
        for file_info in processed_files:
            print(f"- {file_info['output_file']}")
        
    except Exception as e:
        logger.error(f"处理过程中发生未预期的错误: {e}")

if __name__ == "__main__":
    main() 