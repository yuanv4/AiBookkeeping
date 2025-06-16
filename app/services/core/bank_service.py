"""Bank service for handling bank-related operations.

This module provides bank management functionality including CRUD operations
and bank-specific business logic.
"""

from typing import List
import logging

from app.models import Bank

logger = logging.getLogger(__name__)

class BankService:
    """Service for handling bank operations."""

    @staticmethod
    def get_or_create_bank(name: str, code: str = None) -> Bank:
        """Get existing bank or create new one."""
        try:
            return Bank.get_or_create(name=name, code=code)
        except Exception as e:
            logger.error(f"Error getting or creating bank '{name}': {e}")
            raise

    @staticmethod
    def get_all_banks() -> List[Bank]:
        """Get all banks."""
        return Bank.get_all()

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

    @staticmethod
    def create_default_banks() -> None:
        """Create default banks if they don't exist."""
        default_banks = [
            {'name': '招商银行', 'code': 'CMB'},
            {'name': '建设银行', 'code': 'CCB'},
        ]
        
        created_count = 0
        for bank_data in default_banks:
            if not Bank.get_by_name(bank_data['name']):
                Bank.create(**bank_data)
                created_count += 1
        
        if created_count > 0:
            logger.info(f"Created {created_count} default banks")