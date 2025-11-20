from typing import List, Optional
from .base import BaseExtractor
from .alipay import AliPayExtractor
from .wechat import WeChatExtractor
from .bank_standard import BankStandardExtractor

class ExtractorFactory:
    """提取器工厂"""
    
    @staticmethod
    def get_extractor(file_path: str) -> Optional[BaseExtractor]:
        """根据文件路径获取合适的提取器"""
        # 实例化所有提取器
        # 注意：这里每次都实例化，对于无状态的提取器是可以的
        # 如果提取器初始化开销大，可以改为单例或缓存
        extractors = [
            AliPayExtractor(),
            WeChatExtractor(),
            BankStandardExtractor()
        ]
        
        for extractor in extractors:
            if extractor.can_handle(file_path):
                return extractor
        
        return None



