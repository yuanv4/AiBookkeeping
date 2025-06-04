from scripts.db.db_connection import DBConnection
from scripts.common.logging_setup import get_logger

logger = get_logger(__name__)
import sqlite3

class BaseRepository:
    def __init__(self, db_connection: DBConnection):
        self.db_connection = db_connection

    def _get_cursor(self):
        conn = self.db_connection.get_connection()
        if conn:
            return conn.cursor()
        logger.error("Failed to get database cursor: No connection.")
        return None

    def _execute_query(self, query, params=None, commit=False):
        conn = self.db_connection.get_connection()
        if not conn:
            logger.error("Cannot execute query: No database connection.")
            return None
        
        cursor = conn.cursor()
        try:
            cursor.execute(query, params or ())
            if commit:
                conn.commit()
            logger.debug(f"Executed query: {query} with params: {params}")
            return cursor
        except sqlite3.Error as e:
            logger.error(f"Database error during query execution: {e}\nQuery: {query}\nParams: {params}")
            if conn: # Check if conn is still valid before rollback
                conn.rollback()
            return None

    def _fetchone(self, query, params=None):
        cursor = self._execute_query(query, params)
        if cursor:
            return cursor.fetchone()
        return None

    def _fetchall(self, query, params=None):
        cursor = self._execute_query(query, params)
        if cursor:
            return cursor.fetchall()
        return []

    def _get_last_row_id(self, cursor):
        if cursor:
            return cursor.lastrowid
        return None

if __name__ == '__main__':
    # This is a base class and typically not instantiated directly for standalone use.
    # Example of how it might be used by a subclass (conceptual)
    print("BaseRepository is a base class and should be inherited by specific repositories.")
    
    # To run a simple test, one might do the following (requires a DB setup):
    # from scripts.db.db_connection import DBConnection
    # import os
    # test_db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'instance', 'test_repo.db'))
    # if os.path.exists(test_db_path):
    #     os.remove(test_db_path)
    # db_conn_instance = DBConnection(test_db_path)
    # db_conn_instance.init_db() # Ensure tables are created
    
    # class TestRepo(BaseRepository):
    #     def __init__(self, db_conn):
    #         super().__init__(db_conn)
        
    #     def get_test_data(self):
    #         return self._fetchall("SELECT * FROM banks LIMIT 1")

    # if db_conn_instance.get_connection():
    #     repo = TestRepo(db_conn_instance)
    #     data = repo.get_test_data()
    #     if data:
    #         print(f"Test data fetched: {data}")
    #     else:
    #         print("Failed to fetch test data or no data available.")
    #     db_conn_instance.close_connection()
    # else:
    #     print("Failed to establish DB connection for test.")