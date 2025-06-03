import sqlite3
import pandas as pd
import os
import logging
from pathlib import Path
from datetime import datetime
import json
import numpy as np
import traceback

# 导入错误处理机制
from scripts.common.exceptions import (
    DatabaseError, ConnectionError as DBConnectionError, 
    QueryError, ImportError
)
from scripts.common.error_handler import error_handler, safe_operation, log_error

# 导入配置管理器
from scripts.common.config import get_config_manager

# 配置日志
logger = logging.getLogger('db_manager')

class DBManager:
    """数据库管理类，负责SQLite数据库的创建、连接和交易数据管理"""
    
    def __init__(self, db_path=None):
        """初始化数据库管理器
        
        Args:
            db_path: 数据库文件路径，默认使用配置中的路径
        """
        # 获取配置管理器
        self.config_manager = get_config_manager()
        
        # 如果未指定数据库路径，从配置中获取
        if db_path is None:
            # 从配置中获取数据库类型和路径
            db_type = self.config_manager.get('database.type', 'sqlite')
            config_db_path = self.config_manager.get('database.path', 'data/transactions.db')
            
            # 确保路径是绝对路径
            if not os.path.isabs(config_db_path):
                # 定位项目根目录
                current_dir = os.path.dirname(os.path.abspath(__file__))
                scripts_dir = os.path.dirname(current_dir)
                root_dir = os.path.dirname(scripts_dir)
                
                # 结合根目录和配置路径
                db_path = os.path.join(root_dir, config_db_path)
            else:
                db_path = config_db_path
                
            # 确保目录存在
            db_dir = os.path.dirname(db_path)
            os.makedirs(db_dir, exist_ok=True)
        
        self.db_path = db_path
        self.logger = logger
        self.logger.info(f"数据库路径设置为: {self.db_path}")
        
        # 初始化数据库
        self.init_db()
    
    @error_handler(reraise=True, expected_exceptions=DBConnectionError)
    def get_connection(self):
        """获取数据库连接"""
        try:
            # 从配置中获取连接超时参数
            timeout = self.config_manager.get('database.timeout', 30.0)
            busy_timeout = self.config_manager.get('database.busy_timeout', 60000)  # 增加到60秒
            
            # 设置超时时间
            conn = sqlite3.connect(self.db_path, timeout=timeout)
            # 启用外键约束
            conn.execute("PRAGMA foreign_keys = ON")
            # 配置返回行为字典形式
            conn.row_factory = sqlite3.Row
            # 启用WAL模式，提高并发性能
            conn.execute("PRAGMA journal_mode = WAL")
            # 设置busy_timeout，避免数据库锁定
            conn.execute(f"PRAGMA busy_timeout = {busy_timeout}")
            # 设置锁定超时
            conn.execute("PRAGMA lock_timeout = 30000")
            return conn
        except sqlite3.Error as e:
            self.logger.error(f"获取数据库连接时出错: {str(e)}")
            raise DBConnectionError(f"无法连接到数据库: {str(e)}", details={"db_path": self.db_path})
    
    @safe_operation("数据库初始化")
    def init_db(self):
        """初始化数据库表结构"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            # 创建银行表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS banks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bank_code TEXT UNIQUE NOT NULL,
                bank_name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # 创建账户表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_number TEXT UNIQUE NOT NULL,
                bank_id INTEGER NOT NULL,
                account_name TEXT,
                account_type TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (bank_id) REFERENCES banks(id)
            )
            ''')
            
            # 创建交易类型表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS transaction_types (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type_name TEXT NOT NULL,
                type_code TEXT,
                category TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # 创建交易记录表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER NOT NULL,
                transaction_date DATE NOT NULL,
                row_index INTEGER,
                amount REAL NOT NULL,
                balance REAL,
                transaction_type_id INTEGER,
                counterparty TEXT,
                description TEXT,
                category TEXT,
                notes TEXT,
                import_batch TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (account_id) REFERENCES accounts(id),
                FOREIGN KEY (transaction_type_id) REFERENCES transaction_types(id)
            )
            ''')
            
            # 创建索引
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_trans_date ON transactions(transaction_date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_trans_account ON transactions(account_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_trans_type ON transactions(transaction_type_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_trans_amount ON transactions(amount)')
            
            # 添加常见交易类型 - 从配置中获取
            category_mapping = self.config_manager.get('analysis.category_mapping', {})
            common_transaction_types = []
            
            # 收入类型
            for income_type in category_mapping.get('income', ['收入', '工资', '退款', '红包', '利息']):
                common_transaction_types.append((income_type, income_type.upper(), '收入'))
            
            # 支出类型
            for expense_type in category_mapping.get('expense', ['支出', '购物', '餐饮', '交通', '房租', '医疗', '教育', '娱乐', '旅行']):
                common_transaction_types.append((expense_type, expense_type.upper(), '支出'))
            
            # 转账类型
            for transfer_type in category_mapping.get('transfer', ['转账', '信用卡还款']):
                common_transaction_types.append((transfer_type, transfer_type.upper(), '转账'))
            
            # 其他类型
            common_transaction_types.append(('投资', 'INVESTMENT', '投资'))
            common_transaction_types.append(('其他', 'OTHER', '其他'))
            
            for type_info in common_transaction_types:
                self.get_or_create_transaction_type(type_info[0], type_info[1], type_info[2])
            
            # 添加常见银行 - 从配置中获取
            supported_banks = self.config_manager.get('extractors.supported_banks', ['CMB', 'CCB'])
            banks_config = self.config_manager.get('extractors.banks', {})
            common_banks = []
            
            for bank_code in supported_banks:
                bank_info = banks_config.get(bank_code, {})
                bank_name = bank_info.get('bank_name', bank_code)
                common_banks.append((bank_code, bank_name))
            
            # 添加默认银行列表
            if not common_banks:
                common_banks = [
                    ('CCB', '建设银行'),
                    ('ICBC', '工商银行'),
                    ('ABC', '农业银行'),
                    ('BOC', '中国银行'),
                    ('COMM', '交通银行'),
                    ('CMBC', '民生银行'),
                    ('CITIC', '中信银行'),
                    ('SPDB', '浦发银行'),
                    ('CEB', '光大银行'),
                    ('PAB', '平安银行'),
                    ('PSBC', '邮储银行'),
                    ('CMB', '招商银行'),
                    ('CIB', '兴业银行'),
                    ('OTHER', '其他银行'),
                ]
            
            for bank_info in common_banks:
                self.get_or_create_bank(bank_info[0], bank_info[1])
            
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise DatabaseError(f"初始化数据库失败: {str(e)}")
        finally:
            conn.close()
    
    @error_handler(fallback_value=None, reraise=True)
    def get_or_create_bank(self, bank_code, bank_name):
        """获取或创建银行记录"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM banks WHERE bank_code = ?', (bank_code,))
            bank = cursor.fetchone()
            
            if bank:
                return bank[0]
            
            cursor.execute('INSERT INTO banks (bank_code, bank_name) VALUES (?, ?)', (bank_code, bank_name))
            conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            raise DatabaseError(f"创建银行记录失败: {str(e)}")
        finally:
            if conn:
                conn.close()
    
    @error_handler(fallback_value=None, reraise=True)
    def get_or_create_account(self, account_number, bank_id, account_name=None, conn=None, cursor=None):
        """获取或创建账户记录"""
        # 如果没有提供连接，创建新连接（保持向后兼容）
        should_close_conn = False
        if conn is None:
            conn = self.get_connection()
            cursor = conn.cursor()
            should_close_conn = True
        
        try:
            # 检查账户是否存在
            cursor.execute('SELECT id FROM accounts WHERE account_number = ?', (account_number,))
            account = cursor.fetchone()
            
            if account:
                # 如果账号存在但名称为空，且提供了名称，更新账号名称
                if account_name and account_name != 'unknown':
                    cursor.execute('UPDATE accounts SET account_name = ? WHERE id = ?', 
                                  (account_name, account[0]))
                    if should_close_conn:
                        conn.commit()
                return account[0]
            
            # 创建新账户
            cursor.execute('INSERT INTO accounts (account_number, bank_id, account_name) VALUES (?, ?, ?)', 
                          (account_number, bank_id, account_name))
            if should_close_conn:
                conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            if should_close_conn and conn:
                conn.rollback()
            raise DatabaseError(f"创建账户记录失败: {str(e)}")
        finally:
            if should_close_conn and conn:
                conn.close()
    
    @error_handler(fallback_value=None, reraise=True)
    def get_or_create_transaction_type(self, type_name, type_code=None, category=None, conn=None, cursor=None):
        """获取或创建交易类型记录"""
        # 如果没有提供连接，创建新连接（保持向后兼容）
        should_close_conn = False
        if conn is None:
            conn = self.get_connection()
            cursor = conn.cursor()
            should_close_conn = True
        
        try:
            cursor.execute('SELECT id FROM transaction_types WHERE type_name = ?', (type_name,))
            transaction_type = cursor.fetchone()
            
            if transaction_type:
                return transaction_type[0]
            
            # 创建新交易类型
            cursor.execute('INSERT INTO transaction_types (type_name, type_code, category) VALUES (?, ?, ?)', 
                          (type_name, type_code, category))
            if should_close_conn:
                conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            if should_close_conn and conn:
                conn.rollback()
            raise DatabaseError(f"创建交易类型失败: {str(e)}")
        finally:
            if should_close_conn and conn:
                conn.close()
    
    @safe_operation("数据导入")
    def import_transactions(self, df, bank_id, import_batch=None):
        """导入交易数据
        
        Args:
            df: 包含交易数据的DataFrame
            bank_id: 银行ID
            import_batch: 导入批次ID，用于跟踪和去重
            
        Returns:
            int: 导入的记录数量
        """
        if df is None or df.empty:
            self.logger.warning("没有数据可导入")
            return 0
            
        # 确保必须的列存在
        required_columns = ['transaction_date', 'amount']
        for col in required_columns:
            if col not in df.columns:
                raise ImportError(f"缺少必要的列: {col}", details={"missing_column": col})
                
        # 进行数据清理和预处理
        conn = None
        try:
            # 去重操作
            df = df.drop_duplicates()
            
            # 处理日期格式
            df['transaction_date'] = pd.to_datetime(df['transaction_date'], errors='coerce')
            df = df.dropna(subset=['transaction_date'])  # 删除日期无效的行
            df['transaction_date'] = df['transaction_date'].dt.strftime('%Y-%m-%d')
            
            # 确保amount列为数值型
            df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
            df = df.dropna(subset=['amount'])  # 删除金额无效的行
            
            # 确保account_number列存在
            if 'account_number' not in df.columns:
                raise ImportError("数据中缺少account_number列")
                
            # 如果没有指定导入批次，创建一个
            if import_batch is None:
                import_batch = f"import_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 开始事务
            conn.execute("BEGIN IMMEDIATE")
            
            # 记录插入计数
            inserted_count = 0
            
            # 获取每个账号的id，如果不存在则创建
            for account_number in df['account_number'].unique():
                # 获取account_name，如果存在
                account_name = None
                if 'account_name' in df.columns:
                    account_name_records = df[df['account_number'] == account_number]['account_name'].unique()
                    if len(account_name_records) > 0 and not pd.isna(account_name_records[0]):
                        account_name = account_name_records[0]
                
                # 获取或创建账户（使用现有连接）
                account_id = self.get_or_create_account(account_number, bank_id, account_name, conn, cursor)
                
                # 筛选此账户的交易
                account_df = df[df['account_number'] == account_number].copy()
                
                # 为每条交易获取交易类型ID
                for index, row in account_df.iterrows():
                    transaction_type = row.get('transaction_type')
                    transaction_type_id = None
                    
                    if transaction_type and not pd.isna(transaction_type):
                        # 获取或创建交易类型 - 传入当前连接和游标
                        transaction_type_id = self.get_or_create_transaction_type(transaction_type, conn=conn, cursor=cursor)
                    
                    # 准备插入数据
                    # 检查是否存在相同交易（账户ID、日期、金额、类型ID、对手方、导入批次都相同）
                    duplicate_check_query = '''
                    SELECT id FROM transactions 
                    WHERE account_id = ? AND transaction_date = ? AND amount = ?
                    '''
                    duplicate_params = [account_id, row['transaction_date'], row['amount']]
                    
                    # 如果有交易类型，添加到查询条件
                    if transaction_type_id:
                        duplicate_check_query += ' AND transaction_type_id = ?'
                        duplicate_params.append(transaction_type_id)
                    
                    # 如果有对手方，添加到查询条件
                    counterparty = row.get('counterparty')
                    if counterparty and not pd.isna(counterparty):
                        duplicate_check_query += ' AND counterparty = ?'
                        duplicate_params.append(counterparty)
                    
                    cursor.execute(duplicate_check_query, duplicate_params)
                    duplicate = cursor.fetchone()
                    
                    if duplicate:
                        self.logger.debug(f"跳过重复交易: {row['transaction_date']}, {row['amount']}")
                        continue
                    
                    # 准备交易数据
                    transaction_data = {
                        'account_id': account_id,
                        'transaction_date': row['transaction_date'],
                        'amount': row['amount'],
                        'transaction_type_id': transaction_type_id,
                        'import_batch': import_batch
                    }
                    
                    # 添加可选字段
                    for field in ['balance', 'counterparty', 'description', 'category', 'notes', 'row_index']:
                        if field in row and not pd.isna(row[field]):
                            transaction_data[field] = row[field]
                    
                    # 构建插入SQL
                    fields = ', '.join(transaction_data.keys())
                    placeholders = ', '.join(['?'] * len(transaction_data))
                    insert_sql = f'INSERT INTO transactions ({fields}) VALUES ({placeholders})'
                    
                    try:
                        cursor.execute(insert_sql, list(transaction_data.values()))
                        inserted_count += 1
                    except sqlite3.Error as e:
                        self.logger.error(f"插入交易记录时出错: {str(e)}, 数据: {transaction_data}")
                        # 继续处理其他记录
            
            # 提交事务
            conn.commit()
            self.logger.info(f"成功导入 {inserted_count} 条交易记录")
            return inserted_count
            
        except Exception as e:
            if conn:
                conn.rollback()  # 回滚事务
            raise ImportError(f"导入交易数据失败: {str(e)}")
        finally:
            if conn:
                conn.close()  # 确保连接被关闭
        
        return 0
    
    def get_transactions(self, account_number_filter=None, start_date=None, end_date=None,
                         min_amount=None, max_amount=None, transaction_type_filter=None,
                         counterparty_filter=None, currency_filter=None, account_name_filter=None,
                         limit=1000, offset=0, distinct=False):
        """按条件查询交易记录 (已重构以适应新的扁平化transactions表)

        Args:
            account_number_filter: 账号 (用于筛选)
            start_date: 开始日期
            end_date: 结束日期
            min_amount: 最小金额
            max_amount: 最大金额
            transaction_type_filter: 交易类型名称 (用于筛选 tt.type_name)
            counterparty_filter: 交易对方 (用于筛选 t.counterparty)
            currency_filter: 币种 (当前版本数据库表不支持此筛选)
            account_name_filter: 户名 (用于筛选 a.account_name)
            limit: 返回记录数限制
            offset: 分页偏移量
            distinct: 是否去除重复交易 (根据核心字段判断)

        Returns:
            交易记录字典列表
        """
        conn = self.get_connection()
        try:
            cursor = conn.cursor()

            conditions = []
            params = []

            # Base FROM and JOIN clauses
            from_join_clause = """
                FROM transactions t
                LEFT JOIN accounts a ON t.account_id = a.id
                LEFT JOIN banks b ON a.bank_id = b.id
                LEFT JOIN transaction_types tt ON t.transaction_type_id = tt.id
            """

            if account_number_filter:
                conditions.append("a.account_number LIKE ?")
                params.append(f"%{account_number_filter}%")
            if account_name_filter:
                conditions.append("a.account_name LIKE ?")
                params.append(f"%{account_name_filter}%")
            if start_date:
                conditions.append("t.transaction_date >= ?")
                params.append(start_date)
            if end_date:
                conditions.append("t.transaction_date <= ?")
                params.append(end_date)
            if min_amount is not None:
                conditions.append("t.amount >= ?")
                params.append(min_amount)
            if max_amount is not None:
                conditions.append("t.amount <= ?")
                params.append(max_amount)
            if transaction_type_filter:
                conditions.append("tt.type_name LIKE ?")
                params.append(f"%{transaction_type_filter}%")
            if counterparty_filter:
                conditions.append("t.counterparty LIKE ?") # Assumes t.counterparty is the correct direct column
                params.append(f"%{counterparty_filter}%")
            
            if currency_filter:
                self.logger.warning("Currency filter is not currently supported by the database schema for transactions and will be ignored.")
                # No condition is added for currency_filter

            where_clause = ""
            if conditions:
                where_clause = "WHERE " + " AND ".join(conditions)

            # Define fields to select, ensuring aliases are used where column names might clash or for clarity
            # Explicitly list needed fields instead of a generic "core_fields" string here for better control
            # Ensuring original 'transaction_type' key is populated by tt.type_name for compatibility
            # Ensuring original 'account_number' key is populated by a.account_number
            # Ensuring original 'account_name' key is populated by a.account_name (if it exists in select)
            # Adding b.bank_name as bank_name
            select_fields = """
                t.id, t.transaction_date, t.amount, t.balance, t.counterparty, t.description, t.category AS transaction_category, t.notes,
                a.account_number, a.account_name,
                b.bank_name,
                tt.type_name AS transaction_type
            """
            # Note: 'currency' is omitted from select_fields as its source is undefined.
            # 'row_index' and 'import_batch' from t can be added if needed.
            # 't.created_at' is typically added for distinct handling or general info.

            if distinct:
                # For distinct, we group by a set of fields that define a unique transaction for the user's perspective.
                # These fields must be from the joined tables.
                # The MIN(t.id) and MIN(t.created_at) are for consistent row selection within a group.
                # Ensure all fields in GROUP BY are also in SELECT (either directly or aggregated).
                # The 'transaction_category' alias for t.category is used here for clarity.
                # The 'transaction_type' alias for tt.type_name is used here.
                distinct_group_by_fields = "t.transaction_date, t.amount, t.balance, tt.type_name, t.counterparty, a.account_number, a.account_name, b.bank_name, t.description, t.category"
                
                query = f'''
                    SELECT
                        MIN(t.id) as id,
                        t.transaction_date, t.amount, t.balance, t.counterparty, t.description, t.category AS transaction_category, t.notes,
                        a.account_number, a.account_name,
                        b.bank_name,
                        tt.type_name AS transaction_type,
                        MIN(t.created_at) as created_at 
                    FROM transactions t
                    LEFT JOIN accounts a ON t.account_id = a.id
                    LEFT JOIN banks b ON a.bank_id = b.id
                    LEFT JOIN transaction_types tt ON t.transaction_type_id = tt.id
                    {where_clause}
                    GROUP BY {distinct_group_by_fields}
                    ORDER BY t.transaction_date DESC, MIN(t.id) DESC
                    LIMIT ? OFFSET ?
                '''
            else:
                query = f'''
                    SELECT
                        {select_fields},
                        t.created_at
                    {from_join_clause}
                    {where_clause}
                    ORDER BY t.transaction_date DESC, t.id DESC
                    LIMIT ? OFFSET ?
                '''
            
            params.extend([limit, offset])

            self.logger.info(f"Executing transaction query: limit={limit}, offset={offset}, distinct={distinct}")
            self.logger.info(f"SQL: {query}") # Be cautious logging potentially large queries if they become very complex
            self.logger.info(f"Params: {params}")

            cursor.execute(query, params)
            results = [dict(row) for row in cursor.fetchall()]

            self.logger.info(f"Found {len(results)} transaction records")
            if results and len(results) > 0 : # Check if results is not empty before trying to access an element
                 self.logger.info(f"First record example: {results[0]}") # Log first record if exists
            
            return results

        except Exception as e:
            self.logger.error(f"Error querying transactions: {str(e)}")
            self.logger.error(f"Detailed error: {traceback.format_exc()}") # Log full traceback
            return []
        finally:
            conn.close()
    
    def get_accounts(self):
        """获取所有账户信息"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            query = '''
                SELECT a.id, a.account_number, a.account_name, a.account_type, 
                       b.bank_name, b.bank_code
                FROM accounts a
                JOIN banks b ON a.bank_id = b.id
                ORDER BY b.bank_name, a.account_number
            '''
            
            cursor.execute(query)
            
            # 返回结果
            results = []
            for row in cursor.fetchall():
                results.append(dict(row))
            
            return results
            
        except Exception as e:
            self.logger.error(f"获取账户信息时出错: {str(e)}")
            return []
        finally:
            conn.close()
    
    def get_balance_summary(self):
        """获取所有账户的余额汇总"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            # 使用Common Table Expression (CTE) 获取每个账户的最新余额
            # 按交易日期和row_index排序以确保正确的余额顺序
            query = '''
            WITH latest_transactions AS (
                SELECT 
                    t.account_id,
                    t.balance,
                    t.transaction_date,
                    ROW_NUMBER() OVER (PARTITION BY t.account_id ORDER BY t.transaction_date DESC, t.id DESC) as row_num
                FROM transactions t
                WHERE t.balance IS NOT NULL
            )
            SELECT 
                a.id as account_id,
                a.account_number,
                a.account_name,
                b.bank_name,
                lt.balance as latest_balance,
                lt.transaction_date as balance_date
            FROM 
                accounts a
            JOIN 
                banks b ON a.bank_id = b.id
            LEFT JOIN 
                latest_transactions lt ON a.id = lt.account_id AND lt.row_num = 1
            ORDER BY 
                b.bank_name, a.account_number
            '''
            
            cursor.execute(query)
            results = cursor.fetchall()
            
            # 转换为适合前端使用的格式
            balance_summary = []
            for row in results:
                balance_summary.append({
                    'account_id': row['account_id'],
                    'account_number': row['account_number'],
                    'account_name': row['account_name'] or '未命名账户',
                    'bank_name': row['bank_name'],
                    'latest_balance': row['latest_balance'] if row['latest_balance'] is not None else 0,
                    'balance_date': row['balance_date']
                })
            
            # 调试日志 - 输出找到的余额信息
            self.logger.info(f"找到 {len(balance_summary)} 个账户的余额信息")
            for account in balance_summary:
                self.logger.info(f"账户 {account['account_number']} ({account['bank_name']}): 余额 = {account['latest_balance']}")
            
            return balance_summary
        except Exception as e:
            self.logger.error(f"获取余额汇总时出错: {str(e)}")
            self.logger.error(f"详细错误: {e}")
            return []
        finally:
            conn.close()
    
    def export_to_csv(self, query_params=None, output_path=None):
        """将交易数据导出为CSV文件
        
        Args:
            query_params: 查询参数字典
            output_path: 输出文件路径
            
        Returns:
            导出的文件路径
        """
        if query_params is None:
            query_params = {}
            
        if output_path is None:
            # 默认输出到数据目录
            data_dir = os.path.dirname(self.db_path)
            output_path = os.path.join(data_dir, f"export_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv")
        
        # 获取交易数据
        transactions = self.get_transactions(**query_params)
        
        if not transactions:
            self.logger.warning("没有数据可导出")
            return None
        
        try:
            # 转换为DataFrame
            df = pd.DataFrame(transactions)
            
            # 导出到CSV
            df.to_csv(output_path, index=False, encoding='utf-8-sig')
            
            self.logger.info(f"成功导出 {len(df)} 条交易记录到: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"导出CSV时出错: {str(e)}")
            return None
    
    def get_statistics(self):
        """获取交易数据统计信息"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            # 总统计数据
            stats = {}
            
            # 交易总数 - 使用DISTINCT消除重复
            cursor.execute("""
                SELECT COUNT(DISTINCT transaction_date || '_' || amount || '_' || IFNULL(counterparty, '')) as count 
                FROM transactions
            """)
            stats['total_transactions'] = cursor.fetchone()['count']
            
            # 账户总数
            cursor.execute("SELECT COUNT(*) as count FROM accounts")
            stats['total_accounts'] = cursor.fetchone()['count']
            
            # 收入和支出总额 - 使用子查询和DISTINCT消除重复
            cursor.execute("""
                WITH distinct_transactions AS (
                    SELECT DISTINCT transaction_date, amount, IFNULL(counterparty, '') as counterparty
                    FROM transactions
                )
                SELECT 
                    SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) as total_income,
                    SUM(CASE WHEN amount < 0 THEN amount ELSE 0 END) as total_expense,
                    SUM(amount) as net_amount,
                    COUNT(CASE WHEN amount > 0 THEN 1 END) as income_count,
                    COUNT(CASE WHEN amount < 0 THEN 1 END) as expense_count
                FROM distinct_transactions
            """)
            result = cursor.fetchone()
            stats['total_income'] = result['total_income'] or 0
            stats['total_expense'] = result['total_expense'] or 0
            stats['net_amount'] = result['net_amount'] or 0
            stats['income_count'] = result['income_count'] or 0
            stats['expense_count'] = result['expense_count'] or 0
            
            # 交易日期范围
            cursor.execute("""
                SELECT 
                    MIN(transaction_date) as min_date,
                    MAX(transaction_date) as max_date
                FROM transactions
            """)
            result = cursor.fetchone()
            stats['min_date'] = result['min_date']
            stats['max_date'] = result['max_date']
            
            # 按银行统计 - 使用子查询和DISTINCT消除重复
            cursor.execute("""
                WITH distinct_transactions AS (
                    SELECT DISTINCT t.transaction_date, t.amount, IFNULL(t.counterparty, '') as counterparty, t.account_id
                    FROM transactions t
                )
                SELECT 
                    b.bank_name,
                    COUNT(dt.transaction_date) as transaction_count,
                    SUM(CASE WHEN dt.amount > 0 THEN dt.amount ELSE 0 END) as income,
                    SUM(CASE WHEN dt.amount < 0 THEN dt.amount ELSE 0 END) as expense
                FROM distinct_transactions dt
                JOIN accounts a ON dt.account_id = a.id
                JOIN banks b ON a.bank_id = b.id
                GROUP BY b.bank_name
                ORDER BY transaction_count DESC
            """)
            stats['bank_stats'] = [dict(row) for row in cursor.fetchall()]
            
            # 按账户统计 - 使用子查询和DISTINCT消除重复
            cursor.execute("""
                WITH distinct_transactions AS (
                    SELECT DISTINCT t.transaction_date, t.amount, IFNULL(t.counterparty, '') as counterparty, t.account_id
                    FROM transactions t
                )
                SELECT 
                    a.account_number,
                    b.bank_name,
                    COUNT(dt.transaction_date) as transaction_count,
                    SUM(CASE WHEN dt.amount > 0 THEN dt.amount ELSE 0 END) as income,
                    SUM(CASE WHEN dt.amount < 0 THEN dt.amount ELSE 0 END) as expense,
                    (
                        SELECT balance
                        FROM transactions
                        WHERE account_id = a.id AND balance IS NOT NULL
                        ORDER BY transaction_date DESC, row_index DESC
                        LIMIT 1
                    ) as latest_balance
                FROM accounts a
                JOIN banks b ON a.bank_id = b.id
                LEFT JOIN distinct_transactions dt ON a.id = dt.account_id
                GROUP BY a.account_number, b.bank_name
                ORDER BY transaction_count DESC
            """)
            stats['account_stats'] = [dict(row) for row in cursor.fetchall()]
            
            return stats
            
        except Exception as e:
            self.logger.error(f"获取统计信息时出错: {str(e)}")
            return {}
        finally:
            conn.close()
            
    def get_balance_range(self):
        """获取历史余额的最高值和最低值
        
        Returns:
            字典，包含最高余额和最低余额
        """
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            # 查询所有有余额记录的交易
            query = """
            SELECT 
                MAX(balance) as max_balance,
                MIN(balance) as min_balance
            FROM transactions
            WHERE balance IS NOT NULL
            """
            
            cursor.execute(query)
            result = cursor.fetchone()
            
            # 提取结果
            max_balance = result['max_balance'] if result and result['max_balance'] is not None else 0
            min_balance = result['min_balance'] if result and result['min_balance'] is not None else 0
            
            self.logger.info(f"余额范围: 最高 = {max_balance}, 最低 = {min_balance}")
            
            return {
                'max_balance': float(max_balance),
                'min_balance': float(min_balance)
            }
            
        except Exception as e:
            self.logger.error(f"获取余额范围时出错: {str(e)}")
            self.logger.error(f"详细错误: {e}")
            return {'max_balance': 0, 'min_balance': 0}
        finally:
            conn.close()

    def get_monthly_balance_history(self, months=12):
        """获取最近几个月的余额历史数据
        
        Args:
            months: 获取多少个月的数据，默认12个月
            
        Returns:
            列表，包含每个月的日期和余额
        """
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            # 获取当前日期
            from datetime import datetime, timedelta
            
            # 计算过去N个月的数据
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30 * months)
            
            # 简化查询逻辑，直接获取每个月最后一笔交易的余额
            query = """
            WITH monthly_data AS (
                SELECT 
                    strftime('%Y-%m', transaction_date) as month,
                    MAX(transaction_date) as last_date
                FROM transactions
                WHERE balance IS NOT NULL
                GROUP BY strftime('%Y-%m', transaction_date)
            )
            SELECT 
                md.month,
                (SELECT t.balance 
                 FROM transactions t 
                 WHERE strftime('%Y-%m-%d', t.transaction_date) = md.last_date
                 ORDER BY t.row_index DESC, t.id DESC
                 LIMIT 1) as balance
            FROM monthly_data md
            ORDER BY md.month
            """
            
            cursor.execute(query)
            results = cursor.fetchall()
            
            # 格式化结果
            balance_history = []
            for row in results:
                balance_history.append({
                    'month': row['month'],
                    'balance': float(row['balance']) if row['balance'] is not None else 0
                })
            
            self.logger.info(f"获取了 {len(balance_history)} 个月的余额历史数据")
            
            # 如果数据少于请求的月数，填充缺失的月份
            if len(balance_history) < months:
                existing_months = {item['month'] for item in balance_history}
                
                # 生成过去months个月的月份列表
                all_months = []
                temp_date = end_date
                for i in range(months):
                    month_str = temp_date.strftime('%Y-%m')
                    all_months.append(month_str)
                    # 上一个月
                    temp_date = temp_date.replace(day=1) - timedelta(days=1)
                
                # 添加缺失的月份，使用前一个月的余额或0
                all_months.reverse()  # 从早到晚排序
                complete_history = []
                prev_balance = 0
                
                for month in all_months:
                    found = False
                    for item in balance_history:
                        if item['month'] == month:
                            complete_history.append(item)
                            prev_balance = item['balance']
                            found = True
                            break
                    
                    if not found:
                        complete_history.append({
                            'month': month,
                            'balance': prev_balance
                        })
                
                balance_history = complete_history
            
            return balance_history
            
        except Exception as e:
            self.logger.error(f"获取月度余额历史时出错: {str(e)}")
            self.logger.error(f"详细错误: {e}")
            return []
        finally:
            conn.close()

    def get_transactions_count(self, account_number_filter=None, start_date=None, end_date=None,
                               min_amount=None, max_amount=None, transaction_type_filter=None,
                               counterparty_filter=None, currency_filter=None, account_name_filter=None,
                               distinct=False):
        """获取符合条件的交易记录总数 (已重构)

        Args:
            account_number_filter: 账号
            start_date: 开始日期
            end_date: 结束日期
            min_amount: 最小金额
            max_amount: 最大金额
            transaction_type_filter: 交易类型名称
            counterparty_filter: 交易对方
            currency_filter: 币种 (当前版本数据库表不支持此筛选)
            account_name_filter: 户名
            distinct: 是否去除重复交易

        Returns:
            符合条件的交易记录总数
        """
        conn = self.get_connection()
        try:
            cursor = conn.cursor()

            conditions = []
            params = []
            
            # Determine if joins are needed based on filters or distinct requirements
            joins_needed = False
            from_join_clause_parts = ["FROM transactions t"]

            if account_number_filter:
                conditions.append("a.account_number LIKE ?")
                params.append(f"%{account_number_filter}%")
                joins_needed = True # Account join needed
            if account_name_filter:
                conditions.append("a.account_name LIKE ?")
                params.append(f"%{account_name_filter}%")
                joins_needed = True # Account join needed
            if start_date:
                conditions.append("t.transaction_date >= ?")
                params.append(start_date)
            if end_date:
                conditions.append("t.transaction_date <= ?")
                params.append(end_date)
            if min_amount is not None:
                conditions.append("t.amount >= ?")
                params.append(min_amount)
            if max_amount is not None:
                conditions.append("t.amount <= ?")
                params.append(max_amount)
            if transaction_type_filter:
                conditions.append("tt.type_name LIKE ?")
                params.append(f"%{transaction_type_filter}%")
                joins_needed = True # Transaction type join needed
            if counterparty_filter: # Assumes t.counterparty is a direct column in transactions table
                conditions.append("t.counterparty LIKE ?")
                params.append(f"%{counterparty_filter}%")
            
            if currency_filter:
                self.logger.warning("Currency filter is not currently supported for transaction counts and will be ignored.")
                # No condition for currency_filter

            # Construct JOIN clauses if needed for filters or for distinct operation if it relies on joined fields
            # For distinct count, we must always join if distinct_columns refer to joined table fields.
            # The distinct_columns list below has been updated to reflect joined table fields.
            if distinct or joins_needed:
                # Base joins, always include them if any join is needed or for distinct count
                from_join_clause_parts.append("LEFT JOIN accounts a ON t.account_id = a.id")
                from_join_clause_parts.append("LEFT JOIN banks b ON a.bank_id = b.id") # bank_name might be part of distinct_columns
                from_join_clause_parts.append("LEFT JOIN transaction_types tt ON t.transaction_type_id = tt.id")
            
            from_join_clause = "\n                ".join(from_join_clause_parts)

            where_clause = ""
            if conditions:
                where_clause = "WHERE " + " AND ".join(conditions)

            if distinct:
                # These columns define a unique transaction from the user's perspective and come from joined tables.
                distinct_columns = "t.transaction_date, t.amount, t.balance, tt.type_name, t.counterparty, a.account_number, a.account_name, b.bank_name, t.description, t.category"
                query = f'''
                    SELECT COUNT(*) as total_count
                    FROM (
                        SELECT DISTINCT {distinct_columns}
                        {from_join_clause}
                        {where_clause}
                    )
                '''
            else:
                query = f'''
                    SELECT COUNT(*) as total_count
                    {from_join_clause}
                    {where_clause}
                '''

            self.logger.info(f"Executing transaction count query: distinct={distinct}")
            self.logger.info(f"SQL: {query}")
            self.logger.info(f"Params: {params}")

            cursor.execute(query, params)
            result = cursor.fetchone()
            total_count = result['total_count'] if result else 0

            self.logger.info(f"Total matching transaction records: {total_count}")
            return total_count

        except Exception as e:
            self.logger.error(f"Error querying transaction count: {str(e)}")
            self.logger.error(f"Detailed error: {traceback.format_exc()}") # Log full traceback
            return 0
        finally:
            conn.close()

    def get_distinct_values(self, table_name: str, column_name: str) -> list:
        """获取指定表和列的唯一非空值列表，按值排序。"""
        conn = self.get_connection()
        # 对表名和列名进行基本验证，防止SQL注入，尽管这里是内部使用
        # 更安全的方式是使用白名单验证 table_name 和 column_name
        safe_table_name = ''.join(c for c in table_name if c.isalnum() or c == '_')
        safe_column_name = ''.join(c for c in column_name if c.isalnum() or c == '_')
        if not safe_table_name or not safe_column_name or safe_table_name != table_name or safe_column_name != column_name:
            self.logger.error(f"get_distinct_values: 无效的表名或列名: {table_name}, {column_name}")
            return []
        try:
            cursor = conn.cursor()
            # 使用 f-string 插入经过"清洁"的表名和列名
            query = f"SELECT DISTINCT \"{safe_column_name}\" FROM \"{safe_table_name}\" WHERE \"{safe_column_name}\" IS NOT NULL ORDER BY \"{safe_column_name}\" ASC"
            self.logger.debug(f"Executing query for distinct values: {query}")
            cursor.execute(query)
            rows = cursor.fetchall()
            return [row[0] for row in rows]
        except sqlite3.Error as e: # 更具体地捕获SQLite错误
            self.logger.error(f"获取 {safe_table_name}.{safe_column_name} 的唯一值时发生SQLite错误: {e} (Query: {query})")
            return []
        except Exception as e:
            self.logger.error(f"获取 {safe_table_name}.{safe_column_name} 的唯一值时发生未知错误: {e}")
            return []
        finally:
            if conn:
                conn.close()

    @error_handler(fallback_value={})
    def get_income_expense_balance(self):
        """获取收入与支出平衡分析数据
        
        返回：
        - 月度/季度/年度收支差额比率
        - 收入覆盖必要支出的能力（必要支出覆盖率）
        - 储蓄率（每月收入中的储蓄比例）
        """
        self.logger.info("分析收入与支出平衡数据")
        
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            # 获取月度收支数据
            monthly_query = """
            SELECT 
                strftime('%Y-%m', transaction_date) as month,
                SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) as income,
                SUM(CASE WHEN amount < 0 THEN ABS(amount) ELSE 0 END) as expense
            FROM transactions t
            JOIN accounts a ON t.account_id = a.id
            GROUP BY month
            ORDER BY month
            """
            cursor.execute(monthly_query)
            monthly_data = []
            for row in cursor.fetchall():
                month = row['month']
                income = float(row['income']) if row['income'] else 0
                expense = float(row['expense']) if row['expense'] else 0
                
                # 计算收支比率
                if expense > 0:
                    ratio = income / expense
                else:
                    ratio = 1.0 if income > 0 else 0.0
                
                # 计算储蓄率
                if income > 0:
                    saving_rate = (income - expense) / income
                else:
                    saving_rate = 0.0
                
                monthly_data.append({
                    'month': month,
                    'income': income,
                    'expense': expense,
                    'ratio': ratio,
                    'saving_rate': saving_rate
                })
            
            # 获取季度收支数据
            quarterly_query = """
            SELECT 
                strftime('%Y', transaction_date) || '-Q' || ((CAST(strftime('%m', transaction_date) AS INTEGER) + 2) / 3) as quarter,
                SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) as income,
                SUM(CASE WHEN amount < 0 THEN ABS(amount) ELSE 0 END) as expense
            FROM transactions t
            JOIN accounts a ON t.account_id = a.id
            GROUP BY quarter
            ORDER BY quarter
            """
            cursor.execute(quarterly_query)
            quarterly_data = []
            for row in cursor.fetchall():
                quarter = row['quarter']
                income = float(row['income']) if row['income'] else 0
                expense = float(row['expense']) if row['expense'] else 0
                
                # 计算收支比率
                if expense > 0:
                    ratio = income / expense
                else:
                    ratio = 1.0 if income > 0 else 0.0
                
                # 计算储蓄率
                if income > 0:
                    saving_rate = (income - expense) / income
                else:
                    saving_rate = 0.0
                
                quarterly_data.append({
                    'quarter': quarter,
                    'income': income,
                    'expense': expense,
                    'ratio': ratio,
                    'saving_rate': saving_rate
                })
            
            # 获取年度收支数据
            yearly_query = """
            SELECT 
                strftime('%Y', transaction_date) as year,
                SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) as income,
                SUM(CASE WHEN amount < 0 THEN ABS(amount) ELSE 0 END) as expense
            FROM transactions t
            JOIN accounts a ON t.account_id = a.id
            GROUP BY year
            ORDER BY year
            """
            cursor.execute(yearly_query)
            yearly_data = []
            for row in cursor.fetchall():
                year = row['year']
                income = float(row['income']) if row['income'] else 0
                expense = float(row['expense']) if row['expense'] else 0
                
                # 计算收支比率
                if expense > 0:
                    ratio = income / expense
                else:
                    ratio = 1.0 if income > 0 else 0.0
                
                # 计算储蓄率
                if income > 0:
                    saving_rate = (income - expense) / income
                else:
                    saving_rate = 0.0
                
                yearly_data.append({
                    'year': year,
                    'income': income,
                    'expense': expense,
                    'ratio': ratio,
                    'saving_rate': saving_rate
                })
            
            # 计算必要支出覆盖率（假设餐饮、交通、住房、医疗、通讯为必要支出）
            necessary_expense_query = """
            SELECT 
                strftime('%Y-%m', transaction_date) as month,
                SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) as income,
                SUM(CASE WHEN amount < 0 AND (
                    category IN ('餐饮', '交通', '住房', '医疗', '通讯')
                    ) THEN ABS(amount) ELSE 0 END) as necessary_expense
            FROM transactions t
            JOIN accounts a ON t.account_id = a.id
            GROUP BY month
            ORDER BY month
            """
            cursor.execute(necessary_expense_query)
            necessary_expense_coverage = []
            for row in cursor.fetchall():
                month = row['month']
                income = float(row['income']) if row['income'] else 0
                necessary_expense = float(row['necessary_expense']) if row['necessary_expense'] else 0
                
                # 计算必要支出覆盖率
                if necessary_expense > 0:
                    coverage_ratio = income / necessary_expense
                else:
                    coverage_ratio = 1.0 if income > 0 else 0.0
                
                necessary_expense_coverage.append({
                    'month': month,
                    'income': income,
                    'necessary_expense': necessary_expense,
                    'coverage_ratio': coverage_ratio
                })
            
            # 计算总体指标
            overall_stats = {}
            
            # 计算平均储蓄率
            if monthly_data:
                overall_stats['avg_monthly_saving_rate'] = sum(m['saving_rate'] for m in monthly_data) / len(monthly_data)
            else:
                overall_stats['avg_monthly_saving_rate'] = 0.0
            
            # 计算平均收支比率
            if monthly_data:
                overall_stats['avg_monthly_ratio'] = sum(m['ratio'] for m in monthly_data) / len(monthly_data)
            else:
                overall_stats['avg_monthly_ratio'] = 0.0
            
            # 计算平均必要支出覆盖率
            if necessary_expense_coverage:
                overall_stats['avg_necessary_expense_coverage'] = sum(n['coverage_ratio'] for n in necessary_expense_coverage) / len(necessary_expense_coverage)
            else:
                overall_stats['avg_necessary_expense_coverage'] = 0.0
            
            return {
                'monthly_data': monthly_data,
                'quarterly_data': quarterly_data,
                'yearly_data': yearly_data,
                'necessary_expense_coverage': necessary_expense_coverage,
                'overall_stats': overall_stats
            }
        except Exception as e:
            self.logger.error(f"获取收入与支出平衡分析数据时出错: {e}")
            raise
        finally:
            conn.close()

    @error_handler(fallback_value={})
    def get_income_stability(self):
        """获取收入稳定性分析数据
        
        返回：
        - 固定收入占比（如工资占总收入比例）
        - 收入波动系数（标准差/平均值）
        - 最长无收入周期识别
        """
        self.logger.info("分析收入稳定性数据")
        
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            # 获取月度收入数据
            monthly_income_query = """
            SELECT 
                strftime('%Y-%m', transaction_date) as month,
                SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) as income
            FROM transactions t
            JOIN accounts a ON t.account_id = a.id
            GROUP BY month
            ORDER BY month
            """
            cursor.execute(monthly_income_query)
            monthly_income = []
            for row in cursor.fetchall():
                month = row['month']
                income = float(row['income']) if row['income'] else 0
                
                monthly_income.append({
                    'month': month,
                    'income': income
                })
            
            # 计算收入波动系数
            if monthly_income:
                income_values = [m['income'] for m in monthly_income]
                mean_income = sum(income_values) / len(income_values)
                variance = sum((x - mean_income) ** 2 for x in income_values) / len(income_values)
                std_dev = variance ** 0.5
                if mean_income > 0:
                    coefficient_of_variation = std_dev / mean_income
                else:
                    coefficient_of_variation = 0.0
            else:
                mean_income = 0.0
                std_dev = 0.0
                coefficient_of_variation = 0.0
            
            # 获取工资类收入占比
            income_types_query = """
            SELECT 
                SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) as total_income,
                SUM(CASE WHEN amount > 0 AND (
                    description LIKE '%工资%' OR 
                    description LIKE '%薪%' OR
                    category = '工资'
                ) THEN amount ELSE 0 END) as salary_income
            FROM transactions t
            JOIN accounts a ON t.account_id = a.id
            """
            cursor.execute(income_types_query)
            row = cursor.fetchone()
            
            total_income = float(row['total_income']) if row['total_income'] else 0
            salary_income = float(row['salary_income']) if row['salary_income'] else 0
            
            if total_income > 0:
                salary_income_ratio = salary_income / total_income
            else:
                salary_income_ratio = 0.0
            
            # 分析收入间隔和最长无收入周期
            no_income_periods = []
            max_no_income_days = 0
            max_no_income_period = {'start': None, 'end': None, 'days': 0}
            
            if len(monthly_income) > 1:
                # 计算每月是否有收入
                has_income = {}
                for m in monthly_income:
                    has_income[m['month']] = m['income'] > 0
                
                # 获取所有月份（包括没有交易的月份）
                all_months_query = """
                WITH RECURSIVE months(date) AS (
                    SELECT date(MIN(transaction_date), 'start of month')
                    FROM transactions
                    UNION ALL
                    SELECT date(date, '+1 month')
                    FROM months
                    WHERE date < date((SELECT MAX(transaction_date) FROM transactions), 'start of month')
                )
                SELECT strftime('%Y-%m', date) as month FROM months
                """
                cursor.execute(all_months_query)
                all_months = [row['month'] for row in cursor.fetchall()]
                
                current_period = None
                for month in all_months:
                    if month in has_income and has_income[month]:
                        if current_period:
                            # 结束一个无收入周期
                            days = (datetime.strptime(month, '%Y-%m') - 
                                   datetime.strptime(current_period['start'], '%Y-%m')).days
                            current_period['end'] = month
                            current_period['days'] = days
                            no_income_periods.append(current_period)
                            
                            if days > max_no_income_days:
                                max_no_income_days = days
                                max_no_income_period = current_period.copy()
                            
                            current_period = None
                    elif month not in has_income or not has_income[month]:
                        if not current_period:
                            # 开始一个新的无收入周期
                            current_period = {'start': month, 'end': None, 'days': 0}
            
            return {
                'monthly_income': monthly_income,
                'income_stats': {
                    'mean_income': mean_income,
                    'std_dev': std_dev,
                    'coefficient_of_variation': coefficient_of_variation
                },
                'salary_income_ratio': salary_income_ratio,
                'no_income_periods': no_income_periods,
                'max_no_income_period': max_no_income_period
            }
        except Exception as e:
            self.logger.error(f"获取收入稳定性分析数据时出错: {e}")
            raise
        finally:
            conn.close()

    @error_handler(fallback_value={})
    def get_income_diversity(self):
        """获取收入多样性评估数据
        
        返回：
        - 收入来源数量及分布
        - 主要收入来源集中度（最大收入来源占比）
        - 被动收入占比（利息、投资收益等）
        """
        self.logger.info("分析收入多样性数据")
        
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            # 获取收入来源分布
            income_sources_query = """
            SELECT 
                CASE 
                    WHEN description LIKE '%工资%' OR description LIKE '%薪%' THEN '工资收入'
                    WHEN description LIKE '%利息%' OR description LIKE '%股息%' THEN '利息收入'
                    WHEN description LIKE '%退款%' OR description LIKE '%返还%' THEN '退款'
                    WHEN description LIKE '%投资%' OR description LIKE '%基金%' OR description LIKE '%股票%' THEN '投资收益'
                    WHEN category = '工资' THEN '工资收入'
                    WHEN category = '利息' THEN '利息收入'
                    WHEN category = '退款' THEN '退款'
                    WHEN category = '投资' THEN '投资收益'
                    WHEN counterparty IS NOT NULL AND counterparty != '' THEN counterparty
                    ELSE '其他收入'
                END as income_source,
                SUM(amount) as total_amount,
                COUNT(*) as transaction_count
            FROM transactions
            WHERE amount > 0
            GROUP BY income_source
            ORDER BY total_amount DESC
            """
            cursor.execute(income_sources_query)
            income_sources = []
            total_income = 0
            for row in cursor.fetchall():
                source = row['income_source']
                amount = float(row['total_amount']) if row['total_amount'] else 0
                count = int(row['transaction_count'])
                
                total_income += amount
                
                income_sources.append({
                    'source': source,
                    'amount': amount,
                    'count': count
                })
            
            # 计算各收入来源占比
            for source in income_sources:
                if total_income > 0:
                    source['percentage'] = source['amount'] / total_income * 100
                else:
                    source['percentage'] = 0.0
            
            # 计算收入来源集中度
            concentration = 0
            if income_sources and total_income > 0:
                # 计算最大收入来源占比
                max_source_percentage = max(source['percentage'] for source in income_sources)
                concentration = max_source_percentage / 100  # 转换为0-1的比例
            
            # 计算被动收入占比（利息、投资收益等）
            passive_income_query = """
            SELECT 
                SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) as total_income,
                SUM(CASE WHEN amount > 0 AND (
                    description LIKE '%利息%' OR 
                    description LIKE '%股息%' OR
                    description LIKE '%投资%' OR
                    description LIKE '%基金%' OR
                    description LIKE '%股票%' OR
                    category IN ('利息', '投资')
                ) THEN amount ELSE 0 END) as passive_income
            FROM transactions
            """
            cursor.execute(passive_income_query)
            row = cursor.fetchone()
            
            total_income_all = float(row['total_income']) if row['total_income'] else 0
            passive_income = float(row['passive_income']) if row['passive_income'] else 0
            
            if total_income_all > 0:
                passive_income_ratio = passive_income / total_income_all
            else:
                passive_income_ratio = 0.0
            
            # 计算月度收入来源数量
            monthly_sources_query = """
            SELECT 
                strftime('%Y-%m', transaction_date) as month,
                COUNT(DISTINCT CASE 
                    WHEN description LIKE '%工资%' OR description LIKE '%薪%' THEN '工资收入'
                    WHEN description LIKE '%利息%' OR description LIKE '%股息%' THEN '利息收入'
                    WHEN description LIKE '%退款%' OR description LIKE '%返还%' THEN '退款'
                    WHEN description LIKE '%投资%' OR description LIKE '%基金%' OR description LIKE '%股票%' THEN '投资收益'
                    WHEN category = '工资' THEN '工资收入'
                    WHEN category = '利息' THEN '利息收入'
                    WHEN category = '退款' THEN '退款'
                    WHEN category = '投资' THEN '投资收益'
                    WHEN counterparty IS NOT NULL AND counterparty != '' THEN counterparty
                    ELSE '其他收入'
                END) as source_count
            FROM transactions
            WHERE amount > 0
            GROUP BY month
            ORDER BY month
            """
            cursor.execute(monthly_sources_query)
            monthly_sources = []
            for row in cursor.fetchall():
                month = row['month']
                source_count = int(row['source_count'])
                
                monthly_sources.append({
                    'month': month,
                    'source_count': source_count
                })
            
            return {
                'income_sources': income_sources,
                'source_count': len(income_sources),
                'concentration': concentration,
                'passive_income_ratio': passive_income_ratio,
                'monthly_sources': monthly_sources
            }
        except Exception as e:
            self.logger.error(f"获取收入多样性评估数据时出错: {e}")
            raise
        finally:
            conn.close()

    @error_handler(fallback_value={})
    def get_cash_flow_health(self):
        """获取现金流健康度数据
        
        返回：
        - 月度现金流净值趋势
        - 紧急备用金覆盖月数（账户余额/月均支出）
        - 月度资金缺口频率及规模
        """
        self.logger.info("分析现金流健康度数据")
        
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            # 获取月度现金流净值
            monthly_cash_flow_query = """
            SELECT 
                strftime('%Y-%m', transaction_date) as month,
                SUM(amount) as net_flow,
                SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) as income,
                SUM(CASE WHEN amount < 0 THEN amount ELSE 0 END) as expense
            FROM transactions
            GROUP BY month
            ORDER BY month
            """
            cursor.execute(monthly_cash_flow_query)
            monthly_cash_flow = []
            total_months = 0
            total_expense = 0
            negative_months = 0
            total_gap = 0
            
            for row in cursor.fetchall():
                month = row['month']
                net_flow = float(row['net_flow']) if row['net_flow'] else 0
                income = float(row['income']) if row['income'] else 0
                expense = float(row['expense']) if row['expense'] else 0
                
                # 计算资金缺口
                gap = 0
                if net_flow < 0:
                    negative_months += 1
                    gap = abs(net_flow)
                    total_gap += gap
                
                monthly_cash_flow.append({
                    'month': month,
                    'net_flow': net_flow,
                    'income': income,
                    'expense': expense,
                    'gap': gap
                })
                
                total_months += 1
                total_expense += abs(expense)
            
            # 计算月均支出
            avg_monthly_expense = total_expense / total_months if total_months > 0 else 0
            
            # 获取最新余额
            latest_balance_query = """
            SELECT 
                SUM(latest_balance) as total_balance
            FROM (
                SELECT 
                    a.account_number,
                    MAX(t.transaction_date) as latest_date,
                    t.balance as latest_balance
                FROM transactions t
                JOIN accounts a ON t.account_id = a.id
                WHERE t.balance IS NOT NULL
                GROUP BY a.account_number
            )
            """
            cursor.execute(latest_balance_query)
            row = cursor.fetchone()
            total_balance = float(row['total_balance']) if row and row['total_balance'] else 0
            
            # 计算紧急备用金覆盖月数
            emergency_fund_months = total_balance / abs(avg_monthly_expense) if avg_monthly_expense != 0 else 0
            
            # 计算资金缺口频率
            gap_frequency = negative_months / total_months if total_months > 0 else 0
            
            # 计算平均资金缺口
            avg_gap = total_gap / negative_months if negative_months > 0 else 0
            
            return {
                'monthly_cash_flow': monthly_cash_flow,
                'emergency_fund_months': emergency_fund_months,
                'gap_frequency': gap_frequency,
                'avg_gap': avg_gap,
                'total_balance': total_balance,
                'avg_monthly_expense': avg_monthly_expense
            }
        except Exception as e:
            self.logger.error(f"获取现金流健康度数据时出错: {e}")
            raise
        finally:
            conn.close()

    @error_handler(fallback_value={})
    def get_income_growth(self):
        """获取收入增长评估数据
        
        返回：
        - 年度/季度收入增长率
        - 收入增长与通胀对比
        - 职业收入发展轨迹
        """
        self.logger.info("分析收入增长数据")
        
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            # 获取季度收入数据
            quarterly_income_query = """
            SELECT 
                strftime('%Y', transaction_date) || '-Q' || ((CAST(strftime('%m', transaction_date) AS INTEGER) + 2) / 3) as quarter,
                SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) as income
            FROM transactions
            GROUP BY quarter
            ORDER BY quarter
            """
            cursor.execute(quarterly_income_query)
            quarterly_income = []
            quarterly_growth = []
            
            prev_income = None
            for row in cursor.fetchall():
                quarter = row['quarter']
                income = float(row['income']) if row['income'] else 0
                
                quarterly_income.append({
                    'quarter': quarter,
                    'income': income
                })
                
                # 计算环比增长率
                if prev_income is not None and prev_income > 0:
                    growth_rate = (income - prev_income) / prev_income
                    quarterly_growth.append({
                        'quarter': quarter,
                        'growth_rate': growth_rate
                    })
                
                prev_income = income
            
            # 获取年度收入数据
            yearly_income_query = """
            SELECT 
                strftime('%Y', transaction_date) as year,
                SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) as income
            FROM transactions
            GROUP BY year
            ORDER BY year
            """
            cursor.execute(yearly_income_query)
            yearly_income = []
            yearly_growth = []
            
            prev_income = None
            for row in cursor.fetchall():
                year = row['year']
                income = float(row['income']) if row['income'] else 0
                
                yearly_income.append({
                    'year': year,
                    'income': income
                })
                
                # 计算同比增长率
                if prev_income is not None and prev_income > 0:
                    growth_rate = (income - prev_income) / prev_income
                    yearly_growth.append({
                        'year': year,
                        'growth_rate': growth_rate
                    })
                
                prev_income = income
            
            # 获取工资收入趋势
            salary_trend_query = """
            SELECT 
                strftime('%Y-%m', transaction_date) as month,
                SUM(CASE WHEN amount > 0 AND (
                    description LIKE '%工资%' OR 
                    description LIKE '%薪%' OR
                    category = '工资'
                ) THEN amount ELSE 0 END) as salary_income
            FROM transactions
            GROUP BY month
            ORDER BY month
            """
            cursor.execute(salary_trend_query)
            salary_trend = []
            
            for row in cursor.fetchall():
                month = row['month']
                salary = float(row['salary_income']) if row['salary_income'] else 0
                
                salary_trend.append({
                    'month': month,
                    'salary': salary
                })
            
            # 计算收入增长统计
            avg_quarterly_growth = sum(q['growth_rate'] for q in quarterly_growth) / len(quarterly_growth) if quarterly_growth else 0
            avg_yearly_growth = sum(y['growth_rate'] for y in yearly_growth) / len(yearly_growth) if yearly_growth else 0
            
            # 假设通胀率数据（实际应用中可以从外部数据源获取）
            inflation_data = [
                {'year': '2020', 'rate': 0.02},
                {'year': '2021', 'rate': 0.015},
                {'year': '2022', 'rate': 0.02},
                {'year': '2023', 'rate': 0.022},
                {'year': '2024', 'rate': 0.025}
            ]
            
            # 比较收入增长与通胀
            income_vs_inflation = []
            for yearly in yearly_growth:
                year = yearly['year']
                growth = yearly['growth_rate']
                
                # 查找对应年份的通胀率
                inflation = next((item['rate'] for item in inflation_data if item['year'] == year), 0.02)
                
                real_growth = growth - inflation
                
                income_vs_inflation.append({
                    'year': year,
                    'income_growth': growth,
                    'inflation': inflation,
                    'real_growth': real_growth
                })
            
            return {
                'quarterly_income': quarterly_income,
                'quarterly_growth': quarterly_growth,
                'yearly_income': yearly_income,
                'yearly_growth': yearly_growth,
                'salary_trend': salary_trend,
                'income_vs_inflation': income_vs_inflation,
                'stats': {
                    'avg_quarterly_growth': avg_quarterly_growth,
                    'avg_yearly_growth': avg_yearly_growth
                }
            }
        except Exception as e:
            self.logger.error(f"获取收入增长评估数据时出错: {e}")
            raise
        finally:
            conn.close()

    @error_handler(fallback_value={})
    def get_financial_resilience(self):
        """获取财务韧性指标数据
        
        返回：
        - 突发大额支出后的恢复周期
        - 收入中断抵抗力（基于历史数据模拟）
        - 收支平衡点分析
        """
        self.logger.info("分析财务韧性指标数据")
        
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            # 获取月度收支数据用于分析
            monthly_data_query = """
            SELECT 
                strftime('%Y-%m', transaction_date) as month,
                SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) as income,
                SUM(CASE WHEN amount < 0 THEN amount ELSE 0 END) as expense,
                SUM(amount) as net_flow
            FROM transactions
            GROUP BY month
            ORDER BY month
            """
            cursor.execute(monthly_data_query)
            monthly_data = []
            for row in cursor.fetchall():
                month = row['month']
                income = float(row['income']) if row['income'] else 0
                expense = float(row['expense']) if row['expense'] else 0
                net_flow = float(row['net_flow']) if row['net_flow'] else 0
                
                monthly_data.append({
                    'month': month,
                    'income': income,
                    'expense': abs(expense),  # 转为正数便于计算
                    'net_flow': net_flow
                })
            
            # 查找大额支出及恢复周期
            large_expense_query = """
            SELECT 
                t1.transaction_date,
                t1.amount,
                t1.description,
                t1.category
            FROM transactions t1
            WHERE t1.amount < 0
            AND ABS(t1.amount) > (
                SELECT AVG(ABS(t2.amount)) * 3  -- 大于平均支出的3倍
                FROM transactions t2
                WHERE t2.amount < 0
            )
            ORDER BY ABS(t1.amount) DESC
            LIMIT 10
            """
            cursor.execute(large_expense_query)
            large_expenses = []
            for row in cursor.fetchall():
                date = row['transaction_date']
                amount = float(row['amount'])
                description = row['description']
                category = row['category']
                
                # 获取该月数据
                month = datetime.strptime(date, '%Y-%m-%d').strftime('%Y-%m')
                
                # 查找月度数据中的索引
                try:
                    index = next(i for i, m in enumerate(monthly_data) if m['month'] == month)
                    
                    # 计算恢复周期
                    recovery_months = 0
                    cumulative_net_flow = 0
                    expense_amount = abs(amount)
                    
                    for i in range(index, len(monthly_data)):
                        cumulative_net_flow += monthly_data[i]['net_flow']
                        recovery_months += 1
                        if cumulative_net_flow >= expense_amount:
                            break
                    
                    large_expenses.append({
                        'date': date,
                        'amount': amount,
                        'description': description,
                        'category': category,
                        'recovery_months': recovery_months,
                        'recovered': cumulative_net_flow >= expense_amount
                    })
                except (StopIteration, IndexError):
                    # 如果找不到对应月份，跳过
                    continue
            
            # 计算收入中断抵抗力
            # 1. 计算平均月支出
            if monthly_data:
                avg_monthly_expense = sum(m['expense'] for m in monthly_data) / len(monthly_data)
            else:
                avg_monthly_expense = 0
            
            # 2. 获取最新余额
            latest_balance_query = """
            SELECT 
                SUM(latest_balance) as total_balance
            FROM (
                SELECT 
                    a.account_number,
                    MAX(t.transaction_date) as latest_date,
                    t.balance as latest_balance
                FROM transactions t
                JOIN accounts a ON t.account_id = a.id
                WHERE t.balance IS NOT NULL
                GROUP BY a.account_number
            )
            """
            cursor.execute(latest_balance_query)
            row = cursor.fetchone()
            total_balance = float(row['total_balance']) if row and row['total_balance'] else 0
            
            # 3. 计算收入中断抵抗力（月数）
            income_interruption_resistance = total_balance / avg_monthly_expense if avg_monthly_expense > 0 else 0
            
            # 计算收支平衡点
            if monthly_data:
                # 计算平均收入和支出
                avg_monthly_income = sum(m['income'] for m in monthly_data) / len(monthly_data)
                
                # 计算固定支出占比和变动支出占比
                fixed_expense_query = """
                SELECT 
                    SUM(CASE WHEN amount < 0 AND (
                        category IN ('住房', '通讯', '保险')
                    ) THEN ABS(amount) ELSE 0 END) as fixed_expense,
                    SUM(CASE WHEN amount < 0 THEN ABS(amount) ELSE 0 END) as total_expense
                FROM transactions
                """
                cursor.execute(fixed_expense_query)
                row = cursor.fetchone()
                fixed_expense = float(row['fixed_expense']) if row['fixed_expense'] else 0
                total_expense = float(row['total_expense']) if row['total_expense'] else 0
                
                fixed_expense_ratio = fixed_expense / total_expense if total_expense > 0 else 0
                variable_expense_ratio = 1 - fixed_expense_ratio
                
                # 计算收支平衡点
                # 平衡点 = 固定支出 / (1 - 变动支出率)
                # 变动支出率 = 变动支出 / 收入
                if avg_monthly_income > 0:
                    variable_expense_rate = (total_expense * variable_expense_ratio) / (total_expense / avg_monthly_expense * avg_monthly_income)
                    break_even_point = (total_expense * fixed_expense_ratio) / (1 - variable_expense_rate) if variable_expense_rate < 1 else float('inf')
                else:
                    variable_expense_rate = 0
                    break_even_point = 0
            else:
                avg_monthly_income = 0
                fixed_expense_ratio = 0
                variable_expense_ratio = 0
                variable_expense_rate = 0
                break_even_point = 0
            
            return {
                'large_expenses': large_expenses,
                'income_interruption_resistance': income_interruption_resistance,
                'break_even_analysis': {
                    'avg_monthly_income': avg_monthly_income,
                    'avg_monthly_expense': avg_monthly_expense,
                    'fixed_expense_ratio': fixed_expense_ratio,
                    'variable_expense_ratio': variable_expense_ratio,
                    'break_even_point': break_even_point
                },
                'monthly_data': monthly_data,
                'total_balance': total_balance
            }
        except Exception as e:
            self.logger.error(f"获取财务韧性指标数据时出错: {e}")
            raise
        finally:
            conn.close()

# 如果直接运行此脚本，创建数据库结构
if __name__ == "__main__":
    db_manager = DBManager()
    print(f"数据库结构已初始化: {db_manager.db_path}")