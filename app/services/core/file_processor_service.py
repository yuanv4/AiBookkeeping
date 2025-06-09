from pathlib import Path
from werkzeug.utils import secure_filename
from flask import current_app # current_app 用于访问 app.config 和 logger
# 导入 extractor_factory 和 db_facade (或者通过依赖注入传递它们)
# from scripts.extractors.factory.extractor_factory import get_extractor_factory # 假设这些在 app 层面实例化后传入
# from scripts.db.db_facade import DBFacade
import logging

class FileProcessorService:
    def __init__(self, extractor_service, database_service, upload_folder=None):
        self.extractor_service = extractor_service
        self.database_service = database_service
        # 如果没有提供 upload_folder，使用默认值或从配置获取
        if upload_folder:
            self.upload_folder = Path(upload_folder)
        else:
            try:
                from flask import current_app
                self.upload_folder = Path(current_app.config.get('UPLOAD_FOLDER', 'uploads'))
            except RuntimeError:
                self.upload_folder = Path('uploads')
        # 移除对 current_app.logger 的直接访问
        # self.logger = current_app.logger # 使用 Flask 的 logger

    def _get_logger(self):
        """获取 logger，如果在应用上下文中，使用 current_app.logger，否则使用标准库 logger"""
        try:
            return current_app.logger
        except RuntimeError:
            # 如果不在应用上下文中，使用标准库 logging
            return logging.getLogger('file_processor_service')

    def _get_allowed_extensions(self):
        """获取允许的文件扩展名，如果在应用上下文中，使用 current_app.config，否则使用默认值"""
        try:
            return current_app.config['ALLOWED_EXTENSIONS']
        except RuntimeError:
            # 如果不在应用上下文中，使用默认值
            return {'xlsx', 'xls'}

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
                self._get_logger().error(f"保存文件 {filename} 失败: {e}")
                # flash(f"保存文件 {filename} 失败。")
                return None, f"保存文件 {filename} 失败"
        
        if not filenames:
            return None, '没有有效文件被保存'

        self._get_logger().info(f"FileProcessorService: 开始处理 {len(filenames)} 个上传的文件: {', '.join(filenames)}")
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
            processed_files_result_all = self.extractor_service.process_files(file_paths)

            if not processed_files_result_all:
                self._get_logger().warning("提取器未能成功处理任何文件。")
                return None, "未能成功提取任何交易记录"

            # 如果是特定文件上传流程，只关心这些文件的结果
            # 并且只删除这些被成功处理的特定文件
            files_to_consider_for_result_and_cleanup = []
            if specific_filenames:
                # 筛选出本次上传并被处理的文件信息
                for proc_file_info in processed_files_result_all:
                    # 使用file_path字段而不是file字段
                    file_path = proc_file_info.get('file_path', '')
                    file_name = Path(file_path).name if file_path else ''
                    if file_name in specific_filenames:
                        files_to_consider_for_result_and_cleanup.append(proc_file_info)
                
                if not files_to_consider_for_result_and_cleanup:
                    # 这意味着 specific_filenames 中的文件一个都没在 processed_files_result_all 中找到对应的处理记录
                    self._get_logger().warning(f"提供的特定文件 {specific_filenames} 未在处理结果中找到。")
                    return None, "指定的上传文件未能被处理"
            else: # init_database 场景，处理目录下所有检测到的文件
                files_to_consider_for_result_and_cleanup = processed_files_result_all
            
            self._get_logger().info(f"成功处理 {len(files_to_consider_for_result_and_cleanup)} 个目标文件。")

            # 处理完成后删除已处理的文件 (仅删除 files_to_consider_for_result_and_cleanup 中的)
            for file_info in files_to_consider_for_result_and_cleanup:
                try:
                    # 使用file_path字段并提取文件名
                    file_path_to_delete = file_info.get('file_path', '')
                    file_name_to_delete = Path(file_path_to_delete).name if file_path_to_delete else ''
                    path_to_delete = Path(folder_path) / file_name_to_delete
                    if path_to_delete.exists():
                        path_to_delete.unlink()
                        self._get_logger().info(f"已删除处理过的文件: {path_to_delete}")
                    else:
                        # 这个警告可能意味着 extractor_factory.auto_detect_and_process 内部已经移动或删除了文件
                        # 或者 specific_filenames 中的文件实际上在 auto_detect_and_process 调用前就不存在于原始 folder_path
                        self._get_logger().warning(f"尝试删除处理过的文件时未找到: {path_to_delete}。可能已被提取器移动/删除，或最初就不在特定文件名列表中。")
                except Exception as e:
                    self._get_logger().error(f"删除文件 {file_name_to_delete} 时出错: {e}")
            
            # 返回针对 relevant_processed_files 的结果
            return files_to_consider_for_result_and_cleanup, "处理成功"

        except Exception as e:
            self._get_logger().error(f"处理文件时出错 (服务层): {str(e)}", exc_info=True)
            return None, f"处理文件时出错: {str(e)}"
    
    def _is_allowed_file(self, filename):
        # 使用 _get_allowed_extensions 方法获取允许的扩展名
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in self._get_allowed_extensions()