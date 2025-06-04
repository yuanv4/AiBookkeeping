from scripts.db.repositories.base_repository import BaseRepository
from scripts.db.db_connection import DBConnection
from scripts.common.logging_setup import get_logger

logger = get_logger(__name__)
import sqlite3

class AccountRepository(BaseRepository):
    def __init__(self, db_connection: DBConnection):
        super().__init__(db_connection)

    def get_or_create_account(self, bank_id, account_number, account_name=None, currency='CNY'):
        conn = self.db_connection.get_connection()
        if not conn:
            return None

        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT id FROM accounts WHERE bank_id = ? AND account_number = ?",
                (bank_id, account_number)
            )
            account = cursor.fetchone()
            if account:
                return account['id']
            else:
                cursor.execute(
                    "INSERT INTO accounts (bank_id, account_number, account_name, currency) VALUES (?, ?, ?, ?) RETURNING id",
                    (bank_id, account_number, account_name, currency)
                )
                account_id = cursor.fetchone()['id']
                conn.commit()
                logger.info(f"Created new account: {account_number} for bank ID {bank_id} with ID: {account_id}")
                return account_id
        except sqlite3.Error as e:
            logger.error(f"Error getting or creating account '{account_number}' for bank ID {bank_id}: {e}")
            conn.rollback()
            return None

    def get_account_by_id(self, account_id):
        return self._fetchone("SELECT * FROM accounts WHERE id = ?", (account_id,))

    def get_accounts_by_bank_id(self, bank_id):
        return self._fetchall("SELECT * FROM accounts WHERE bank_id = ? ORDER BY account_number", (bank_id,))

    def get_all_accounts(self):
        return self._fetchall("SELECT a.*, b.name as bank_name FROM accounts a JOIN banks b ON a.bank_id = b.id ORDER BY b.name, a.account_number")

    def update_account(self, account_id, account_name=None, currency=None):
        updates = []
        params = []
        if account_name is not None:
            updates.append("account_name = ?")
            params.append(account_name)
        if currency is not None:
            updates.append("currency = ?")
            params.append(currency)

        if not updates:
            logger.warning(f"No updates provided for account ID {account_id}.")
            return False

        query = f"UPDATE accounts SET {', '.join(updates)} WHERE id = ?"
        params.append(account_id)

        cursor = self._execute_query(query, tuple(params), commit=True)
        if cursor and cursor.rowcount > 0:
            logger.info(f"Updated account ID {account_id}.")
            return True
        logger.warning(f"Failed to update account ID {account_id} or account not found.")
        return False

    def delete_account(self, account_id):
        # Consider adding a check for associated transactions before deleting
        query = "DELETE FROM accounts WHERE id = ?"
        cursor = self._execute_query(query, (account_id,), commit=True)
        if cursor and cursor.rowcount > 0:
            logger.info(f"Deleted account ID: {account_id}")
            return True
        logger.warning(f"Failed to delete account ID {account_id} or account not found.")
        return False

if __name__ == '__main__':
    # Example usage for testing
    import os
    from scripts.db.repositories.bank_repository import BankRepository

    test_db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'instance', 'test_account_repo.db'))
    
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
        print(f"Removed existing test DB: {test_db_path}")

    db_conn = DBConnection(test_db_path)
    db_conn.init_db() # Ensure tables are created

    bank_repo = BankRepository(db_conn)
    account_repo = AccountRepository(db_conn)

    # Create a bank first
    bank_id = bank_repo.get_or_create_bank("Test Bank C")
    print(f"Test Bank C ID: {bank_id}")

    if bank_id:
        # Test get_or_create_account
        acc1_id = account_repo.get_or_create_account(bank_id, "622200000001", "Savings Account", "USD")
        print(f"Account 1 ID: {acc1_id}")
        acc2_id = account_repo.get_or_create_account(bank_id, "622200000002", "Checking Account")
        print(f"Account 2 ID: {acc2_id}")
        acc1_id_again = account_repo.get_or_create_account(bank_id, "622200000001", "Savings Account", "USD")
        print(f"Account 1 ID (again): {acc1_id_again}")

        # Test get_account_by_id
        acc1 = account_repo.get_account_by_id(acc1_id)
        print(f"Account 1 by ID: {dict(acc1) if acc1 else 'Not found'}")

        # Test get_accounts_by_bank_id
        bank_accounts = account_repo.get_accounts_by_bank_id(bank_id)
        print("Accounts for Test Bank C:")
        for acc in bank_accounts:
            print(f"  ID: {acc['id']}, Number: {acc['account_number']}, Name: {acc['account_name']}")

        # Test get_all_accounts
        all_accounts = account_repo.get_all_accounts()
        print("All Accounts:")
        for acc in all_accounts:
            print(f"  ID: {acc['id']}, Bank: {acc['bank_name']}, Number: {acc['account_number']}, Name: {acc['account_name']}")

        # Test update_account
        account_repo.update_account(acc1_id, account_name="Updated Savings", currency="EUR")
        acc1_updated = account_repo.get_account_by_id(acc1_id)
        print(f"Updated Account 1: {dict(acc1_updated) if acc1_updated else 'Not found'}")

        # Test delete_account
        account_repo.delete_account(acc2_id)
        acc2_deleted = account_repo.get_account_by_id(acc2_id)
        print(f"Account 2 after deletion: {acc2_deleted}")

    db_conn.close_connection()