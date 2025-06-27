from pathlib import Path
from werkzeug.utils import secure_filename
from flask import current_app # current_app 用于访问 app.config 和 logger
# 导入 extractor_factory 和 db_facade (或者通过依赖注入传递它们)
# from scripts.extractors.factory.extractor_factory import get_extractor_factory # 假设这些在 app 层面实例化后传入
# from scripts.db.db_facade import DBFacade
import logging
from ..extraction.payee_service import payee_service

class FileProcessorService:
    def __init__(self, extractor_service, bank_service, account_service, transaction_service, upload_folder=None, allowed_extensions=None):
        """初始化文件处理服务
        
        Args:
            extractor_service: 文件提取服务
            bank_service: 银行服务实例
            account_service: 账户服务实例
            transaction_service: 交易服务实例
            upload_folder: 上传文件夹路径
            allowed_extensions: 允许的文件扩展名集合
        """
        self.extractor_service = extractor_service
        self.bank_service = bank_service
        self.account_service = account_service
        self.transaction_service = transaction_service
        
        # 设置上传文件夹
        if upload_folder:
            self.upload_folder = Path(upload_folder)
        else:
            self.upload_folder = Path('uploads')
        
        # 设置允许的文件扩展名
        self.allowed_extensions = allowed_extensions or {'xlsx', 'xls'}
        
        # 设置日志器
        self.logger = logging.getLogger(__name__)

    def _is_allowed_file(self, filename):
        """检查文件是否为允许的类型"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in self.allowed_extensions

    def process_uploaded_files(self, uploaded_file_objects):
        """
        处理通过HTTP请求上传的一批文件。
        保存文件，调用提取器，删除已处理文件。
        返回处理结果元组 (processed_files_result, message)。
        """
        filenames = []
        # saved_file_paths = [] # 暂时未使用
        if not uploaded_file_objects or (uploaded_file_objects and uploaded_file_objects[0].filename == ''):
            # flash('没有选择文件 (来自服务)') # flash 应在视图层处理
            return None, "没有选择文件"

        for file_obj in uploaded_file_objects:
            if not self._is_allowed_file(file_obj.filename):
                # flash(f'不支持的文件类型: {file_obj.filename} (来自服务)')
                return None, f'不支持的文件类型: {file_obj.filename}'
            
            filename = secure_filename(file_obj.filename)
            file_path = self.upload_folder / filename
            try:
                file_obj.save(file_path)
                filenames.append(filename)
                # saved_file_paths.append(file_path)
            except Exception as e:
                self.logger.error(f"保存文件 {filename} 失败: {e}")
                # flash(f"保存文件 {filename} 失败。")
                return None, f"保存文件 {filename} 失败"
        
        if not filenames:
            return None, '没有有效文件被保存'

        self.logger.info(f"FileProcessorService: 开始处理 {len(filenames)} 个上传的文件: {', '.join(filenames)}")
        # specific_filenames 用于告知 _process_and_cleanup_files_in_folder 这些是本次上传的文件
        return self._process_and_cleanup_files_in_folder(self.upload_folder, specific_filenames=filenames)

    def _process_and_cleanup_files_in_folder(self, folder_path, specific_filenames=None):
        """
        核心处理逻辑：调用提取器，处理数据库，清理文件。
        specific_filenames: 一个可选的列表，如果提供，则只处理这些文件名。
                           否则，处理文件夹内所有符合条件的文件。
        返回处理结果元组 (processed_files_result, message)。
        """
        try:
            # 获取文件夹中的所有文件
            folder_path_obj = Path(folder_path)
            file_paths = [str(f) for f in folder_path_obj.glob('*') if f.is_file()]
            
            # 处理每个文件
            processed_files_result_all = []
            for file_path in file_paths:
                result = self._process_single_file(file_path)
                processed_files_result_all.append(result)

            if not processed_files_result_all:
                self.logger.warning("提取器未能成功处理任何文件。")
                return None, "未能成功提取任何交易记录"

            # 如果是特定文件上传流程，只关心这些文件的结果
            # 并且只删除这些被成功处理的特定文件
            files_to_consider_for_result_and_cleanup = []
            if specific_filenames:
                # 筛选出本次上传并被处理的文件信息
                for proc_file_info in processed_files_result_all:
                    # 直接访问字典的file_path键
                    file_path = proc_file_info.get('file_path', '')
                    file_name = Path(file_path).name if file_path else ''
                    if file_name in specific_filenames:
                        files_to_consider_for_result_and_cleanup.append(proc_file_info)
                
                if not files_to_consider_for_result_and_cleanup:
                    # 这意味着 specific_filenames 中的文件一个都没在 processed_files_result_all 中找到对应的处理记录
                    self.logger.warning(f"提供的特定文件 {specific_filenames} 未在处理结果中找到。")
                    return None, "指定的上传文件未能被处理"
            else: # 处理目录下所有检测到的文件
                files_to_consider_for_result_and_cleanup = processed_files_result_all
            
            self.logger.info(f"成功处理 {len(files_to_consider_for_result_and_cleanup)} 个目标文件。")

            # 处理完成后删除已处理的文件 (仅删除 files_to_consider_for_result_and_cleanup 中的)
            for file_info in files_to_consider_for_result_and_cleanup:
                file_name_to_delete = "未知文件"  # 初始化默认值
                try:
                    # 使用file_path字段并提取文件名
                    file_path_to_delete = file_info.get('file_path', '')
                    file_name_to_delete = Path(file_path_to_delete).name if file_path_to_delete else ''
                    path_to_delete = Path(folder_path) / file_name_to_delete
                    if path_to_delete.exists():
                        path_to_delete.unlink()
                        self.logger.info(f"已删除处理过的文件: {path_to_delete}")
                    else:
                        # 这个警告可能意味着 extractor_factory.auto_detect_and_process 内部已经移动或删除了文件
                        # 或者 specific_filenames 中的文件实际上在 auto_detect_and_process 调用前就不存在于原始 folder_path
                        self.logger.warning(f"尝试删除处理过的文件时未找到: {path_to_delete}。可能已被提取器移动/删除，或最初就不在特定文件名列表中。")
                except Exception as e:
                    self.logger.error(f"删除文件 {file_name_to_delete} 时出错: {e}")
            
            # 返回针对 relevant_processed_files 的结果
            return files_to_consider_for_result_and_cleanup, "处理成功"

        except Exception as e:
            self.logger.error(f"处理文件时出错 (服务层): {str(e)}", exc_info=True)
            return None, f"处理文件时出错: {str(e)}"
    
    def _process_single_file(self, file_path: str):
        """处理单个文件，从文件导入交易记录
        
        Args:
            file_path: 文件路径
            
        Returns:
            dict: 导入结果
        """
        
        try:
            # 提取数据
            extracted_data = self.extractor_service.extract(file_path)
            
            # 确保银行存在
            bank = self.bank_service.get_or_create_bank(
                name=extracted_data.bank_name,
                code=extracted_data.bank_code
            )
            
            # 确保账户存在
            account = self.account_service.get_or_create_account(
                bank_id=bank.id,
                account_number=extracted_data.account_number,
                account_name=extracted_data.account_name
            )
            
            # 处理交易记录
            processed_count = 0
            for transaction_dict in extracted_data.transactions:
                try:
                    # 使用PayeeService提取商家名称
                    extracted_merchant = payee_service.extract_merchant_name(
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
                    is_duplicate = self.transaction_service.is_duplicate_transaction(transaction_data)
                    
                    if not is_duplicate:
                        # 创建交易记录
                        self.logger.debug(f"新建交易：{transaction_data}")
                        transaction = self.transaction_service.create_transaction(**transaction_data)
                        if transaction:
                            processed_count += 1
                    else:
                        self.logger.debug(f"重复交易：{transaction_data}")
                    
                except Exception as e:
                    self.logger.warning(f"处理交易记录失败: {e}")
                    continue

            # 创建成功结果
            result_data = {
                'success': True,
                'bank': extracted_data.bank_name,
                'account_number': extracted_data.account_number,
                'account_name': extracted_data.account_name,
                'record_count': processed_count,
                'file_path': file_path
            }

            return {
                'success': True,
                'bank': extracted_data.bank_name,
                'record_count': processed_count,
                'file_path': file_path,
                'data': result_data,
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