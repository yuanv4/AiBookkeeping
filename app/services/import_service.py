"""文件导入和处理服务

合并了原来的 FileProcessorService、ExtractionService 和 PayeeService 的功能，
提供统一的文件导入和数据处理接口。

主要功能:
- 文件上传和验证
- 调用提取器解析数据
- 数据导入和处理
- 商家名称识别
- 文件清理和错误处理
"""

import re
from pathlib import Path
from werkzeug.utils import secure_filename
from flask import current_app
import logging
import pandas as pd
from typing import Optional, Dict, List, Any
from functools import lru_cache

from .data_service import DataService
from .models import ExtractedData, ImportResult, ImportConstants

logger = logging.getLogger(__name__)

class ImportService:
    """文件导入和处理服务
    
    提供完整的文件导入流程，从文件上传到数据入库。
    """
    
    def __init__(self, data_service: DataService = None, upload_folder=None, allowed_extensions=None):
        """初始化导入服务
        
        Args:
            data_service: 数据服务实例
            upload_folder: 上传文件夹路径
            allowed_extensions: 允许的文件扩展名集合
        """
        self.data_service = data_service or DataService()
        
        # 设置上传文件夹
        if upload_folder:
            self.upload_folder = Path(upload_folder)
        else:
            self.upload_folder = Path(ImportConstants.DEFAULT_UPLOAD_FOLDER)

        # 设置允许的文件扩展名
        self.allowed_extensions = allowed_extensions or ImportConstants.ALLOWED_EXTENSIONS
        
        # 设置日志器
        self.logger = logging.getLogger(__name__)
        
        # 加载提取器
        self._extractors = []
        self._load_extractors()
        
        # 初始化商家识别规则
        self._merchant_rules = self._build_merchant_rules()

    def _load_extractors(self):
        """加载所有可用的提取器"""
        try:
            from .extractors import ALL_EXTRACTORS
            
            for extractor_class in ALL_EXTRACTORS:
                try:
                    extractor_instance = extractor_class()
                    self._extractors.append(extractor_instance)
                    self.logger.info(f"加载提取器: {extractor_instance.get_bank_name()}")
                except Exception as e:
                    self.logger.error(f"加载提取器失败 {extractor_class}: {e}")
        except ImportError as e:
            self.logger.error(f"无法导入提取器: {e}")

    def _is_allowed_file(self, filename):
        """检查文件是否为允许的类型"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in self.allowed_extensions

    def process_uploaded_files(self, uploaded_file_objects):
        """处理通过HTTP请求上传的一批文件"""
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
            
            # 确保银行存在
            bank = self.data_service.get_or_create_bank(
                name=extracted_data.bank_name,
                code=extracted_data.bank_code
            )
            
            # 确保账户存在
            account = self.data_service.get_or_create_account(
                bank_id=bank.id,
                account_number=extracted_data.account_number,
                account_name=extracted_data.account_name
            )
            
            # 处理交易记录
            processed_count = 0
            for transaction_dict in extracted_data.transactions:
                try:
                    # 使用内置商家识别功能
                    extracted_merchant = self.extract_merchant_name(
                        description=transaction_dict['description'],
                        counterparty=transaction_dict['counterparty']
                    )
                    
                    # 创建交易记录数据
                    transaction_data = {
                        'account_id': account.id,
                        'date': transaction_dict['date'],
                        'amount': transaction_dict['amount'],
                        'balance_after': transaction_dict['balance_after'],
                        'currency': transaction_dict['currency'],
                        'description': transaction_dict['description'],
                        'counterparty': transaction_dict['counterparty'],
                        'merchant_name': extracted_merchant,
                    }
                    
                    # 检查是否已存在相同交易
                    is_duplicate = self.data_service.is_duplicate_transaction(transaction_data)
                    
                    if not is_duplicate:
                        self.logger.debug(f"新建交易：{transaction_data}")
                        transaction = self.data_service.create_transaction(**transaction_data)
                        if transaction:
                            processed_count += 1
                    else:
                        self.logger.debug(f"重复交易：{transaction_data}")
                    
                except Exception as e:
                    self.logger.warning(f"处理交易记录失败: {e}")
                    continue

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
                    self.logger.info(f"为文件 {file_path} 选择了提取器: {extractor.get_bank_name()}")
                    return extractor
            except Exception as e:
                self.logger.debug(f"提取器 {extractor.get_bank_name()} 检查数据时出错: {e}")
                continue
        
        self.logger.warning(f"未找到适用于文件 {file_path} 的提取器")
        return None

    # ==================== 商家名称识别功能 ====================
    
    def _build_merchant_rules(self) -> List[Dict[str, str]]:
        """构建商家识别规则库"""
        rules = [
            # 常见商家规则
            {'pattern': r'美团|MEITUAN|三快在线|北京三快', 'merchant': '美团'},
            {'pattern': r'支付宝|ALIPAY|蚂蚁金服', 'merchant': '支付宝'},
            {'pattern': r'微信支付|WECHAT|腾讯|财付通', 'merchant': '微信支付'},
            {'pattern': r'淘宝|TAOBAO|天猫|TMALL|阿里巴巴', 'merchant': '淘宝/天猫'},
            {'pattern': r'京东|JD\.COM|京东商城', 'merchant': '京东'},
            {'pattern': r'滴滴|DIDI|小桔科技', 'merchant': '滴滴出行'},
            {'pattern': r'星巴克|STARBUCKS', 'merchant': '星巴克'},
            {'pattern': r'APPLE|苹果|APP STORE|ITUNES', 'merchant': 'Apple'},
            # 银行相关
            {'pattern': r'工商银行|ICBC', 'merchant': '工商银行'},
            {'pattern': r'建设银行|CCB', 'merchant': '建设银行'},
            {'pattern': r'农业银行|ABC', 'merchant': '农业银行'},
            {'pattern': r'中国银行|BOC', 'merchant': '中国银行'},
            {'pattern': r'招商银行|CMB', 'merchant': '招商银行'},
            # 生活服务
            {'pattern': r'中国移动|CHINA MOBILE|移动通信', 'merchant': '中国移动'},
            {'pattern': r'中国联通|CHINA UNICOM|联通', 'merchant': '中国联通'},
            {'pattern': r'中国电信|CHINA TELECOM|电信', 'merchant': '中国电信'},
            {'pattern': r'国家电网|电力公司|供电局', 'merchant': '国家电网'},
            {'pattern': r'自来水|水务|供水', 'merchant': '自来水公司'},
            {'pattern': r'燃气|天然气|煤气', 'merchant': '燃气公司'},
        ]
        return rules

    def extract_merchant_name(self, description: str, counterparty: str = None) -> Optional[str]:
        """从交易描述和交易对方信息中提取商家名称"""
        if not description:
            return None
        
        # 合并描述和交易对方信息进行匹配
        text_to_match = description
        if counterparty:
            text_to_match = f"{description} {counterparty}"
        
        # 清理文本，移除特殊字符但保留中英文
        text_to_match = re.sub(r'[^\w\s\u4e00-\u9fff]', ' ', text_to_match)
        
        # 遍历规则库进行匹配
        for rule in self._merchant_rules:
            pattern = rule['pattern']
            merchant = rule['merchant']
            
            # 使用正则表达式进行匹配（忽略大小写）
            if re.search(pattern, text_to_match, re.IGNORECASE):
                return merchant
        
        return None
