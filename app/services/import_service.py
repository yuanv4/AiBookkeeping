"""文件导入和处理服务

合并了原来的 FileProcessorService、ExtractionService 和 PayeeService 的功能，
提供统一的文件导入和数据处理接口。

主要功能:
- 文件上传和验证
- 调用提取器解析数据
- 数据导入和处理
- 商家名称识别
- 文件清理和错误处理

业务逻辑:
- 分类设置：由提取器负责设置交易分类
- 重复检查：避免重复导入相同的交易记录
- 错误处理：提供完整的异常处理和日志记录
"""

from pathlib import Path
from werkzeug.utils import secure_filename
import logging
import pandas as pd
from typing import List, Any, Optional, Dict, Set, Union

from .transaction_service import TransactionService
from . import ExtractedData

class ImportService:
    """文件导入和处理服务

    提供完整的文件导入流程，从文件上传到数据入库。
    """

    def __init__(self, transaction_service: TransactionService, upload_folder: Optional[Union[str, Path]] = None, allowed_extensions: Optional[Set[str]] = None) -> None:
        """初始化导入服务

        Args:
            transaction_service: 交易服务实例
            upload_folder: 上传文件夹路径
            allowed_extensions: 允许的文件扩展名集合
        """
        self.transaction_service = transaction_service
        self.logger = logging.getLogger(self.__class__.__name__)

        # 设置上传文件夹
        self.upload_folder = Path('uploads')

        # 设置允许的文件扩展名
        self.allowed_extensions = {'xlsx', 'xls'}

        # 加载提取器
        self._extractors = []
        self._load_extractors()

    def _load_extractors(self) -> None:
        """加载所有可用的提取器"""
        try:
            from . import ALL_EXTRACTORS
            
            for extractor_class in ALL_EXTRACTORS:
                try:
                    extractor_instance = extractor_class()
                    self._extractors.append(extractor_instance)
                    self.logger.info(f"加载提取器: {extractor_instance.BANK_NAME}")
                except Exception as e:
                    self.logger.error(f"加载提取器失败 {extractor_class}: {e}")
        except ImportError as e:
            self.logger.error(f"无法导入提取器: {e}")

    def _is_allowed_file(self, filename: str) -> bool:
        """检查文件是否为允许的类型

        Args:
            filename: 文件名

        Returns:
            bool: 如果文件类型被允许则返回True，否则返回False
        """
        return ('.' in filename and
                filename.rsplit('.', 1)[1].lower() in self.allowed_extensions)

    def process_uploaded_files(self, uploaded_file_objects: List[Any]) -> tuple:
        """处理通过HTTP请求上传的一批文件

        Args:
            uploaded_file_objects: 上传的文件对象列表

        Returns:
            tuple: (处理结果, 状态消息)
        """
        filenames = []
        
        if not uploaded_file_objects or (uploaded_file_objects and uploaded_file_objects[0].filename == ''):
            return None, "没有选择文件"

        for file_obj in uploaded_file_objects:
            if not self._is_allowed_file(file_obj.filename):
                return None, f'不支持的文件类型: {file_obj.filename}'
            
            filename = secure_filename(file_obj.filename)
            file_path = self.upload_folder / filename
            try:
                file_obj.save(file_path)
                filenames.append(filename)
            except Exception as e:
                self.logger.error(f"保存文件 {filename} 失败: {e}")
                return None, f"保存文件 {filename} 失败"

        if not filenames:
            return None, '没有有效文件被保存'

        self.logger.info(f"开始处理 {len(filenames)} 个上传的文件: {', '.join(filenames)}")
        return self._process_and_cleanup_files_in_folder(self.upload_folder, specific_filenames=filenames)

    def _process_and_cleanup_files_in_folder(self, folder_path, specific_filenames=None):
        """核心处理逻辑：调用提取器，处理数据库，清理文件"""
        try:
            folder_path_obj = Path(folder_path)
            file_paths = [str(f) for f in folder_path_obj.glob('*') if f.is_file()]
            
            processed_files_result_all = []
            for file_path in file_paths:
                result = self._process_single_file(file_path)
                processed_files_result_all.append(result)

            if not processed_files_result_all:
                self.logger.warning("提取器未能成功处理任何文件。")
                return None, "未能成功提取任何交易记录"

            # 筛选目标文件
            files_to_consider_for_result_and_cleanup = []
            if specific_filenames:
                for proc_file_info in processed_files_result_all:
                    file_path = proc_file_info.get('file_path', '')
                    file_name = Path(file_path).name if file_path else ''
                    if file_name in specific_filenames:
                        files_to_consider_for_result_and_cleanup.append(proc_file_info)

                if not files_to_consider_for_result_and_cleanup:
                    self.logger.warning(f"提供的特定文件 {specific_filenames} 未在处理结果中找到。")
                    return None, "指定的上传文件未能被处理"
            else:
                files_to_consider_for_result_and_cleanup = processed_files_result_all

            self.logger.info(f"成功处理 {len(files_to_consider_for_result_and_cleanup)} 个目标文件。")

            # 清理已处理的文件
            for file_info in files_to_consider_for_result_and_cleanup:
                file_name_to_delete = "未知文件"
                try:
                    file_path_to_delete = file_info.get('file_path', '')
                    file_name_to_delete = Path(file_path_to_delete).name if file_path_to_delete else ''
                    path_to_delete = Path(folder_path) / file_name_to_delete
                    if path_to_delete.exists():
                        path_to_delete.unlink()
                        self.logger.info(f"已删除处理过的文件: {path_to_delete}")
                    else:
                        self.logger.warning(f"尝试删除处理过的文件时未找到: {path_to_delete}")
                except Exception as e:
                    self.logger.error(f"删除文件 {file_name_to_delete} 时出错: {e}")

            return files_to_consider_for_result_and_cleanup, "处理成功"

        except Exception as e:
            self.logger.error(f"处理文件时出错: {str(e)}", exc_info=True)
            return None, f"处理文件时出错: {str(e)}"

    def _process_single_file(self, file_path: str):
        """处理单个文件，从文件导入交易记录"""
        try:
            # 提取数据
            extracted_data = self.extract_from_file(file_path)
            
            # 处理交易记录
            processed_count = 0

            # 准备所有交易数据
            transactions_data = []
            for transaction_dict in extracted_data.transactions:
                try:
                    # 创建交易记录数据（直接使用银行和账户信息）
                    transaction_data = {
                        'bank_name': extracted_data.bank_name,
                        'bank_code': extracted_data.bank_code,
                        'account_number': extracted_data.account_number,
                        'account_name': extracted_data.account_name,
                        'account_type': 'checking',  # 默认账户类型
                        'date': transaction_dict['date'],
                        'amount': transaction_dict['amount'],
                        'balance_after': transaction_dict['balance_after'],
                        'currency': transaction_dict['currency'],
                        'description': transaction_dict['description'],
                        'counterparty': transaction_dict['counterparty'],
                        'category': transaction_dict['category'],
                    }
                    transactions_data.append(transaction_data)

                except Exception as e:
                    self.logger.warning(f"准备交易记录失败: {e}")
                    continue

            # 批量检查重复交易，提高性能
            if transactions_data:
                duplicate_flags = self.transaction_service.batch_check_duplicates(transactions_data)

                # 批量创建非重复交易
                for transaction_data, is_duplicate in zip(transactions_data, duplicate_flags):
                    if not is_duplicate:
                        try:
                            self.logger.debug(f"新建交易：{transaction_data}")
                            transaction = self.transaction_service.create_transaction(**transaction_data)
                            if transaction:
                                processed_count += 1
                        except Exception as e:
                            self.logger.warning(f"创建交易记录失败: {e}")
                    else:
                        self.logger.debug(f"跳过重复交易：{transaction_data.get('counterparty', 'Unknown')}")

            self.logger.info(f"文件 {file_path} 处理完成，新增 {processed_count} 条交易记录")

            return {
                'success': True,
                'bank': extracted_data.bank_name,
                'record_count': processed_count,
                'file_path': file_path,
                'data': {
                    'success': True,
                    'bank': extracted_data.bank_name,
                    'account_number': extracted_data.account_number,
                    'account_name': extracted_data.account_name,
                    'record_count': processed_count,
                    'file_path': file_path
                },
                'error': None
            }
            
        except Exception as e:
            self.logger.error(f"从文件导入交易记录失败 {file_path}: {e}")
            return {
                'success': False,
                'bank': None,
                'record_count': 0,
                'file_path': file_path,
                'data': None,
                'error': f'从文件导入交易记录失败: {str(e)}'
            }

    def extract_from_file(self, file_path: str) -> ExtractedData:
        """从文件中提取银行对账单数据"""
        # 验证文件并读取数据
        df_raw = self._read_file_to_dataframe(file_path)

        # 查找合适的提取器
        extractor = self._find_suitable_extractor(df_raw, file_path)
        if not extractor:
            raise ValueError('未找到适用于该文件的提取器')

        # 使用提取器进行完整提取
        return extractor.extract(df_raw)

    def _read_file_to_dataframe(self, file_path: str) -> pd.DataFrame:
        """读取文件为DataFrame"""
        if not Path(file_path).exists():
            raise FileNotFoundError(f'文件不存在: {file_path}')
        
        try:
            return pd.read_excel(file_path, header=None)
        except Exception as e:
            self.logger.error(f"读取文件失败 {file_path}: {e}")
            raise ValueError(f'无法读取文件 {file_path}: {str(e)}')

    def _find_suitable_extractor(self, df_raw: pd.DataFrame, file_path: str):
        """查找合适的提取器"""
        for extractor in self._extractors:
            try:
                if extractor.is_applicable(df_raw):
                    self.logger.info(f"为文件 {file_path} 选择了提取器: {extractor.BANK_NAME}")
                    return extractor
            except Exception as e:
                self.logger.debug(f"提取器 {extractor.BANK_NAME} 检查数据时出错: {e}")
                continue

        self.logger.warning(f"未找到适用于文件 {file_path} 的提取器")
        return None