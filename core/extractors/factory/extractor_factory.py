"""提取器工厂模块，负责创建和管理银行提取器"""
import os
import sys
import importlib
import inspect
import logging
from typing import Dict, List, Type, Optional, Any, Union
from pathlib import Path

# 添加项目根目录到PYTHONPATH
current_dir = os.path.dirname(os.path.abspath(__file__))
extractors_dir = os.path.dirname(current_dir)
scripts_dir = os.path.dirname(extractors_dir)
root_dir = os.path.dirname(scripts_dir)
if root_dir not in sys.path:
    sys.path.append(root_dir)
if scripts_dir not in sys.path:
    sys.path.append(scripts_dir)

from core.extractors.interfaces.extractor_interface import ExtractorInterface
from core.extractors.config.config_loader import get_config_loader

class ExtractorFactory:
    """银行提取器工厂，用于创建和管理银行提取器"""
    
    def __init__(self, app):
        """初始化提取器工厂
        
        Args:
            app: Flask application instance.
        """
        self.logger = logging.getLogger('extractor_factory')
        self.app = app
        self.extractors: Dict[str, Type[ExtractorInterface]] = {}
        self.config_loader = get_config_loader(self.app)
    
    def register(self, bank_code: str, extractor_class: Type[ExtractorInterface]):
        """注册银行提取器
        
        Args:
            bank_code: 银行代码
            extractor_class: 提取器类
        """
        if bank_code in self.extractors:
            self.logger.warning(f"提取器已存在，将被覆盖: {bank_code}")
        
        self.extractors[bank_code] = extractor_class
        self.logger.info(f"注册提取器: {bank_code} -> {extractor_class.__name__}")
    
    def create(self, bank_code: str) -> Optional[ExtractorInterface]:
        """创建指定银行的提取器实例
        
        Args:
            bank_code: 银行代码
            
        Returns:
            ExtractorInterface: 提取器实例，如果不存在返回None
        """
        extractor_class = self.extractors.get(bank_code)
        if extractor_class is None:
            self.logger.warning(f"未注册的提取器: {bank_code}")
            return None
        
        try:
            return extractor_class()
        except Exception as e:
            self.logger.error(f"创建提取器失败: {bank_code}, 错误: {str(e)}")
            return None
    
    def get_all_codes(self) -> List[str]:
        """获取所有已注册的银行代码
        
        Returns:
            list: 银行代码列表
        """
        return list(self.extractors.keys())
    
    def auto_detect_and_create(self, file_path: str) -> Optional[ExtractorInterface]:
        """根据文件自动检测适用的提取器
        
        Args:
            file_path: 文件路径
            
        Returns:
            ExtractorInterface: 提取器实例，如果没有适用的提取器返回None
        """
        self.logger.info(f"尝试自动检测适用于文件的提取器: {file_path}")
        
        for bank_code in self.extractors:
            try:
                extractor = self.create(bank_code)
                if extractor and extractor.can_process_file(file_path):
                    self.logger.info(f"检测到适用的提取器: {bank_code} -> {file_path}")
                    return extractor
            except Exception as e:
                self.logger.error(f"检测提取器时出错: {bank_code}, 错误: {str(e)}")
        
        self.logger.warning(f"未找到适用于文件的提取器: {file_path}")
        return None
    
    def auto_discover_and_register(self):
        """自动发现并注册所有提取器"""
        try:
            banks_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'banks')
            if not os.path.exists(banks_dir):
                self.logger.warning(f"银行提取器目录不存在: {banks_dir}")
                return
            
            # 获取所有提取器模块
            for file_name in os.listdir(banks_dir):
                if file_name.endswith('_transaction_extractor.py'):
                    module_name = file_name[:-3]  # 去掉.py后缀
                    try:
                        # 动态导入模块
                        module_path = f"scripts.extractors.banks.{module_name}"
                        module = importlib.import_module(module_path)
                        
                        # 查找模块中的提取器类
                        for name, obj in inspect.getmembers(module):
                            if (inspect.isclass(obj) and 
                                issubclass(obj, ExtractorInterface) and 
                                obj.__module__ == module.__name__):
                                
                                # 创建实例以获取bank_code
                                try:
                                    instance = obj()
                                    bank_code = instance.get_bank_code()
                                    self.register(bank_code, obj)
                                except Exception as e:
                                    self.logger.error(f"注册提取器失败: {name}, 错误: {str(e)}")
                    
                    except Exception as e:
                        self.logger.error(f"导入模块失败: {module_name}, 错误: {str(e)}")
            
            self.logger.info(f"已自动注册 {len(self.extractors)} 个提取器")
            
        except Exception as e:
            self.logger.error(f"自动发现提取器时出错: {str(e)}")
    
    def auto_detect_and_process(self, upload_dir: Union[str, Path]) -> List[Dict[str, Any]]:
        """自动检测并处理目录中的所有银行交易明细文件
        
        Args:
            upload_dir: 上传文件目录路径（字符串或Path对象）
            
        Returns:
            list: 处理结果信息列表
                每项包含: {
                    'file': 文件名,
                    'bank': 银行名称,
                    'record_count': 提取的记录数量,
                    'status': 处理状态,
                    'message': 处理消息
                }
        """
        self.logger.info(f"开始自动检测并处理目录: {upload_dir}")
        
        # 确保upload_dir是Path对象
        if isinstance(upload_dir, str):
            upload_dir = Path(upload_dir)
            
        # 查找所有Excel文件
        excel_files = list(upload_dir.glob('*.xlsx')) + list(upload_dir.glob('*.xls'))
        
        if not excel_files:
            self.logger.warning(f"在目录 {upload_dir} 中未找到Excel文件")
            return []
            
        # 处理结果
        all_processed_files = []
        
        # 遍历处理每个文件
        for file_path in excel_files:
            try:
                self.logger.info(f"处理文件: {file_path}")
                
                # 尝试自动检测适用的提取器
                extractor = self.auto_detect_and_create(str(file_path))
                if extractor:
                    # 处理文件
                    bank_name = extractor.get_bank_name()
                    result = extractor.process_file(str(file_path))
                    
                    if result and result.get('success'):
                        process_result = {
                            'file': file_path.name,
                            'bank': bank_name,
                            'record_count': result.get('record_count', 0),
                            'status': 'success',
                            'message': result.get('message', '处理成功')
                        }
                        all_processed_files.append(process_result)
                        self.logger.info(f"成功处理文件: {file_path}, 提取 {result.get('record_count', 0)} 条记录")
                    else:
                        error_message = result.get('message', '未知错误') if result else '处理失败'
                        self.logger.warning(f"处理文件失败: {file_path}, 原因: {error_message}")
                else:
                    self.logger.warning(f"未找到适用的提取器: {file_path}")
            except Exception as e:
                self.logger.error(f"处理文件时出错: {file_path}, 错误: {str(e)}")
        
        self.logger.info(f"处理完成，成功处理 {len(all_processed_files)} 个文件")
        return all_processed_files
    
    def process_files(self, upload_dir: str) -> List[Dict[str, Any]]:
        """处理上传目录中的所有文件
        
        Args:
            upload_dir: 上传文件目录
            
        Returns:
            list: 处理结果信息
        """
        import glob
        
        # 查找所有Excel文件
        excel_patterns = ['*.xlsx', '*.xls']
        excel_files = []
        
        for pattern in excel_patterns:
            excel_files.extend(glob.glob(os.path.join(upload_dir, pattern)))
        
        if not excel_files:
            self.logger.warning(f"在目录 {upload_dir} 中未找到Excel文件")
            return []
        
        # 处理结果
        all_processed_files = []
        
        # 遍历处理每个文件
        for file_path in excel_files:
            extractor = self.auto_detect_and_create(file_path)
            if extractor:
                try:
                    # 处理单个文件
                    result = extractor.process_files(upload_dir)
                    if result:
                        all_processed_files.extend(result)
                except Exception as e:
                    self.logger.error(f"处理文件时出错: {file_path}, 错误: {str(e)}")
            else:
                self.logger.warning(f"未找到适用的提取器: {file_path}")
        
        return all_processed_files

# 单例模式管理调整：工厂现在依赖 app 实例
# _factory = None # Global singleton might be problematic if app context changes or for testing

def get_extractor_factory(app) -> ExtractorFactory:
    """获取提取器工厂实例

    Args:
        app: Flask application instance.

    Returns:
        ExtractorFactory: 提取器工厂实例
    """
    # Simplest approach: create a new factory per app or manage it on the app object itself.
    # For now, let's assume it's okay to create it or retrieve from app if already set.
    if not hasattr(app, 'extractor_factory_instance'):
        factory = ExtractorFactory(app)
        factory.auto_discover_and_register()  # 自动发现并注册
        app.extractor_factory_instance = factory
    return app.extractor_factory_instance