from scripts.db.repositories.base_repository import BaseRepository
from scripts.db.db_connection import DBConnection
from scripts.common.logging_setup import get_logger

logger = get_logger(__name__)
import sqlite3

class BankRepository(BaseRepository):
    def __init__(self, db_connection: DBConnection):
        super().__init__(db_connection)

    def get_or_create_bank(self, name):
        conn = self.db_connection.get_connection()
        if not conn:
            return None

        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id FROM banks WHERE name = ?", (name,))
            bank = cursor.fetchone()
            if bank:
                return bank['id']
            else:
                cursor.execute("INSERT INTO banks (name) VALUES (?) RETURNING id", (name,))
                bank_id = cursor.fetchone()['id']
                conn.commit()
                logger.info(f"Created new bank: {name} with ID: {bank_id}")
                return bank_id
        except sqlite3.Error as e:
            logger.error(f"Error getting or creating bank '{name}': {e}")
            conn.rollback()
            return None

    def get_bank_by_id(self, bank_id):
        return self._fetchone("SELECT * FROM banks WHERE id = ?", (bank_id,))

    def get_bank_by_name(self, name):
        return self._fetchone("SELECT * FROM banks WHERE name = ?", (name,))

    def get_all_banks(self):
        return self._fetchall("SELECT * FROM banks ORDER BY name")

    def update_bank_name(self, bank_id, new_name):
        query = "UPDATE banks SET name = ? WHERE id = ?"
        cursor = self._execute_query(query, (new_name, bank_id), commit=True)
        if cursor and cursor.rowcount > 0:
            logger.info(f"Updated bank ID {bank_id} to new name: {new_name}")
            return True
        logger.warning(f"Failed to update bank ID {bank_id} or bank not found.")
        return False

    def delete_bank(self, bank_id):
        # Consider adding a check for associated accounts before deleting
        query = "DELETE FROM banks WHERE id = ?"
        cursor = self._execute_query(query, (bank_id,), commit=True)
        if cursor and cursor.rowcount > 0:
            logger.info(f"Deleted bank ID: {bank_id}")
            return True
        logger.warning(f"Failed to delete bank ID {bank_id} or bank not found.")
        return False

if __name__ == '__main__':
    # Example usage for testing
    import os
    test_db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'instance', 'test_bank_repo.db'))
    
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
        print(f"Removed existing test DB: {test_db_path}")

    db_conn = DBConnection(test_db_path)
    db_conn.init_db() # Ensure tables are created

    bank_repo = BankRepository(db_conn)

    # Test get_or_create_bank
    bank1_id = bank_repo.get_or_create_bank("Test Bank A")
    print(f"Test Bank A ID: {bank1_id}")
    bank2_id = bank_repo.get_or_create_bank("Test Bank B")
    print(f"Test Bank B ID: {bank2_id}")
    bank1_id_again = bank_repo.get_or_create_bank("Test Bank A")
    print(f"Test Bank A ID (again): {bank1_id_again}")

    # Test get_bank_by_id
    bank_a = bank_repo.get_bank_by_id(bank1_id)
    print(f"Bank A by ID: {dict(bank_a) if bank_a else 'Not found'}")

    # Test get_bank_by_name
    bank_b = bank_repo.get_bank_by_name("Test Bank B")
    print(f"Bank B by Name: {dict(bank_b) if bank_b else 'Not found'}")

    # Test get_all_banks
    all_banks = bank_repo.get_all_banks()
    print("All Banks:")
    for bank in all_banks:
        print(f"  ID: {bank['id']}, Name: {bank['name']}")

    # Test update_bank_name
    bank_repo.update_bank_name(bank1_id, "Updated Test Bank A")
    bank_a_updated = bank_repo.get_bank_by_id(bank1_id)
    print(f"Updated Bank A: {dict(bank_a_updated) if bank_a_updated else 'Not found'}")

    # Test delete_bank
    bank_repo.delete_bank(bank2_id)
    bank_b_deleted = bank_repo.get_bank_by_id(bank2_id)
    print(f"Bank B after deletion: {bank_b_deleted}")

    db_conn.close_connection()