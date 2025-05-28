from abc import ABC, abstractmethod
import pandas as pd
from typing import Tuple, Dict, List, Optional, Any, Union

class ExtractorInterface(ABC):
    """银行交易提取器接口，定义所有提取器必须实现的方法"""

    @abstractmethod
    def get_bank_code(self) -> str:
        """获取银行代码，如CMB、CCB等"""
        pass

    @abstractmethod
    def get_bank_name(self) -> str:
        """获取银行名称，如招商银行、建设银行等"""
        pass

    @abstractmethod
    def get_bank_keyword(self) -> str:
        """获取银行关键词，用于文件匹配"""
        pass

    @abstractmethod
    def can_process_file(self, file_path: str) -> bool:
        """判断是否可以处理指定文件"""
        pass

    @abstractmethod
    def extract_account_info(self, df: pd.DataFrame) -> Tuple[str, str]:
        """提取账户信息
        
        Args:
            df: 包含账户信息的DataFrame
            
        Returns:
            tuple: (account_name, account_number)
        """
        pass

    @abstractmethod
    def extract_transactions(self, file_path: str) -> Optional[pd.DataFrame]:
        """提取交易数据
        
        Args:
            file_path: Excel文件路径
            
        Returns:
            DataFrame: 标准格式的交易数据或None（提取失败）
        """
        pass

    @abstractmethod
    def process_files(self, upload_dir: str) -> List[Dict[str, Any]]:
        """处理指定目录中的所有文件
        
        Args:
            upload_dir: 上传文件目录
            
        Returns:
            list: 处理结果信息
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    def create_standard_dataframe(self, df: pd.DataFrame, account_name: str, account_number: str, header_row_idx: int) -> pd.DataFrame:
        """创建标准格式的交易数据DataFrame
        
        Args:
            df: 原始DataFrame
            account_name: 账户名称
            account_number: 账户号码
            header_row_idx: 标题行索引
            
        Returns:
            pandas.DataFrame: 标准格式的DataFrame，包含以下列:
                - transaction_date: 交易日期
                - transaction_id: 交易ID
                - amount: 交易金额
                - balance: 余额
                - transaction_type: 交易类型
                - counterparty: 交易对手方
                - currency: 币种
                - remarks: 备注
        """
        pass 