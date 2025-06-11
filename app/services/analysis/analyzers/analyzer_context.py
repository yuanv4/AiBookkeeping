"""分析器依赖注入容器

提供统一的配置管理和依赖注入功能，用于分析器的创建和配置。
"""

from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session


class AnalyzerContext:
    """分析器依赖注入容器
    
    提供分析器所需的所有依赖项，包括数据库会话、用户配置、时间范围等。
    使用依赖注入模式，便于测试和配置管理。
    """
    
    def __init__(
        self,
        db_session: Session,
        user_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """初始化分析器上下文
        
        Args:
            db_session: 数据库会话
            user_id: 用户ID
            start_date: 分析开始时间（可选）
            end_date: 分析结束时间（可选）
            config: 额外配置参数（可选）
        """
        self._db_session = db_session
        self._user_id = user_id
        self._start_date = start_date
        self._end_date = end_date
        self._config = config or {}
        
        # 初始化服务属性为None，实际使用时需要设置
        self.data_service = None
        self.calculation_service = None
        self.cache_service = None
    
    @property
    def db_session(self) -> Session:
        """获取数据库会话"""
        return self._db_session
    
    @property
    def user_id(self) -> int:
        """获取用户ID"""
        return self._user_id
    
    @property
    def start_date(self) -> Optional[datetime]:
        """获取分析开始时间"""
        return self._start_date
    
    @property
    def end_date(self) -> Optional[datetime]:
        """获取分析结束时间"""
        return self._end_date
    
    @property
    def config(self) -> Dict[str, Any]:
        """获取配置参数"""
        return self._config.copy()
    
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """获取指定配置值
        
        Args:
            key: 配置键名
            default: 默认值
            
        Returns:
            配置值或默认值
        """
        return self._config.get(key, default)
    
    def set_config_value(self, key: str, value: Any) -> None:
        """设置配置值
        
        Args:
            key: 配置键名
            value: 配置值
        """
        self._config[key] = value
    
    def update_config(self, config: Dict[str, Any]) -> None:
        """批量更新配置
        
        Args:
            config: 配置字典
        """
        self._config.update(config)
    
    def with_time_range(self, start_date: datetime, end_date: datetime) -> 'AnalyzerContext':
        """创建带有新时间范围的上下文副本
        
        Args:
            start_date: 新的开始时间
            end_date: 新的结束时间
            
        Returns:
            新的上下文实例
        """
        return AnalyzerContext(
            db_session=self._db_session,
            user_id=self._user_id,
            start_date=start_date,
            end_date=end_date,
            config=self._config.copy()
        )
    
    def with_config(self, config: Dict[str, Any]) -> 'AnalyzerContext':
        """创建带有新配置的上下文副本
        
        Args:
            config: 新的配置字典
            
        Returns:
            新的上下文实例
        """
        new_config = self._config.copy()
        new_config.update(config)
        
        return AnalyzerContext(
            db_session=self._db_session,
            user_id=self._user_id,
            start_date=self._start_date,
            end_date=self._end_date,
            config=new_config
        )
    
    def __repr__(self) -> str:
        """字符串表示"""
        return (
            f"AnalyzerContext("
            f"user_id={self._user_id}, "
            f"start_date={self._start_date}, "
            f"end_date={self._end_date}, "
            f"config_keys={list(self._config.keys())}"
            f")"
        )