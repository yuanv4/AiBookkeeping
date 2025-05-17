import sqlite3
import pandas as pd
import os
import logging
from pathlib import Path
from datetime import datetime
import json
import numpy as np

# 配置日志
logger = logging.getLogger('db_manager')

class DBManager:
    """数据库管理类，负责SQLite数据库的创建、连接和交易数据管理"""
    
    def __init__(self, db_path=None):
        """初始化数据库管理器
        
        Args:
            db_path: 数据库文件路径，默认为项目根目录下的data目录
        """
        if db_path is None:
            # 默认路径：项目根目录下的data/transactions.db
            root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            data_dir = os.path.join(root_dir, 'data')
            os.makedirs(data_dir, exist_ok=True)
            db_path = os.path.join(data_dir, 'transactions.db')
        
        self.db_path = db_path
        self.logger = logger
        self.logger.info(f"数据库路径设置为: {self.db_path}")
        
        # 初始化数据库
        self.init_db()
    
    def get_connection(self):
        """获取数据库连接"""
        try:
            # 设置超时时间为30秒
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            # 启用外键约束
            conn.execute("PRAGMA foreign_keys = ON")
            # 配置返回行为字典形式
            conn.row_factory = sqlite3.Row
            # 启用WAL模式，提高并发性能
            conn.execute("PRAGMA journal_mode = WAL")
            # 设置busy_timeout，避免数据库锁定
            conn.execute("PRAGMA busy_timeout = 30000")
            return conn
        except Exception as e:
            self.logger.error(f"获取数据库连接时出错: {str(e)}")
            raise
    
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
            
            # 添加常见交易类型
            common_transaction_types = [
                ('收入', 'INCOME', '收入'),
                ('支出', 'EXPENSE', '支出'),
                ('转账', 'TRANSFER', '转账'),
                ('存款', 'DEPOSIT', '收入'),
                ('取款', 'WITHDRAW', '支出'),
                ('利息', 'INTEREST', '收入'),
                ('信用卡还款', 'CREDIT_PAYMENT', '转账'),
                ('投资', 'INVESTMENT', '投资'),
                ('退款', 'REFUND', '收入'),
                ('工资', 'SALARY', '收入'),
                ('红包', 'GIFT', '收入'),
                ('餐饮', 'FOOD', '支出'),
                ('购物', 'SHOPPING', '支出'),
                ('交通', 'TRANSPORT', '支出'),
                ('房租', 'RENT', '支出'),
                ('医疗', 'HEALTHCARE', '支出'),
                ('教育', 'EDUCATION', '支出'),
                ('娱乐', 'ENTERTAINMENT', '支出'),
                ('旅行', 'TRAVEL', '支出'),
                ('其他', 'OTHER', '其他'),
            ]
            
            for type_info in common_transaction_types:
                self.get_or_create_transaction_type(type_info[0], type_info[1], type_info[2])
            
            # 添加常见银行
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
            self.logger.error(f"初始化数据库时出错: {str(e)}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def get_or_create_bank(self, bank_code, bank_name):
        """获取或创建银行记录"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM banks WHERE bank_code = ?', (bank_code,))
        bank = cursor.fetchone()
        
        if bank:
            return bank[0]
        
        cursor.execute('INSERT INTO banks (bank_code, bank_name) VALUES (?, ?)', (bank_code, bank_name))
        conn.commit()
        return cursor.lastrowid
    
    def clean_numeric(self, value):
        """清理数字格式的数据"""
        if pd.isna(value):
            return None
        
        if isinstance(value, (int, float)):
            return float(value)
        
        # 处理字符串类型的数值
        if isinstance(value, str):
            # 移除千分位分隔符和其他非数字字符
            value = value.replace(',', '').replace(' ', '')
            # 保留加减号和数字以及小数点
            value = ''.join(c for c in value if c.isdigit() or c in '.-+')
            
            try:
                return float(value)
            except ValueError:
                return None
        
        return None
    
    def get_or_create_account(self, account_number, bank_id, account_name=None):
        """获取或创建账户记录"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            # 先查找是否存在
            cursor.execute('SELECT id FROM accounts WHERE account_number = ?', (account_number,))
            result = cursor.fetchone()
            
            if result:
                return result['id']
            
            # 不存在则创建
            cursor.execute(
                'INSERT INTO accounts (account_number, bank_id, account_name) VALUES (?, ?, ?)',
                (account_number, bank_id, account_name)
            )
            conn.commit()
            
            # 返回新创建的ID
            return cursor.lastrowid
            
        except Exception as e:
            self.logger.error(f"获取或创建账户记录时出错: {str(e)}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def get_or_create_transaction_type(self, type_name, type_code=None, category=None):
        """获取或创建交易类型"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 尝试根据type_name查找
        cursor.execute('SELECT id FROM transaction_types WHERE type_name = ?', (type_name,))
        transaction_type = cursor.fetchone()
        
        if transaction_type:
            return transaction_type[0]
        
        # 如果没有找到，则创建新的
        cursor.execute(
            'INSERT INTO transaction_types (type_name, type_code, category) VALUES (?, ?, ?)',
            (type_name, type_code, category)
        )
        conn.commit()
        
        return cursor.lastrowid
    
    def import_transactions(self, df, bank_id, import_batch=None):
        """导入交易数据到数据库"""
        conn = self.get_connection()
        total_imported = 0  # 用于记录总共导入的记录数
        try:
            cursor = conn.cursor()
            
            # 获取或创建交易类型
            transaction_types = {}
            for type_name in df['transaction_type'].unique():
                if pd.notna(type_name):
                    type_id = self.get_or_create_transaction_type(type_name)
                    transaction_types[type_name] = type_id
            
            for account_number, account_df in df.groupby('account_number'):
                try:
                    # 获取或创建账户
                    account_id = self.get_or_create_account(str(account_number), bank_id)
                    
                    # 准备批量插入的数据
                    insert_data = []
                    
                    # 准备插入数据
                    for _, row in account_df.iterrows():
                        try:
                            # 处理日期
                            transaction_date = None
                            if pd.notna(row['transaction_date']):
                                # 确保日期是字符串格式，如果是Timestamp则转为字符串
                                if isinstance(row['transaction_date'], (pd.Timestamp, datetime)):
                                    transaction_date = row['transaction_date'].strftime('%Y-%m-%d')
                                else:
                                    transaction_date = str(row['transaction_date'])
                            
                            # 处理row_index
                            row_index = row['row_index'] if pd.notna(row['row_index']) else None
                            
                            # 处理金额
                            amount = self.clean_numeric(row['amount']) if pd.notna(row['amount']) else 0
                            balance = self.clean_numeric(row['balance']) if pd.notna(row['balance']) else None
                            
                            # 处理交易类型
                            trans_type = row['transaction_type'] if pd.notna(row['transaction_type']) else None
                            trans_type_id = transaction_types.get(trans_type) if trans_type else None
                            
                            # 处理交易对象和描述
                            counterparty = row['counterparty'] if pd.notna(row['counterparty']) else None
                            
                            # 将数据添加到批量插入列表
                            insert_data.append((
                                account_id,
                                transaction_date,
                                row_index,
                                amount,
                                balance,
                                trans_type_id,
                                counterparty,
                                None,  # description
                                None,  # category
                                None,  # notes
                                import_batch
                            ))
                            total_imported += 1
                            
                        except Exception as e:
                            self.logger.error(f"处理交易记录时出错: {str(e)}")
                    
                    # 批量插入数据
                    if insert_data:
                        try:
                            cursor.executemany('''
                            INSERT INTO transactions 
                            (account_id, transaction_date, row_index, amount, balance, 
                             transaction_type_id, counterparty, description, category, notes, import_batch)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ''', insert_data)
                            conn.commit()
                        except Exception as e:
                            self.logger.error(f"导入交易记录到数据库时出错: {str(e)}")
                            conn.rollback()
                
                except Exception as e:
                    self.logger.error(f"处理账号 {account_number} 时出错: {str(e)}")
                    conn.rollback()
                    
            self.logger.info(f"总共导入 {total_imported} 条交易记录到数据库")
            return total_imported
            
        except Exception as e:
            self.logger.error(f"导入交易数据时出错: {str(e)}")
            conn.rollback()
        finally:
            conn.close()
    
    def get_transactions(self, account_id=None, start_date=None, end_date=None, 
                         min_amount=None, max_amount=None, transaction_type=None,
                         counterparty=None, limit=1000, offset=0, distinct=False):
        """按条件查询交易记录
        
        Args:
            account_id: 账户ID
            start_date: 开始日期
            end_date: 结束日期
            min_amount: 最小金额
            max_amount: 最大金额
            transaction_type: 交易类型
            counterparty: 交易对方
            limit: 返回记录数限制
            offset: 分页偏移量
            distinct: 是否去除重复交易（根据日期、金额、交易类型和交易对象判断）
            
        Returns:
            交易记录字典列表
        """
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            # 构建查询条件
            conditions = []
            params = []
            
            if account_id:
                conditions.append("t.account_id = ?")
                params.append(account_id)
                
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
                
            if transaction_type:
                conditions.append("tt.type_name LIKE ?")
                params.append(f"%{transaction_type}%")
                
            if counterparty:
                conditions.append("t.counterparty LIKE ?")
                params.append(f"%{counterparty}%")
            
            # 构建WHERE子句
            where_clause = ""
            if conditions:
                where_clause = "WHERE " + " AND ".join(conditions)
            
            # 查询交易记录
            # 如果需要去重，使用GROUP BY子句
            if distinct:
                query = f'''
                    SELECT 
                        MIN(t.id) as id, 
                        t.transaction_date, 
                        t.amount, 
                        t.balance, 
                        t.counterparty, 
                        t.description, 
                        t.category, 
                        MIN(t.created_at) as created_at, 
                        t.row_index,
                        a.account_number, 
                        tt.type_name as transaction_type, 
                        b.bank_name
                    FROM transactions t
                    JOIN accounts a ON t.account_id = a.id
                    JOIN banks b ON a.bank_id = b.id
                    LEFT JOIN transaction_types tt ON t.transaction_type_id = tt.id
                    {where_clause}
                    GROUP BY t.transaction_date, t.amount, t.counterparty, tt.type_name
                    ORDER BY t.transaction_date DESC, t.row_index DESC
                    LIMIT ? OFFSET ?
                '''
            else:
                query = f'''
                    SELECT 
                        t.id, 
                        t.transaction_date, 
                        t.amount, 
                        t.balance, 
                        t.counterparty, 
                        t.description, 
                        t.category, 
                        t.created_at, 
                        t.row_index,
                        a.account_number, 
                        tt.type_name as transaction_type, 
                        b.bank_name
                    FROM transactions t
                    JOIN accounts a ON t.account_id = a.id
                    JOIN banks b ON a.bank_id = b.id
                    LEFT JOIN transaction_types tt ON t.transaction_type_id = tt.id
                    {where_clause}
                    ORDER BY t.transaction_date DESC, t.row_index DESC
                    LIMIT ? OFFSET ?
                '''
            
            # 添加参数
            params.extend([limit, offset])
            
            # 记录查询信息
            self.logger.info(f"执行交易查询: limit={limit}, offset={offset}, distinct={distinct}")
            self.logger.info(f"SQL: {query}")
            self.logger.info(f"参数: {params}")
            
            cursor.execute(query, params)
            
            # 获取结果，不再添加中文字段名，只使用原始英文字段名
            results = []
            for row in cursor.fetchall():
                # 转换为字典并直接添加到结果中
                results.append(dict(row))
            
            # 记录查询结果数量
            self.logger.info(f"查询到 {len(results)} 条交易记录")
            
            # 如果查询到了结果，记录第一条记录的信息
            if results:
                self.logger.info(f"第一条记录: {results[0]}")
            
            return results
            
        except Exception as e:
            self.logger.error(f"查询交易记录时出错: {str(e)}")
            self.logger.error(f"详细错误: {e}")
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

    def get_transactions_count(self, account_id=None, start_date=None, end_date=None, 
                          min_amount=None, max_amount=None, transaction_type=None,
                          counterparty=None, distinct=False):
        """获取符合条件的交易记录总数
        
        Args:
            account_id: 账户ID
            start_date: 开始日期
            end_date: 结束日期
            min_amount: 最小金额
            max_amount: 最大金额
            transaction_type: 交易类型
            counterparty: 交易对方
            distinct: 是否去除重复交易
            
        Returns:
            符合条件的交易记录总数
        """
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            # 构建查询条件
            conditions = []
            params = []
            
            if account_id:
                conditions.append("t.account_id = ?")
                params.append(account_id)
                
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
                
            if transaction_type:
                conditions.append("tt.type_name LIKE ?")
                params.append(f"%{transaction_type}%")
                
            if counterparty:
                conditions.append("t.counterparty LIKE ?")
                params.append(f"%{counterparty}%")
            
            # 构建WHERE子句
            where_clause = ""
            if conditions:
                where_clause = "WHERE " + " AND ".join(conditions)
            
            # 查询记录总数
            if distinct:
                query = f'''
                    SELECT COUNT(DISTINCT t.transaction_date || '_' || t.amount || '_' || IFNULL(t.counterparty, '')) as total_count
                    FROM transactions t
                    JOIN accounts a ON t.account_id = a.id
                    JOIN banks b ON a.bank_id = b.id
                    LEFT JOIN transaction_types tt ON t.transaction_type_id = tt.id
                    {where_clause}
                '''
            else:
                query = f'''
                    SELECT COUNT(*) as total_count
                    FROM transactions t
                    JOIN accounts a ON t.account_id = a.id
                    JOIN banks b ON a.bank_id = b.id
                    LEFT JOIN transaction_types tt ON t.transaction_type_id = tt.id
                    {where_clause}
                '''
            
            # 记录查询信息
            self.logger.info(f"执行交易记录总数查询: distinct={distinct}")
            self.logger.info(f"SQL: {query}")
            self.logger.info(f"参数: {params}")
            
            cursor.execute(query, params)
            result = cursor.fetchone()
            total_count = result['total_count'] if result else 0
            
            # 记录查询结果
            self.logger.info(f"符合条件的交易记录总数: {total_count}")
            
            return total_count
            
        except Exception as e:
            self.logger.error(f"查询交易记录总数时出错: {str(e)}")
            self.logger.error(f"详细错误: {e}")
            return 0
        finally:
            conn.close()

# 如果直接运行此脚本，创建数据库结构
if __name__ == "__main__":
    db_manager = DBManager()
    print(f"数据库结构已初始化: {db_manager.db_path}") 