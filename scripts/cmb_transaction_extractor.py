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
        """从招商银行Excel文件中提取交易记录"""
        self.logger.info(f"处理招商银行文件: {file_path}")
        
        try:
            # 读取Excel文件的所有工作表
            excel_file = pd.ExcelFile(file_path)
        except Exception as e:
            self.logger.error(f"打开Excel文件时出错: {e}")
            return None
        
        # 用于存储所有符合条件的数据
        all_filtered_data = []
        
        # 定义列名映射，根据实际数据调整
        column_names = {
            0: '交易日期',
            1: '货币',
            2: '交易金额',
            3: '账户余额',
            4: '交易类型',
            5: '交易对象',
        }
        
        # 用于存储户名和账号信息
        account_name = ""
        account_number = ""
        
        for sheet_name in excel_file.sheet_names:
            self.logger.info(f"  处理工作表: {sheet_name}")
            
            try:
                # 读取当前工作表，不指定表头
                df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
            except Exception as e:
                self.logger.error(f"读取工作表 {sheet_name} 时出错: {e}")
                continue
            
            # 确保DataFrame不为空且至少有一列
            if df.empty or len(df.columns) == 0:
                self.logger.warning(f"工作表 {sheet_name} 为空或没有列")
                continue
            
            # 从工作表中提取户名和账号信息
            sheet_account_name, sheet_account_number = self.extract_account_info(df)
            
            # 如果能找到户名和账号，更新变量
            if sheet_account_name:
                account_name = sheet_account_name
            if sheet_account_number:
                account_number = sheet_account_number
            
            # 筛选首列符合日期格式的行
            filtered_rows = []
            for idx, row in df.iterrows():
                # 确保行有至少一个元素
                if len(row) == 0:
                    continue
                    
                # 获取第一列的值
                first_cell_value = row[0]
                if self.is_date_format(first_cell_value):
                    # 只保留需要的列
                    filtered_rows.append(row)
            
            # 如果找到符合条件的行，添加到结果中
            if filtered_rows:
                filtered_df = pd.DataFrame(filtered_rows)
                
                # 确保不会索引超出范围
                if len(filtered_df.columns) < 6:
                    self.logger.warning(f"工作表 {sheet_name} 的列数不足，当前列数: {len(filtered_df.columns)}")
                    # 添加缺失的列
                    for i in range(len(filtered_df.columns), 6):
                        filtered_df[i] = None
                
                # 添加户名和账号列
                filtered_df['户名'] = account_name
                filtered_df['账号'] = account_number
                all_filtered_data.append(filtered_df)
            else:
                self.logger.warning(f"在工作表 {sheet_name} 中未找到符合条件的数据")
        
        # 如果找到符合条件的数据，将其合并并返回
        if all_filtered_data:
            try:
                result_df = pd.concat(all_filtered_data, ignore_index=True)
                
                # 标准化日期
                if 0 in result_df.columns:
                    result_df[0] = result_df[0].apply(self.standardize_date)
                
                # 确保数值列是数值类型
                for col in [2, 3]:  # 交易金额和账户余额列
                    if col in result_df.columns:
                        result_df[col] = result_df[col].apply(self.clean_numeric)
                
                # 重命名列
                rename_dict = {i: name for i, name in column_names.items() if i in result_df.columns}
                result_df = result_df.rename(columns=rename_dict)
                
                self.logger.info(f"从文件 {file_path} 中提取了 {len(result_df)} 行数据")
                return result_df
            except Exception as e:
                self.logger.error(f"处理提取的数据时出错: {e}")
                return None
        else:
            self.logger.warning(f"在文件 {file_path} 中未找到符合条件的数据")
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