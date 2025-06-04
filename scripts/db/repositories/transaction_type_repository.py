from scripts.db.repositories.base_repository import BaseRepository
from scripts.db.db_connection import DBConnection
from scripts.common.logging_setup import get_logger

logger = get_logger(__name__)
import sqlite3

class TransactionTypeRepository(BaseRepository):
    def __init__(self, db_connection: DBConnection):
        super().__init__(db_connection)

    def get_or_create_transaction_type(self, name, is_income=False):
        conn = self.db_connection.get_connection()
        if not conn:
            return None

        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id FROM transaction_types WHERE name = ?", (name,))
            ttype = cursor.fetchone()
            if ttype:
                return ttype['id']
            else:
                cursor.execute("INSERT INTO transaction_types (name, is_income) VALUES (?, ?) RETURNING id", (name, is_income))
                ttype_id = cursor.fetchone()['id']
                conn.commit()
                logger.info(f"Created new transaction type: {name} (Income: {is_income}) with ID: {ttype_id}")
                return ttype_id
        except sqlite3.Error as e:
            logger.error(f"Error getting or creating transaction type '{name}': {e}")
            conn.rollback()
            return None

    def get_transaction_type_by_id(self, type_id):
        return self._fetchone("SELECT * FROM transaction_types WHERE id = ?", (type_id,))

    def get_transaction_type_by_name(self, name):
        return self._fetchone("SELECT * FROM transaction_types WHERE name = ?", (name,))

    def get_all_transaction_types(self):
        return self._fetchall("SELECT * FROM transaction_types ORDER BY name")

    def update_transaction_type(self, type_id, new_name=None, new_is_income=None):
        updates = []
        params = []
        if new_name is not None:
            updates.append("name = ?")
            params.append(new_name)
        if new_is_income is not None:
            updates.append("is_income = ?")
            params.append(new_is_income)

        if not updates:
            logger.warning(f"No updates provided for transaction type ID {type_id}.")
            return False

        query = f"UPDATE transaction_types SET {', '.join(updates)} WHERE id = ?"
        params.append(type_id)

        cursor = self._execute_query(query, tuple(params), commit=True)
        if cursor and cursor.rowcount > 0:
            logger.info(f"Updated transaction type ID {type_id}.")
            return True
        logger.warning(f"Failed to update transaction type ID {type_id} or type not found.")
        return False

    def delete_transaction_type(self, type_id):
        # Consider adding a check for associated transactions before deleting
        query = "DELETE FROM transaction_types WHERE id = ?"
        cursor = self._execute_query(query, (type_id,), commit=True)
        if cursor and cursor.rowcount > 0:
            logger.info(f"Deleted transaction type ID: {type_id}")
            return True
        logger.warning(f"Failed to delete transaction type ID {type_id} or type not found.")
        return False

if __name__ == '__main__':
    # Example usage for testing
    import os

    test_db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'instance', 'test_ttype_repo.db'))
    
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
        print(f"Removed existing test DB: {test_db_path}")

    db_conn = DBConnection(test_db_path)
    db_conn.init_db() # Ensure tables are created and common types populated

    ttype_repo = TransactionTypeRepository(db_conn)

    # Test get_or_create_transaction_type
    type1_id = ttype_repo.get_or_create_transaction_type("Salary", True)
    print(f"Salary Type ID: {type1_id}")
    type2_id = ttype_repo.get_or_create_transaction_type("Groceries", False)
    print(f"Groceries Type ID: {type2_id}")
    type1_id_again = ttype_repo.get_or_create_transaction_type("Salary", True)
    print(f"Salary Type ID (again): {type1_id_again}")

    # Test get_transaction_type_by_id
    ttype1 = ttype_repo.get_transaction_type_by_id(type1_id)
    print(f"Type 1 by ID: {dict(ttype1) if ttype1 else 'Not found'}")

    # Test get_transaction_type_by_name
    ttype2 = ttype_repo.get_transaction_type_by_name("Groceries")
    print(f"Type 2 by Name: {dict(ttype2) if ttype2 else 'Not found'}")

    # Test get_all_transaction_types
    all_ttypes = ttype_repo.get_all_transaction_types()
    print("All Transaction Types:")
    for ttype in all_ttypes:
        print(f"  ID: {ttype['id']}, Name: {ttype['name']}, Income: {ttype['is_income']}")

    # Test update_transaction_type
    ttype_repo.update_transaction_type(type2_id, new_name="Food Expenses", new_is_income=False)
    ttype2_updated = ttype_repo.get_transaction_type_by_id(type2_id)
    print(f"Updated Type 2: {dict(ttype2_updated) if ttype2_updated else 'Not found'}")

    # Test delete_transaction_type
    ttype_repo.delete_transaction_type(type1_id)
    ttype1_deleted = ttype_repo.get_transaction_type_by_id(type1_id)
    print(f"Type 1 after deletion: {ttype1_deleted}")

    db_conn.close_connection()