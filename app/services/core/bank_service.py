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
    def get_or_create_bank(name: str, code: str = None, country: str = 'CN') -> Bank:
        """Get existing bank or create new one."""
        try:
            return Bank.get_or_create(name=name, code=code, country=country)
        except Exception as e:
            logger.error(f"Error getting or creating bank '{name}': {e}")
            raise

    @staticmethod
    def get_all_banks(active_only: bool = True) -> List[Bank]:
        """Get all banks."""
        if active_only:
            return Bank.get_active_banks()
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
    def delete_bank(bank_id: int, soft_delete: bool = True) -> bool:
        """Delete bank (soft delete by default)."""
        try:
            bank = Bank.get_by_id(bank_id)
            if bank:
                if soft_delete:
                    bank.deactivate()
                else:
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
            {'name': '中国工商银行', 'code': 'ICBC', 'country': 'CN'},
            {'name': '中国建设银行', 'code': 'CCB', 'country': 'CN'},
            {'name': '中国农业银行', 'code': 'ABC', 'country': 'CN'},
            {'name': '中国银行', 'code': 'BOC', 'country': 'CN'},
            {'name': '招商银行', 'code': 'CMB', 'country': 'CN'},
            {'name': '交通银行', 'code': 'BOCOM', 'country': 'CN'},
            {'name': '中信银行', 'code': 'CITIC', 'country': 'CN'},
            {'name': '中国光大银行', 'code': 'CEB', 'country': 'CN'},
            {'name': '华夏银行', 'code': 'HXB', 'country': 'CN'},
            {'name': '中国民生银行', 'code': 'CMBC', 'country': 'CN'},
            {'name': '平安银行', 'code': 'PAB', 'country': 'CN'},
            {'name': '兴业银行', 'code': 'CIB', 'country': 'CN'},
            {'name': '浦发银行', 'code': 'SPDB', 'country': 'CN'},
        ]
        
        created_count = 0
        for bank_data in default_banks:
            if not Bank.get_by_name(bank_data['name']):
                Bank.create(**bank_data)
                created_count += 1
        
        if created_count > 0:
            logger.info(f"Created {created_count} default banks")