"""Bank service for handling bank-related operations."""

from typing import List, Optional
import logging

from app.models import Bank

logger = logging.getLogger(__name__)

class BankService:
    """Service for handling bank operations."""
    
    def __init__(self, db_session=None):
        """初始化银行服务
        
        Args:
            db_session: 数据库会话，如果为None则使用默认会话
        """
        from app.models import db
        self.db = db_session or db.session
        self.logger = logging.getLogger(__name__)

    def get_or_create_bank(self, name: str, code: str = None) -> Bank:
        """Get existing bank or create new one."""
        try:
            # 首先尝试根据名称查找现有银行
            bank = self.get_by_name(name)
            if not bank:
                # 如果不存在，创建新银行
                bank = Bank.create(name=name, code=code)
                self.logger.info(f"Created new bank: {name}")
            return bank
        except Exception as e:
            self.logger.error(f"Error getting or creating bank '{name}': {e}")
            raise

    def get_by_name(self, name: str) -> Optional[Bank]:
        """Get bank by name."""
        try:
            return Bank.query.filter_by(name=name.strip()).first()
        except Exception as e:
            self.logger.error(f"Error getting bank by name '{name}': {e}")
            raise

    def get_by_code(self, code: str) -> Optional[Bank]:
        """Get bank by code."""
        try:
            if not code:
                return None
            return Bank.query.filter_by(code=code.strip().upper()).first()
        except Exception as e:
            self.logger.error(f"Error getting bank by code '{code}': {e}")
            raise

    def get_all_banks(self) -> List[Bank]:
        """Get all banks."""
        try:
            return Bank.query.order_by(Bank.name).all()
        except Exception as e:
            self.logger.error(f"Error getting all banks: {e}")
            raise

    def update_bank(self, bank_id: int, **kwargs) -> bool:
        """Update bank information."""
        try:
            bank = Bank.get_by_id(bank_id)
            if bank:
                bank.update(**kwargs)
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error updating bank {bank_id}: {e}")
            raise

    def delete_bank(self, bank_id: int) -> bool:
        """Delete bank."""
        try:
            bank = Bank.get_by_id(bank_id)
            if bank:
                bank.delete()
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error deleting bank {bank_id}: {e}")
            raise