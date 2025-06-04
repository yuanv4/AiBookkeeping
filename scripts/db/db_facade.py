from scripts.db.db_connection import DBConnection
from scripts.db.repositories.bank_repository import BankRepository
from scripts.db.repositories.account_repository import AccountRepository
from scripts.db.repositories.transaction_type_repository import TransactionTypeRepository
from scripts.db.repositories.transaction_repository import TransactionRepository
from scripts.db.services.financial_analyzer import FinancialAnalyzer

class DBFacade:
    def __init__(self, db_path=None):
        # DBConnection 现在是线程安全的，每个线程会获取自己的连接
        self.db_connection = DBConnection(db_path)
        self.bank_repo = BankRepository(self.db_connection)
        self.account_repo = AccountRepository(self.db_connection)
        self.transaction_type_repo = TransactionTypeRepository(self.db_connection)
        self.transaction_repo = TransactionRepository(self.db_connection)
        self.financial_analyzer = FinancialAnalyzer(self.db_connection)

    def init_db(self):
        self.db_connection.init_db()

    def close_connection(self):
        self.db_connection.close_connection()

    # --- Bank Repository Methods ---
    def get_or_create_bank(self, name):
        return self.bank_repo.get_or_create_bank(name)

    def get_bank_by_id(self, bank_id):
        return self.bank_repo.get_bank_by_id(bank_id)

    def get_bank_by_name(self, name):
        return self.bank_repo.get_bank_by_name(name)

    def get_all_banks(self):
        return self.bank_repo.get_all_banks()

    def update_bank_name(self, bank_id, new_name):
        return self.bank_repo.update_bank_name(bank_id, new_name)

    def delete_bank(self, bank_id):
        return self.bank_repo.delete_bank(bank_id)

    # --- Account Repository Methods ---
    def get_or_create_account(self, bank_id, account_number, account_name, currency='CNY'):
        return self.account_repo.get_or_create_account(bank_id, account_number, account_name, currency)

    def get_account_by_id(self, account_id):
        return self.account_repo.get_account_by_id(account_id)

    def get_accounts_by_bank_id(self, bank_id):
        return self.account_repo.get_accounts_by_bank_id(bank_id)

    def get_all_accounts(self):
        return self.account_repo.get_all_accounts()

    def update_account(self, account_id, new_account_number=None, new_account_name=None, new_currency=None):
        return self.account_repo.update_account(account_id, new_account_number, new_account_name, new_currency)

    def delete_account(self, account_id):
        return self.account_repo.delete_account(account_id)

    # --- Transaction Type Repository Methods ---
    def get_or_create_transaction_type(self, name, is_income):
        return self.transaction_type_repo.get_or_create_transaction_type(name, is_income)

    def get_transaction_type_by_id(self, type_id):
        return self.transaction_type_repo.get_transaction_type_by_id(type_id)

    def get_transaction_type_by_name(self, name):
        return self.transaction_type_repo.get_transaction_type_by_name(name)

    def get_all_transaction_types(self):
        return self.transaction_type_repo.get_all_transaction_types()

    def update_transaction_type(self, type_id, new_name=None, new_is_income=None):
        return self.transaction_type_repo.update_transaction_type(type_id, new_name, new_is_income)

    def delete_transaction_type(self, type_id):
        return self.transaction_type_repo.delete_transaction_type(type_id)

    # --- Transaction Repository Methods ---
    def import_transactions(self, transactions_data):
        return self.transaction_repo.import_transactions(transactions_data)

    def get_transactions(self, account_id=None, account_number=None, start_date=None, end_date=None,
                         transaction_type_id=None, min_amount=None, max_amount=None,
                         description_keyword=None, counterparty_keyword=None,
                         is_income=None, limit=None, offset=None, distinct=False):
        return self.transaction_repo.get_transactions(account_id, account_number, start_date, end_date,
                                                     transaction_type_id, min_amount, max_amount,
                                                     description_keyword, counterparty_keyword,
                                                     is_income, limit, offset, distinct)

    def get_transactions_count(self, account_id=None, account_number=None, start_date=None, end_date=None,
                               transaction_type_id=None, min_amount=None, max_amount=None,
                               description_keyword=None, counterparty_keyword=None, is_income=None):
        return self.transaction_repo.get_transactions_count(account_id, account_number, start_date, end_date,
                                                           transaction_type_id, min_amount, max_amount,
                                                           description_keyword, counterparty_keyword, is_income)

    def get_distinct_column_values(self, column_name, table_name='transactions'):
        return self.transaction_repo.get_distinct_column_values(column_name, table_name)

    def export_transactions_to_csv(self, file_path, account_id=None, start_date=None, end_date=None):
        return self.transaction_repo.export_transactions_to_csv(file_path, account_id, start_date, end_date)

    # --- Financial Analyzer Methods ---
    def get_balance_summary(self, account_id=None, account_number=None):
        return self.financial_analyzer.get_balance_summary(account_id, account_number)

    def get_general_statistics(self):
        return self.financial_analyzer.get_general_statistics()

    def get_balance_range(self, account_id=None, account_number=None):
        return self.financial_analyzer.get_balance_range(account_id, account_number)

    def get_monthly_balance_history(self, account_id=None, account_number=None, months=12):
        return self.financial_analyzer.get_monthly_balance_history(account_id, account_number, months)

    def get_income_expense_balance(self, account_id=None, account_number=None, period_type='monthly', periods=12):
        return self.financial_analyzer.get_income_expense_balance(account_id, account_number, period_type, periods)

    def get_income_stability(self, account_id=None, account_number=None, months=12):
        return self.financial_analyzer.get_income_stability(account_id, account_number, months)

    def get_income_diversity(self, account_id=None, account_number=None, months=12):
        return self.financial_analyzer.get_income_diversity(account_id, account_number, months)

    def get_cash_flow_health(self, account_id=None, account_number=None, months=12):
        return self.financial_analyzer.get_cash_flow_health(account_id, account_number, months)

    def get_income_growth(self, account_id=None, account_number=None, periods=4, period_type='quarterly'):
        return self.financial_analyzer.get_income_growth(account_id, account_number, periods, period_type)

    def get_financial_resilience(self, account_id=None, account_number=None, months=12):
        return self.financial_analyzer.get_financial_resilience(account_id, account_number, months)

if __name__ == '__main__':
    import os
    test_db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'instance', 'test_db_facade.db'))
    
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
        print(f"Removed existing test DB: {test_db_path}")

    facade = DBFacade(test_db_path)
    facade.init_db()

    # Example Usage
    bank_id = facade.get_or_create_bank("Facade Bank")
    account_id = facade.get_or_create_account(bank_id, "123456789", "Facade Checking")
    income_type_id = facade.get_or_create_transaction_type("Salary", True)
    expense_type_id = facade.get_or_create_transaction_type("Groceries", False)

    transactions_data = [
        {'account_id': account_id, 'date': '2023-01-01', 'type_id': income_type_id, 'amount': 3000.00, 'currency': 'CNY', 'description': 'Monthly Salary', 'counterparty': 'Employer', 'notes': '', 'original_description': 'Salary'},
        {'account_id': account_id, 'date': '2023-01-05', 'type_id': expense_type_id, 'amount': -150.00, 'currency': 'CNY', 'description': 'Weekly Groceries', 'counterparty': 'Supermarket', 'notes': '', 'original_description': 'Groceries'},
        {'account_id': account_id, 'date': '2023-02-01', 'type_id': income_type_id, 'amount': 3200.00, 'currency': 'CNY', 'description': 'Monthly Salary', 'counterparty': 'Employer', 'notes': '', 'original_description': 'Salary'},
        {'account_id': account_id, 'date': '2023-02-10', 'type_id': expense_type_id, 'amount': -200.00, 'currency': 'CNY', 'description': 'Restaurant', 'counterparty': 'Restaurant', 'notes': '', 'original_description': 'Restaurant'},
    ]
    facade.import_transactions(transactions_data)

    print("\n--- All Accounts ---")
    print(facade.get_all_accounts())

    print("\n--- All Transactions ---")
    print(facade.get_transactions(account_id=account_id))

    print("\n--- Balance Summary ---")
    print(facade.get_balance_summary(account_id=account_id))

    facade.close_connection()
    print("\nDBFacade example finished.")