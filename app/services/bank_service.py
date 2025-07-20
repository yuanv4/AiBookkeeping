"""银行管理服务

专门负责银行相关的CRUD操作，从DataService中拆分出来。
遵循单一职责原则，只处理银行相关的业务逻辑。
"""

from typing import List, Optional
import logging

from app.models import Bank, db
from app.utils.decorators import cached_query

logger = logging.getLogger(__name__)


class BankService:
    """银行管理服务
    
    提供银行的创建、查询、更新、删除等功能。
    """
    
    def __init__(self, db_session=None):
        """初始化银行服务
        
        Args:
            db_session: 数据库会话，如果为None则使用默认会话
        """
        self.db = db_session or db.session
        self.logger = logging.getLogger(__name__)
    
    def get_or_create_bank(self, name: str, code: str = None) -> Bank:
        """获取或创建银行

        Args:
            name: 银行名称
            code: 银行代码，可选

        Returns:
            Bank: 银行实例

        Raises:
            Exception: 当银行创建或查询失败时抛出异常
        """
        try:
            bank = self.get_bank_by_name(name)
            if not bank:
                bank = Bank.create(name=name, code=code)
                self.logger.info(f"创建新银行: {name}")
            return bank
        except Exception as e:
            self.logger.error(f"获取或创建银行 '{name}' 失败: {e}")
            raise

    def get_bank_by_name(self, name: str) -> Optional[Bank]:
        """根据名称获取银行"""
        try:
            return Bank.query.filter_by(name=name.strip()).first()
        except Exception as e:
            self.logger.error(f"Error getting bank by name '{name}': {e}")
            raise

    def get_bank_by_code(self, code: str) -> Optional[Bank]:
        """根据代码获取银行"""
        try:
            if not code:
                return None
            return Bank.query.filter_by(code=code.strip().upper()).first()
        except Exception as e:
            self.logger.error(f"Error getting bank by code '{code}': {e}")
            raise

    @cached_query()
    def get_all_banks(self) -> List[Bank]:
        """获取所有银行"""
        try:
            return Bank.query.order_by(Bank.name).all()
        except Exception as e:
            self.logger.error(f"Error getting all banks: {e}")
            raise

    def update_bank(self, bank_id: int, **kwargs) -> bool:
        """更新银行信息"""
        try:
            bank = Bank.get_by_id(bank_id)
            if bank:
                bank.update(**kwargs)
                self.logger.info(f"更新银行信息: {bank_id}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error updating bank {bank_id}: {e}")
            raise

    def delete_bank(self, bank_id: int) -> bool:
        """删除银行"""
        try:
            bank = Bank.get_by_id(bank_id)
            if bank:
                bank.delete()
                self.logger.info(f"删除银行: {bank_id}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error deleting bank {bank_id}: {e}")
            raise

    def get_bank_by_id(self, bank_id: int) -> Optional[Bank]:
        """根据ID获取银行"""
        try:
            return Bank.get_by_id(bank_id)
        except Exception as e:
            self.logger.error(f"Error getting bank by id {bank_id}: {e}")
            raise

    def bank_exists(self, name: str) -> bool:
        """检查银行是否存在"""
        try:
            return self.get_bank_by_name(name) is not None
        except Exception as e:
            self.logger.error(f"Error checking bank existence '{name}': {e}")
            return False

    def get_banks_count(self) -> int:
        """获取银行总数"""
        try:
            return Bank.query.count()
        except Exception as e:
            self.logger.error(f"Error getting banks count: {e}")
            return 0
