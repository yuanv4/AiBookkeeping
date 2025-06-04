# db包初始化文件
"""
数据库管理模块
============

负责数据库操作和数据存储。

主要模块：
- db_facade.py - 数据库门面，统一管理所有数据库操作
"""

from .db_facade import DBFacade

__all__ = ['DBManager']