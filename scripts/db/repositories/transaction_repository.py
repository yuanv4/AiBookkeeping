from scripts.db.repositories.base_repository import BaseRepository
from scripts.db.db_connection import DBConnection
from scripts.common.logging_setup import get_logger

logger = get_logger(__name__)
import sqlite3
from datetime import datetime

class TransactionRepository(BaseRepository):
    def __init__(self, db_connection: DBConnection):
        super().__init__(db_connection)

    def import_transactions(self, transactions_data):
        conn = self.db_connection.get_connection()
        if not conn:
            return 0

        cursor = conn.cursor()
        imported_count = 0
        try:
            for transaction in transactions_data:
                account_id = transaction.get('account_id')
                date = transaction.get('date')
                type_id = transaction.get('type_id')
                amount = transaction.get('amount')
                currency = transaction.get('currency', 'CNY')
                description = transaction.get('description')
                counterparty = transaction.get('counterparty')
                notes = transaction.get('notes')
                original_description = transaction.get('original_description')

                # Basic deduplication: check if a similar transaction exists within a small amount tolerance
                # This is a simplified deduplication. A more robust solution might involve hashing or unique transaction IDs.
                cursor.execute(
                    "SELECT id FROM transactions WHERE account_id = ? AND date = ? AND type_id = ? AND ABS(amount - ?) < 0.01 AND description = ?",
                    (account_id, date, type_id, amount, description)
                )
                if cursor.fetchone():
                    logger.debug(f"Skipping duplicate transaction: {description} on {date} for account {account_id}")
                    continue

                cursor.execute(
                    "INSERT INTO transactions (account_id, date, type_id, amount, currency, description, counterparty, notes, original_description) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (account_id, date, type_id, amount, currency, description, counterparty, notes, original_description)
                )
                imported_count += 1
            conn.commit()
            logger.info(f"Successfully imported {imported_count} new transactions.")
            return imported_count
        except sqlite3.Error as e:
            logger.error(f"Error importing transactions: {e}")
            conn.rollback()
            return 0

    def get_transactions(self, account_id=None, start_date=None, end_date=None, min_amount=None, max_amount=None, transaction_type_id=None, counterparty=None, notes=None, limit=None, offset=None, distinct=False, account_number=None, bank_id=None):
        select_clause = "SELECT DISTINCT t.*" if distinct else "SELECT t.*"
        query = f"""{select_clause}, tt.name as type_name, tt.is_income, a.account_number, a.account_name, b.name as bank_name
                   FROM transactions t
                   JOIN transaction_types tt ON t.type_id = tt.id
                   JOIN accounts a ON t.account_id = a.id
                   JOIN banks b ON a.bank_id = b.id
                """
        conditions = []
        params = []

        if account_id:
            conditions.append("t.account_id = ?")
            params.append(account_id)
        if account_number:
            conditions.append("a.account_number = ?")
            params.append(account_number)
        if bank_id:
            conditions.append("b.id = ?")
            params.append(bank_id)
        if start_date:
            conditions.append("t.date >= ?")
            params.append(start_date)
        if end_date:
            conditions.append("t.date <= ?")
            params.append(end_date)
        if min_amount is not None:
            conditions.append("t.amount >= ?")
            params.append(min_amount)
        if max_amount is not None:
            conditions.append("t.amount <= ?")
            params.append(max_amount)
        if transaction_type_id:
            conditions.append("t.type_id = ?")
            params.append(transaction_type_id)
        if counterparty:
            conditions.append("t.counterparty LIKE ?")
            params.append(f"%{counterparty}%")
        if notes:
            conditions.append("t.notes LIKE ?")
            params.append(f"%{notes}%")

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY t.date DESC, t.id DESC"

        if limit is not None:
            query += " LIMIT ?"
            params.append(limit)
        if offset is not None:
            query += " OFFSET ?"
            params.append(offset)

        return self._fetchall(query, tuple(params))

    def get_transactions_count(self, account_id=None, start_date=None, end_date=None, min_amount=None, max_amount=None, transaction_type_id=None, counterparty=None, notes=None, account_number=None, bank_id=None):
        query = """SELECT COUNT(t.id)
                   FROM transactions t
                   JOIN transaction_types tt ON t.type_id = tt.id
                   JOIN accounts a ON t.account_id = a.id
                   JOIN banks b ON a.bank_id = b.id
                """
        conditions = []
        params = []

        if account_id:
            conditions.append("t.account_id = ?")
            params.append(account_id)
        if account_number:
            conditions.append("a.account_number = ?")
            params.append(account_number)
        if bank_id:
            conditions.append("b.id = ?")
            params.append(bank_id)
        if start_date:
            conditions.append("t.date >= ?")
            params.append(start_date)
        if end_date:
            conditions.append("t.date <= ?")
            params.append(end_date)
        if min_amount is not None:
            conditions.append("t.amount >= ?")
            params.append(min_amount)
        if max_amount is not None:
            conditions.append("t.amount <= ?")
            params.append(max_amount)
        if transaction_type_id:
            conditions.append("t.type_id = ?")
            params.append(transaction_type_id)
        if counterparty:
            conditions.append("t.counterparty LIKE ?")
            params.append(f"%{counterparty}%")
        if notes:
            conditions.append("t.notes LIKE ?")
            params.append(f"%{notes}%")

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        result = self._fetchone(query, tuple(params))
        return result[0] if result else 0

    def get_distinct_column_values(self, column_name, table_name='transactions', filter_column=None, filter_value=None):
        if column_name not in ['description', 'counterparty', 'notes', 'currency']:
            logger.warning(f"Unsupported column for distinct values: {column_name}")
            return []

        query = f"SELECT DISTINCT {column_name} FROM {table_name}"
        params = []
        if filter_column and filter_value:
            query += f" WHERE {filter_column} = ?"
            params.append(filter_value)
        query += f" WHERE {column_name} IS NOT NULL AND {column_name} != '' ORDER BY {column_name}"

        return [row[0] for row in self._fetchall(query, tuple(params))]

    def export_transactions_to_csv(self, transactions, file_path):
        if not transactions:
            logger.warning("No transactions to export.")
            return False

        try:
            import csv
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = transactions[0].keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                writer.writeheader()
                for transaction in transactions:
                    writer.writerow(transaction)
            logger.info(f"Successfully exported {len(transactions)} transactions to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error exporting transactions to CSV: {e}")
            return False

if __name__ == '__main__':
    # Example usage for testing
    import os
    from scripts.db.repositories.bank_repository import BankRepository
    from scripts.db.repositories.account_repository import AccountRepository
    from scripts.db.repositories.transaction_type_repository import TransactionTypeRepository

    test_db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'instance', 'test_transaction_repo.db'))
    
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
        print(f"Removed existing test DB: {test_db_path}")

    db_conn = DBConnection(test_db_path)
    db_conn.init_db() # Ensure tables are created

    bank_repo = BankRepository(db_conn)
    account_repo = AccountRepository(db_conn)
    ttype_repo = TransactionTypeRepository(db_conn)
    transaction_repo = TransactionRepository(db_conn)

    # Setup test data
    bank_id = bank_repo.get_or_create_bank("Test Bank D")
    account_id = account_repo.get_or_create_account(bank_id, "622200000003", "Main Account")
    income_type_id = ttype_repo.get_or_create_transaction_type("Salary", True)
    expense_type_id = ttype_repo.get_or_create_transaction_type("Food", False)

    test_transactions = [
        {'account_id': account_id, 'date': '2023-01-01', 'type_id': income_type_id, 'amount': 5000.00, 'description': 'Monthly Salary', 'counterparty': 'Employer', 'original_description': 'Salary Jan'},
        {'account_id': account_id, 'date': '2023-01-05', 'type_id': expense_type_id, 'amount': -50.00, 'description': 'Groceries', 'counterparty': 'Supermarket', 'original_description': 'Food bill'},
        {'account_id': account_id, 'date': '2023-01-10', 'type_id': expense_type_id, 'amount': -120.00, 'description': 'Dinner', 'counterparty': 'Restaurant', 'original_description': 'Dinner out'},
        {'account_id': account_id, 'date': '2023-02-01', 'type_id': income_type_id, 'amount': 5000.00, 'description': 'Monthly Salary', 'counterparty': 'Employer', 'original_description': 'Salary Feb'},
        {'account_id': account_id, 'date': '2023-02-05', 'type_id': expense_type_id, 'amount': -75.00, 'description': 'Groceries', 'counterparty': 'Supermarket', 'original_description': 'Food bill'},
    ]

    # Test import_transactions
    imported_count = transaction_repo.import_transactions(test_transactions)
    print(f"Imported {imported_count} transactions.")

    # Test get_transactions
    all_transactions = transaction_repo.get_transactions(account_id=account_id)
    print("All Transactions:")
    for t in all_transactions:
        print(f"  {t['date']} | {t['type_name']} | {t['amount']} | {t['description']} | {t['account_number']}")

    # Test get_transactions with filters
    filtered_transactions = transaction_repo.get_transactions(account_id=account_id, start_date='2023-01-01', end_date='2023-01-31', min_amount=-100.00, max_amount=0.00)
    print("Filtered Transactions (Jan expenses > -100):")
    for t in filtered_transactions:
        print(f"  {t['date']} | {t['type_name']} | {t['amount']} | {t['description']}")

    # Test get_transactions_count
    count = transaction_repo.get_transactions_count(account_id=account_id)
    print(f"Total transactions count: {count}")
    count_filtered = transaction_repo.get_transactions_count(account_id=account_id, transaction_type_id=income_type_id)
    print(f"Income transactions count: {count_filtered}")

    # Test get_distinct_column_values
    distinct_descriptions = transaction_repo.get_distinct_column_values('description')
    print(f"Distinct Descriptions: {distinct_descriptions}")

    # Test export_transactions_to_csv
    export_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'instance', 'exported_transactions.csv'))
    if os.path.exists(export_file):
        os.remove(export_file)
    
    # Need to convert Row objects to dicts for csv.DictWriter
    transactions_for_export = [dict(t) for t in all_transactions]
    transaction_repo.export_transactions_to_csv(transactions_for_export, export_file)

    db_conn.close_connection()