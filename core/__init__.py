# scripts包初始化文件
"""
AI记账系统
=========

这个包包含AI记账系统的所有脚本模块，按功能分为以下几类：

1. extractors - 数据提取模块
2. analyzers - 数据分析模块
3. visualization - 数据可视化模块
4. db - 数据库管理模块
5. automation - 自动化工具模块
"""

import os
import sys
from typing import Dict, Any, Optional, List

# 添加项目根目录到PYTHONPATH以解决导入问题
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
if root_dir not in sys.path:
    sys.path.append(root_dir)

# 设置日志
# from core.common.logging_setup import setup_logging # Commented out as app instance is not available here
# logger = setup_logging(module_name='scripts') # Commented out

# 导入主要组件
# from core.common.config import get_config_manager # This line is intentionally commented out
from core.common.exceptions import AIBookkeepingError
from core.db.db_manager import DBManager
from core.extractors.factory.extractor_factory import ExtractorFactory
from core.analyzers.transaction_analyzer import TransactionAnalyzer
from core.visualization.visualization_helper import VisualizationHelper

# 版本信息
__version__ = '1.0.0'

def initialize_system(config_path: Optional[str] = None) -> Dict[str, Any]:
    """初始化AI记账系统
    
    Args:
        config_path: 配置文件路径，如果为None则使用默认路径
        
    Returns:
        dict: 包含各个组件实例的字典
    """
    try:
        # 获取配置管理器
        config_manager = get_config_manager()
        
        # 如果指定了配置路径，重新加载配置
        if config_path:
            # 这里可以在未来实现从指定路径加载配置的功能
            pass
        
        # 初始化数据库管理器
        db_manager = DBManager()
        
        # 初始化提取器工厂
        extractor_factory = ExtractorFactory()
        
        # 初始化交易分析器
        transaction_analyzer = TransactionAnalyzer(db_manager)
        
        # 返回系统组件
        return {
            'config_manager': config_manager,
            'db_manager': db_manager,
            'extractor_factory': extractor_factory,
            'transaction_analyzer': transaction_analyzer
        }
    except Exception as e:
        logger.error(f"初始化系统失败: {str(e)}")
        raise

def process_files(directory: str, bank_code: Optional[str] = None) -> Dict[str, Any]:
    """处理目录中的交易文件
    
    Args:
        directory: 文件目录
        bank_code: 银行代码，如果为None则自动检测
        
    Returns:
        dict: 处理结果
    """
    try:
        # 初始化系统
        system = initialize_system()
        extractor_factory = system['extractor_factory']
        
        # 获取提取器
        if bank_code:
            extractor = extractor_factory.get_extractor(bank_code)
        else:
            extractor = extractor_factory.auto_detect_extractor(directory)
        
        if not extractor:
            raise AIBookkeepingError("无法确定适用的提取器")
        
        # 处理文件
        results = extractor.process_files(directory)
        
        # 返回处理结果
        return {
            'success': True,
            'results': results,
            'bank_code': extractor.get_bank_code(),
            'bank_name': extractor.get_bank_name()
        }
    except Exception as e:
        logger.error(f"处理文件失败: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

def analyze_transactions(start_date: Optional[str] = None, end_date: Optional[str] = None, 
                        account_number: Optional[str] = None) -> Dict[str, Any]:
    """分析交易数据
    
    Args:
        start_date: 开始日期 (YYYY-MM-DD)
        end_date: 结束日期 (YYYY-MM-DD)
        account_number: 账号 (用于过滤)
        
    Returns:
        dict: 分析结果
    """
    try:
        # 初始化系统
        system = initialize_system()
        transaction_analyzer = system['transaction_analyzer']
        
        # 分析数据
        results = transaction_analyzer.analyze_transaction_data_direct(
            start_date=start_date,
            end_date=end_date,
            account_number=account_number
        )
        
        return {
            'success': True,
            'results': results
        }
    except Exception as e:
        logger.error(f"分析交易失败: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

def generate_visualizations(analysis_data: Dict[str, Any]) -> Dict[str, Any]:
    """生成可视化
    
    Args:
        analysis_data: 分析数据
        
    Returns:
        dict: 包含图表路径的字典
    """
    try:
        # 创建可视化助手
        visualizer = VisualizationHelper(data=analysis_data)
        
        # 生成所有图表
        charts = visualizer.generate_all_charts()
        
        return {
            'success': True,
            'charts': charts
        }
    except Exception as e:
        logger.error(f"生成可视化失败: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }