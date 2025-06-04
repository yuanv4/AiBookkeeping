import sqlite3
from datetime import datetime, timedelta
from collections import defaultdict

from scripts.db.db_connection import DBConnection
from scripts.db.repositories.transaction_repository import TransactionRepository
from scripts.db.repositories.account_repository import AccountRepository
from scripts.common.logging_setup import get_logger

logger = get_logger(__name__)

class FinancialAnalyzer:
    def __init__(self, db_connection: DBConnection):
        self.db_connection = db_connection
        self.transaction_repo = TransactionRepository(db_connection)
        self.account_repo = AccountRepository(db_connection)

    def _get_transactions_for_analysis(self, account_id=None, account_number=None, start_date=None, end_date=None):
        # Helper to fetch transactions for various analysis methods
        return self.transaction_repo.get_transactions(
            account_id=account_id,
            account_number=account_number,
            start_date=start_date,
            end_date=end_date
        )

    def get_balance_summary(self, account_id=None, account_number=None):
        conn = self.db_connection.get_connection()
        if not conn:
            return None

        cursor = conn.cursor()
        summary = {
            'total_income': 0.0,
            'total_expense': 0.0,
            'net_balance': 0.0,
            'account_balances': {}
        }

        try:
            # Get overall income and expense
            base_query = """SELECT SUM(CASE WHEN tt.is_income = 1 THEN t.amount ELSE 0 END) as total_income,
                                  SUM(CASE WHEN tt.is_income = 0 THEN t.amount ELSE 0 END) as total_expense
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
            elif account_number:
                conditions.append("a.account_number = ?")
                params.append(account_number)

            if conditions:
                base_query += " WHERE " + " AND ".join(conditions)

            cursor.execute(base_query, params)
            overall_summary = cursor.fetchone()

            if overall_summary:
                summary['total_income'] = overall_summary['total_income'] if overall_summary['total_income'] is not None else 0.0
                summary['total_expense'] = overall_summary['total_expense'] if overall_summary['total_expense'] is not None else 0.0
                summary['net_balance'] = summary['total_income'] + summary['total_expense'] # expense is negative

            # Get balance for each account
            account_balance_query = """SELECT a.id, a.account_name, a.account_number, a.currency,
                                          SUM(t.amount) as current_balance
                                   FROM transactions t
                                   JOIN accounts a ON t.account_id = a.id
                                   GROUP BY a.id, a.account_name, a.account_number, a.currency
                                """
            cursor.execute(account_balance_query)
            account_balances = cursor.fetchall()

            for acc_bal in account_balances:
                summary['account_balances'][acc_bal['account_number']] = {
                    'account_name': acc_bal['account_name'],
                    'currency': acc_bal['currency'],
                    'balance': acc_bal['current_balance'] if acc_bal['current_balance'] is not None else 0.0
                }
            return summary
        except sqlite3.Error as e:
            logger.error(f"Error getting balance summary: {e}")
            return None

    def get_general_statistics(self):
        conn = self.db_connection.get_connection()
        if not conn:
            return None

        cursor = conn.cursor()
        stats = {
            'total_transactions': 0,
            'total_accounts': 0,
            'first_transaction_date': None,
            'last_transaction_date': None,
            'average_transaction_amount': 0.0,
            'largest_income': 0.0,
            'largest_expense': 0.0
        }

        try:
            cursor.execute("SELECT COUNT(id) FROM transactions")
            stats['total_transactions'] = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(id) FROM accounts")
            stats['total_accounts'] = cursor.fetchone()[0]

            cursor.execute("SELECT MIN(date), MAX(date) FROM transactions")
            date_range = cursor.fetchone()
            if date_range:
                stats['first_transaction_date'] = date_range[0]
                stats['last_transaction_date'] = date_range[1]

            cursor.execute("SELECT AVG(amount) FROM transactions")
            avg_amount = cursor.fetchone()[0]
            stats['average_transaction_amount'] = avg_amount if avg_amount is not None else 0.0

            cursor.execute("SELECT MAX(amount) FROM transactions WHERE amount > 0")
            largest_income = cursor.fetchone()[0]
            stats['largest_income'] = largest_income if largest_income is not None else 0.0

            cursor.execute("SELECT MIN(amount) FROM transactions WHERE amount < 0")
            largest_expense = cursor.fetchone()[0]
            stats['largest_expense'] = largest_expense if largest_expense is not None else 0.0

            return stats
        except sqlite3.Error as e:
            logger.error(f"Error getting general statistics: {e}")
            return None

    def get_balance_range(self, account_id=None, account_number=None):
        conn = self.db_connection.get_connection()
        if not conn:
            return None

        cursor = conn.cursor()
        query = """SELECT MIN(t.amount) as min_amount, MAX(t.amount) as max_amount
                   FROM transactions t
                   JOIN accounts a ON t.account_id = a.id
                """
        conditions = []
        params = []

        if account_id:
            conditions.append("t.account_id = ?")
            params.append(account_id)
        elif account_number:
            conditions.append("a.account_number = ?")
            params.append(account_number)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        try:
            cursor.execute(query, params)
            result = cursor.fetchone()
            return {'min_amount': result['min_amount'], 'max_amount': result['max_amount']} if result else {'min_amount': 0.0, 'max_amount': 0.0}
        except sqlite3.Error as e:
            logger.error(f"Error getting balance range: {e}")
            return None

    def get_monthly_balance_history(self, account_id=None, account_number=None, months=12):
        conn = self.db_connection.get_connection()
        if not conn:
            return []

        history = []
        today = datetime.now()
        for i in range(months):
            month_start = (today - timedelta(days=30*i)).replace(day=1)
            month_end = (month_start + timedelta(days=31)).replace(day=1) - timedelta(days=1)

            query = """SELECT SUM(t.amount) FROM transactions t
                       JOIN accounts a ON t.account_id = a.id
                       WHERE t.date BETWEEN ? AND ?
                    """
            conditions = []
            params = [month_start.strftime('%Y-%m-%d'), month_end.strftime('%Y-%m-%d')]

            if account_id:
                conditions.append("t.account_id = ?")
                params.append(account_id)
            elif account_number:
                conditions.append("a.account_number = ?")
                params.append(account_number)

            if conditions:
                query += " AND " + " AND ".join(conditions)

            cursor = conn.cursor()
            try:
                cursor.execute(query, params)
                balance = cursor.fetchone()[0]
                history.append({
                    'month': month_start.strftime('%Y-%m'),
                    'balance': balance if balance is not None else 0.0
                })
            except sqlite3.Error as e:
                logger.error(f"Error getting monthly balance for {month_start.strftime('%Y-%m')}: {e}")
                history.append({'month': month_start.strftime('%Y-%m'), 'balance': 0.0})
        return list(reversed(history))

    def get_income_expense_balance(self, account_id=None, account_number=None, period_type='monthly', periods=12):
        conn = self.db_connection.get_connection()
        if not conn:
            return None

        results = defaultdict(lambda: {'income': 0.0, 'expense': 0.0, 'net': 0.0})
        all_transactions = self._get_transactions_for_analysis(account_id=account_id, account_number=account_number)

        for t in all_transactions:
            trans_date = datetime.strptime(t['date'], '%Y-%m-%d')
            key = None
            if period_type == 'monthly':
                key = trans_date.strftime('%Y-%m')
            elif period_type == 'quarterly':
                quarter = (trans_date.month - 1) // 3 + 1
                key = f"{trans_date.year}-Q{quarter}"
            elif period_type == 'yearly':
                key = str(trans_date.year)
            else:
                continue

            if t['is_income']:
                results[key]['income'] += t['amount']
            else:
                results[key]['expense'] += t['amount']
            results[key]['net'] += t['amount']

        # Sort results by key (date/period)
        sorted_results = sorted(results.items())

        # Calculate saving rate and necessary expense coverage
        total_income_all = sum(v['income'] for k, v in sorted_results)
        total_expense_all = sum(v['expense'] for k, v in sorted_results)
        net_balance_all = total_income_all + total_expense_all

        saving_rate = (net_balance_all / total_income_all * 100) if total_income_all > 0 else 0.0
        # Assuming 'necessary expense' is a subset of total expense, for simplicity, let's use total expense
        # In a real app, you'd categorize expenses as necessary/discretionary
        necessary_expense_coverage = (total_income_all / abs(total_expense_all)) if total_expense_all < 0 else float('inf')

        return {
            'period_data': [{period: k, **data} for k, data in sorted_results],
            'overall_summary': {
                'total_income': total_income_all,
                'total_expense': total_expense_all,
                'net_balance': net_balance_all,
                'saving_rate': saving_rate,
                'necessary_expense_coverage': necessary_expense_coverage
            }
        }

    def get_income_stability(self, account_id=None, account_number=None, months=12):
        income_data = defaultdict(float)
        all_transactions = self._get_transactions_for_analysis(account_id=account_id, account_number=account_number)

        for t in all_transactions:
            if t['is_income']:
                month = datetime.strptime(t['date'], '%Y-%m-%d').strftime('%Y-%m')
                income_data[month] += t['amount']

        if not income_data:
            return {
                'monthly_income': [],
                'average_monthly_income': 0.0,
                'income_volatility_cv': 0.0,
                'salary_income_ratio': 0.0,
                'periods_without_income': 0
            }

        # Fill in missing months with 0 income for a continuous history
        sorted_months = sorted(income_data.keys())
        if not sorted_months:
            return {}

        start_date = datetime.strptime(sorted_months[0], '%Y-%m')
        end_date = datetime.strptime(sorted_months[-1], '%Y-%m')

        current_date = start_date
        full_income_history = []
        while current_date <= end_date:
            month_str = current_date.strftime('%Y-%m')
            full_income_history.append({'month': month_str, 'income': income_data.get(month_str, 0.0)})
            # Move to next month
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)

        monthly_incomes = [item['income'] for item in full_income_history]

        # Calculate average monthly income
        avg_monthly_income = sum(monthly_incomes) / len(monthly_incomes) if monthly_incomes else 0.0

        # Calculate income volatility (Coefficient of Variation)
        if len(monthly_incomes) > 1 and avg_monthly_income != 0:
            variance = sum([(x - avg_monthly_income) ** 2 for x in monthly_incomes]) / (len(monthly_incomes) - 1)
            std_dev = variance ** 0.5
            income_volatility_cv = std_dev / avg_monthly_income
        else:
            income_volatility_cv = 0.0

        # Calculate salary income ratio (assuming '工资' is salary type)
        salary_income = 0.0
        total_income = 0.0
        for t in all_transactions:
            if t['is_income']:
                total_income += t['amount']
                if t['type_name'] == '工资': # Assuming '工资' is the salary type name
                    salary_income += t['amount']
        salary_income_ratio = (salary_income / total_income) if total_income > 0 else 0.0

        # Periods without income
        periods_without_income = sum(1 for income in monthly_incomes if income == 0)

        return {
            'monthly_income_history': full_income_history,
            'average_monthly_income': avg_monthly_income,
            'income_volatility_cv': income_volatility_cv,
            'salary_income_ratio': salary_income_ratio,
            'periods_without_income': periods_without_income
        }

    def get_income_diversity(self, account_id=None, account_number=None, months=12):
        income_sources = defaultdict(float)
        all_transactions = self._get_transactions_for_analysis(account_id=account_id, account_number=account_number)

        for t in all_transactions:
            if t['is_income']:
                income_sources[t['type_name']] += t['amount']

        total_income = sum(income_sources.values())
        diversity_index = 0.0
        if total_income > 0:
            # Herfindahl-Hirschman Index (HHI) for income concentration
            # Lower HHI means higher diversity
            hhi = sum((amount / total_income) ** 2 for amount in income_sources.values())
            diversity_index = 1 - hhi # Invert HHI for a diversity score (0 to 1, 1 being most diverse)

        # Passive income ratio (assuming '其他收入' or similar is passive)
        passive_income = income_sources.get('其他收入', 0.0) # Example: '其他收入' as passive
        passive_income_ratio = (passive_income / total_income) if total_income > 0 else 0.0

        sorted_sources = sorted(income_sources.items(), key=lambda item: item[1], reverse=True)

        return {
            'income_sources': sorted_sources,
            'total_income': total_income,
            'income_diversity_index': diversity_index,
            'passive_income_ratio': passive_income_ratio
        }

    def get_cash_flow_health(self, account_id=None, account_number=None, months=12):
        cash_flow_data = defaultdict(float)
        all_transactions = self._get_transactions_for_analysis(account_id=account_id, account_number=account_number)

        for t in all_transactions:
            month = datetime.strptime(t['date'], '%Y-%m-%d').strftime('%Y-%m')
            cash_flow_data[month] += t['amount']

        # Fill in missing months with 0 net flow
        sorted_months = sorted(cash_flow_data.keys())
        if not sorted_months:
            return {}

        start_date = datetime.strptime(sorted_months[0], '%Y-%m')
        end_date = datetime.strptime(sorted_months[-1], '%Y-%m')

        current_date = start_date
        full_cash_flow_history = []
        while current_date <= end_date:
            month_str = current_date.strftime('%Y-%m')
            full_cash_flow_history.append({'month': month_str, 'net_flow': cash_flow_data.get(month_str, 0.0)})
            # Move to next month
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)

        net_flows = [item['net_flow'] for item in full_cash_flow_history]

        # Emergency fund coverage (simplified: assuming target 3-6 months of average expense)
        # This requires average monthly expense, which can be derived from get_income_expense_balance
        # For now, let's assume a placeholder or calculate from current data
        total_expense_for_period = sum(t['amount'] for t in all_transactions if not t['is_income'])
        num_months_covered = len(set(datetime.strptime(t['date'], '%Y-%m-%d').strftime('%Y-%m') for t in all_transactions))
        avg_monthly_expense = abs(total_expense_for_period / num_months_covered) if num_months_covered > 0 else 0.0

        # This needs actual current cash balance, which is not directly available here.
        # For demonstration, let's use the last month's net flow as a proxy for 'available cash' for emergency fund calc.
        # In a real system, you'd query current account balances.
        current_cash_balance = net_flows[-1] if net_flows else 0.0 # Very simplified
        emergency_fund_months = (current_cash_balance / avg_monthly_expense) if avg_monthly_expense > 0 else float('inf')

        # Funding gap frequency (how often net flow is negative)
        funding_gap_months = sum(1 for flow in net_flows if flow < 0)
        funding_gap_frequency = (funding_gap_months / len(net_flows)) if net_flows else 0.0

        return {
            'monthly_cash_flow': full_cash_flow_history,
            'emergency_fund_months_coverage': emergency_fund_months,
            'funding_gap_frequency': funding_gap_frequency
        }

    def get_income_growth(self, account_id=None, account_number=None, periods=4, period_type='quarterly'):
        income_data = defaultdict(float)
        all_transactions = self._get_transactions_for_analysis(account_id=account_id, account_number=account_number)

        for t in all_transactions:
            if t['is_income']:
                trans_date = datetime.strptime(t['date'], '%Y-%m-%d')
                key = None
                if period_type == 'monthly':
                    key = trans_date.strftime('%Y-%m')
                elif period_type == 'quarterly':
                    quarter = (trans_date.month - 1) // 3 + 1
                    key = f"{trans_date.year}-Q{quarter}"
                elif period_type == 'yearly':
                    key = str(trans_date.year)
                else:
                    continue
                income_data[key] += t['amount']

        sorted_periods = sorted(income_data.keys())
        growth_rates = []

        for i in range(1, len(sorted_periods)):
            current_period_income = income_data[sorted_periods[i]]
            previous_period_income = income_data[sorted_periods[i-1]]

            if previous_period_income != 0:
                growth = (current_period_income - previous_period_income) / previous_period_income * 100
            else:
                growth = float('inf') if current_period_income > 0 else 0.0
            growth_rates.append({'period': sorted_periods[i], 'growth_rate': growth})

        # Salary trend (assuming '工资' is salary type)
        salary_trend = []
        salary_income_by_period = defaultdict(float)
        for t in all_transactions:
            if t['is_income'] and t['type_name'] == '工资':
                trans_date = datetime.strptime(t['date'], '%Y-%m-%d')
                key = None
                if period_type == 'monthly':
                    key = trans_date.strftime('%Y-%m')
                elif period_type == 'quarterly':
                    quarter = (trans_date.month - 1) // 3 + 1
                    key = f"{trans_date.year}-Q{quarter}"
                elif period_type == 'yearly':
                    key = str(trans_date.year)
                else:
                    continue
                salary_income_by_period[key] += t['amount']
        
        sorted_salary_periods = sorted(salary_income_by_period.keys())
        for i in range(len(sorted_salary_periods)):
            salary_trend.append({'period': sorted_salary_periods[i], 'salary': salary_income_by_period[sorted_salary_periods[i]]})

        return {
            'income_growth_rates': growth_rates,
            'salary_trend': salary_trend
        }

    def get_financial_resilience(self, account_id=None, account_number=None, months=12):
        all_transactions = self._get_transactions_for_analysis(account_id=account_id, account_number=account_number)

        # Recovery period after large expenses (simplified: find largest expense, then time to recover net balance)
        largest_expense_trans = None
        for t in all_transactions:
            if t['amount'] < 0 and (largest_expense_trans is None or t['amount'] < largest_expense_trans['amount']):
                largest_expense_trans = t
        
        recovery_period_days = None
        if largest_expense_trans:
            # This is complex to calculate accurately without a running balance. 
            # A simplified approach: find when cumulative net income after the expense covers the expense.
            # This would require re-querying or processing transactions chronologically after the expense.
            # For now, let's return a placeholder.
            recovery_period_days = "N/A (requires detailed balance tracking)"

        # Income interruption resistance (how many months can expenses be covered by savings/emergency fund)
        # This requires current savings/emergency fund amount and average monthly expenses.
        # Using placeholders as actual balances are not managed here.
        emergency_fund_months_coverage = self.get_cash_flow_health(account_id, account_number, months).get('emergency_fund_months_coverage', 0.0)

        # Break-even point (date when income covers expenses for the year/month)
        # This requires cumulative income/expense tracking within a period.
        break_even_point_data = defaultdict(lambda: {'income': 0.0, 'expense': 0.0, 'net': 0.0, 'break_even_date': None})
        
        # Sort transactions by date for cumulative calculation
        sorted_transactions = sorted(all_transactions, key=lambda x: datetime.strptime(x['date'], '%Y-%m-%d'))

        current_year = None
        cumulative_income = 0.0
        cumulative_expense = 0.0

        for t in sorted_transactions:
            trans_date = datetime.strptime(t['date'], '%Y-%m-%d')
            if current_year is None or trans_date.year != current_year:
                # Reset for new year
                if current_year is not None:
                    # Store previous year's data before resetting
                    pass # Logic for storing break_even_point_data[current_year] if needed
                current_year = trans_date.year
                cumulative_income = 0.0
                cumulative_expense = 0.0
                break_even_point_data[current_year] = {'income': 0.0, 'expense': 0.0, 'net': 0.0, 'break_even_date': None}

            if t['is_income']:
                cumulative_income += t['amount']
            else:
                cumulative_expense += t['amount']
            
            if break_even_point_data[current_year]['break_even_date'] is None and (cumulative_income + cumulative_expense) >= 0:
                break_even_point_data[current_year]['break_even_date'] = t['date']
            
            break_even_point_data[current_year]['income'] = cumulative_income
            break_even_point_data[current_year]['expense'] = cumulative_expense
            break_even_point_data[current_year]['net'] = cumulative_income + cumulative_expense

        return {
            'recovery_period_after_largest_expense_days': recovery_period_days,
            'income_interruption_resistance_months': emergency_fund_months_coverage, # Reusing this metric
            'break_even_point_by_year': {year: data for year, data in break_even_point_data.items()}
        }

if __name__ == '__main__':
    # Example usage for testing
    import os
    from scripts.db.repositories.bank_repository import BankRepository
    from scripts.db.repositories.account_repository import AccountRepository
    from scripts.db.repositories.transaction_type_repository import TransactionTypeRepository
    from scripts.db.repositories.transaction_repository import TransactionRepository

    test_db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'instance', 'test_financial_analyzer.db'))
    
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
        print(f"Removed existing test DB: {test_db_path}")

    db_conn = DBConnection(test_db_path)
    db_conn.init_db() # Ensure tables are created

    bank_repo = BankRepository(db_conn)
    account_repo = AccountRepository(db_conn)
    ttype_repo = TransactionTypeRepository(db_conn)
    transaction_repo = TransactionRepository(db_conn)
    financial_analyzer = FinancialAnalyzer(db_conn)

    # Setup test data
    bank_id = bank_repo.get_or_create_bank("Test Bank E")
    account_id = account_repo.get_or_create_account(bank_id, "622200000004", "Analyzer Account")
    income_type_id = ttype_repo.get_or_create_transaction_type("Salary", True)
    bonus_type_id = ttype_repo.get_or_create_transaction_type("Bonus", True)
    food_type_id = ttype_repo.get_or_create_transaction_type("Food", False)
    rent_type_id = ttype_repo.get_or_create_transaction_type("Rent", False)
    transport_type_id = ttype_repo.get_or_create_transaction_type("Transport", False)

    test_transactions = [
        {'account_id': account_id, 'date': '2023-01-01', 'type_id': income_type_id, 'amount': 5000.00, 'description': 'Jan Salary', 'is_income': True},
        {'account_id': account_id, 'date': '2023-01-05', 'type_id': food_type_id, 'amount': -300.00, 'description': 'Jan Food', 'is_income': False},
        {'account_id': account_id, 'date': '2023-01-20', 'type_id': rent_type_id, 'amount': -1500.00, 'description': 'Jan Rent', 'is_income': False},
        {'account_id': account_id, 'date': '2023-02-01', 'type_id': income_type_id, 'amount': 5200.00, 'description': 'Feb Salary', 'is_income': True},
        {'account_id': account_id, 'date': '2023-02-10', 'type_id': food_type_id, 'amount': -350.00, 'description': 'Feb Food', 'is_income': False},
        {'account_id': account_id, 'date': '2023-03-01', 'type_id': income_type_id, 'amount': 5100.00, 'description': 'Mar Salary', 'is_income': True},
        {'account_id': account_id, 'date': '2023-03-15', 'type_id': bonus_type_id, 'amount': 1000.00, 'description': 'Mar Bonus', 'is_income': True},
        {'account_id': account_id, 'date': '2023-03-20', 'type_id': transport_type_id, 'amount': -2000.00, 'description': 'Mar Travel', 'is_income': False}, # Large expense
        {'account_id': account_id, 'date': '2023-04-01', 'type_id': income_type_id, 'amount': 5300.00, 'description': 'Apr Salary', 'is_income': True},
        {'account_id': account_id, 'date': '2024-01-01', 'type_id': income_type_id, 'amount': 6000.00, 'description': 'Jan Salary 2024', 'is_income': True},
        {'account_id': account_id, 'date': '2024-01-10', 'type_id': food_type_id, 'amount': -400.00, 'description': 'Jan Food 2024', 'is_income': False},
    ]

    # The `is_income` field in test_transactions is for convenience in this test script.
    # In real usage, `is_income` comes from `transaction_types` table via `type_id`.
    # So, we need to ensure `type_id` is correctly mapped.
    processed_transactions = []
    for t in test_transactions:
        ttype = ttype_repo.get_transaction_type_by_id(t['type_id'])
        if ttype and ttype['is_income'] != t['is_income']:
            logger.warning(f"Mismatch in is_income for type_id {t['type_id']}: {ttype['name']}. Test data: {t['is_income']}, DB: {ttype['is_income']}")
        processed_transactions.append({
            'account_id': t['account_id'],
            'date': t['date'],
            'type_id': t['type_id'],
            'amount': t['amount'],
            'currency': 'CNY', # Default currency
            'description': t['description'],
            'counterparty': 'N/A', # Placeholder
            'notes': 'N/A', # Placeholder
            'original_description': t['description']
        })

    transaction_repo.import_transactions(processed_transactions)

    print("\n--- Balance Summary ---")
    summary = financial_analyzer.get_balance_summary(account_id=account_id)
    print(summary)

    print("\n--- General Statistics ---")
    stats = financial_analyzer.get_general_statistics()
    print(stats)

    print("\n--- Monthly Balance History ---")
    monthly_history = financial_analyzer.get_monthly_balance_history(account_id=account_id, months=6)
    print(monthly_history)

    print("\n--- Income/Expense Balance (Monthly) ---")
    income_expense_monthly = financial_analyzer.get_income_expense_balance(account_id=account_id, period_type='monthly')
    print(income_expense_monthly)

    print("\n--- Income Stability ---")
    income_stability = financial_analyzer.get_income_stability(account_id=account_id)
    print(income_stability)

    print("\n--- Income Diversity ---")
    income_diversity = financial_analyzer.get_income_diversity(account_id=account_id)
    print(income_diversity)

    print("\n--- Cash Flow Health ---")
    cash_flow_health = financial_analyzer.get_cash_flow_health(account_id=account_id)
    print(cash_flow_health)

    print("\n--- Income Growth ---")
    income_growth = financial_analyzer.get_income_growth(account_id=account_id, period_type='quarterly')
    print(income_growth)

    print("\n--- Financial Resilience ---")
    financial_resilience = financial_analyzer.get_financial_resilience(account_id=account_id)
    print(financial_resilience)

    db_conn.close_connection()