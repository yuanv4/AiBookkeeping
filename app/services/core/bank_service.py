"""Bank service for handling bank-related operations.

This module provides bank management functionality including CRUD operations
and bank-specific business logic.
"""

from typing import List, Optional
import logging

from app.models import Bank

logger = logging.getLogger(__name__)

class BankService:
    """Service for handling bank operations."""

    @staticmethod
    def get_or_create_bank(name: str, code: str = None) -> Bank:
        """Get existing bank or create new one."""
        try:
            # 首先尝试根据名称查找现有银行
            bank = BankService.get_by_name(name)
            if not bank:
                # 如果不存在，创建新银行
                bank = Bank.create(name=name, code=code)
                logger.info(f"Created new bank: {name}")
            return bank
        except Exception as e:
            logger.error(f"Error getting or creating bank '{name}': {e}")
            raise

    @staticmethod
    def get_by_name(name: str) -> Optional[Bank]:
        """Get bank by name."""
        try:
            return Bank.query.filter_by(name=name.strip()).first()
        except Exception as e:
            logger.error(f"Error getting bank by name '{name}': {e}")
            raise

    @staticmethod
    def get_by_code(code: str) -> Optional[Bank]:
        """Get bank by code."""
        try:
            if not code:
                return None
            return Bank.query.filter_by(code=code.strip().upper()).first()
        except Exception as e:
            logger.error(f"Error getting bank by code '{code}': {e}")
            raise

    @staticmethod
    def get_all_banks() -> List[Bank]:
        """Get all banks."""
        try:
            return Bank.query.order_by(Bank.name).all()
        except Exception as e:
            logger.error(f"Error getting all banks: {e}")
            raise

    @staticmethod
    def update_bank(bank_id: int, **kwargs) -> bool:
        """Update bank information."""
        try:
            bank = Bank.get_by_id(bank_id)
            if bank:
                bank.update(**kwargs)
                return True
            return False
        except Exception as e:
            logger.error(f"Error updating bank {bank_id}: {e}")
            raise

    @staticmethod
    def delete_bank(bank_id: int) -> bool:
        """Delete bank."""
        try:
            bank = Bank.get_by_id(bank_id)
            if bank:
                bank.delete()
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting bank {bank_id}: {e}")
            raise