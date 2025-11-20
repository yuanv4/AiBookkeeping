"""Category mapping model with fixed primary key"""

from .base import db, BaseModel
from datetime import datetime


class CategoryMapping(BaseModel):
    """分类映射表 - 用户配置的数据源分类到目标分类的映射"""

    __tablename__ = 'category_mappings'

    id = db.Column(db.Integer, primary_key=True)  # 主键ID
    source_category = db.Column(db.String(100), nullable=False, unique=True)  # 数据源分类
    target_category = db.Column(db.String(50), nullable=False)  # 映射到的分类
    is_active = db.Column(db.Boolean, default=True)  # 是否启用
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)  # 创建时间

    def __repr__(self):
        return f'<CategoryMapping {self.source_category} -> {self.target_category}>'