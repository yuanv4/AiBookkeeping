import sqlite3
import pandas as pd
import os
import logging
from pathlib import Path
from datetime import datetime
import json

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
            root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 创建银行表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS banks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bank_code TEXT NOT NULL UNIQUE,
                bank_name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # 创建账户表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_number TEXT NOT NULL UNIQUE,
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
                type_code TEXT NOT NULL UNIQUE,
                type_name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # 创建交易记录表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER NOT NULL,
                transaction_date DATE NOT NULL,
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
            
            # 创建索引提高查询性能
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(transaction_date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_account ON transactions(account_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions(transaction_type_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_amount ON transactions(amount)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_counterparty ON transactions(counterparty)')
            
            # 预插入常见银行
            banks = [
                ('CCB', '建设银行'),
                ('ICBC', '工商银行'),
                ('BOC', '中国银行'),
                ('ABC', '农业银行'),
                ('BOCOM', '交通银行'),
                ('CMB', '招商银行')
            ]
            
            for bank_code, bank_name in banks:
                cursor.execute(
                    'INSERT OR IGNORE INTO banks (bank_code, bank_name) VALUES (?, ?)',
                    (bank_code, bank_name)
                )
            
            # 预插入常见交易类型
            transaction_types = [
                ('income', '收入'),
                ('expense', '支出'),
                ('transfer_in', '转入'),
                ('transfer_out', '转出'),
                ('refund', '退款'),
                ('payment', '付款'),
                ('withdrawal', '取款'),
                ('deposit', '存款'),
                ('interest', '利息'),
                ('fee', '手续费'),
                ('other', '其他')
            ]
            
            for type_code, type_name in transaction_types:
                cursor.execute(
                    'INSERT OR IGNORE INTO transaction_types (type_code, type_name) VALUES (?, ?)',
                    (type_code, type_name)
                )
            
            conn.commit()
            self.logger.info("数据库表结构初始化完成")
            
        except Exception as e:
            self.logger.error(f"初始化数据库时出错: {str(e)}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
    
    def get_or_create_bank(self, bank_code, bank_name):
        """获取或创建银行记录"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            # 先查找是否存在
            cursor.execute('SELECT id FROM banks WHERE bank_code = ?', (bank_code,))
            result = cursor.fetchone()
            
            if result:
                return result['id']
            
            # 不存在则创建
            cursor.execute(
                'INSERT INTO banks (bank_code, bank_name) VALUES (?, ?)',
                (bank_code, bank_name)
            )
            conn.commit()
            
            # 返回新创建的ID
            return cursor.lastrowid
            
        except Exception as e:
            self.logger.error(f"获取或创建银行记录时出错: {str(e)}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
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
    
    def get_or_create_transaction_type(self, type_name):
        """根据名称获取或创建交易类型"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 先查找是否存在
            cursor.execute('SELECT id FROM transaction_types WHERE type_name = ?', (type_name,))
            result = cursor.fetchone()
            
            if result:
                return result['id']
            
            # 不存在则查找近似名称
            cursor.execute('SELECT id, type_name FROM transaction_types')
            all_types = {row['type_name']: row['id'] for row in cursor.fetchall()}
            
            # 简单的名称映射
            type_mapping = {
                '收入': ['收入', '收款'],
                '支出': ['支出', '消费', '购物'],
                '转入': ['转入', '存入'],
                '转出': ['转出', '转账'],
                '退款': ['退款'],
                '付款': ['付款', '支付'],
                '取款': ['取款', 'ATM'],
                '存款': ['存款'],
                '利息': ['利息'],
                '手续费': ['手续费', '服务费']
            }
            
            # 检查是否匹配任何预定义类型
            for base_type, keywords in type_mapping.items():
                if any(keyword in type_name for keyword in keywords):
                    return all_types.get(base_type)
            
            # 如果都不匹配，创建新类型
            type_code = 'custom_' + str(hash(type_name) % 10000)
            cursor.execute(
                'INSERT INTO transaction_types (type_code, type_name) VALUES (?, ?)',
                (type_code, type_name)
            )
            conn.commit()
            
            # 返回新创建的ID
            return cursor.lastrowid
            
        except Exception as e:
            self.logger.error(f"获取或创建交易类型时出错: {str(e)}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                try:
                    conn.close()
                except Exception as e:
                    self.logger.error(f"关闭数据库连接时出错: {str(e)}")
    
    def import_dataframe(self, df, bank_code, batch_id=None):
        """导入DataFrame数据到数据库
        
        Args:
            df: 包含交易数据的DataFrame
            bank_code: 银行代码
            batch_id: 导入批次ID，默认使用当前时间戳
            
        Returns:
            导入的记录数
        """
        if df is None or df.empty:
            self.logger.warning("没有数据可导入")
            return 0
            
        # 生成批次ID
        if batch_id is None:
            batch_id = f"import_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
        # 确保必要的列存在
        required_columns = ['交易日期', '交易金额', '账号']
        for col in required_columns:
            if col not in df.columns:
                self.logger.error(f"数据缺少必要的列: {col}")
                return 0
        
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 获取或创建银行ID
            bank_name = None
            if '银行' in df.columns and not df['银行'].isnull().all():
                bank_name = df['银行'].iloc[0]
                
            bank_id = self.get_or_create_bank(bank_code, bank_name or bank_code)
            
            # 预先获取所有需要的交易类型
            transaction_types = {}
            if '交易类型' in df.columns:
                unique_types = df['交易类型'].unique()
                for type_name in unique_types:
                    if pd.notna(type_name):
                        try:
                            type_id = self.get_or_create_transaction_type(type_name)
                            transaction_types[type_name] = type_id
                        except Exception as e:
                            self.logger.error(f"获取交易类型时出错: {str(e)}, 类型: {type_name}")
                            transaction_types[type_name] = None
            
            # 处理每个账户的交易
            imported_count = 0
            for account_number, account_df in df.groupby('账号'):
                try:
                    # 获取或创建账户
                    account_id = self.get_or_create_account(str(account_number), bank_id)
                    
                    # 准备批量插入的数据
                    insert_data = []
                    for _, row in account_df.iterrows():
                        try:
                            # 转换日期格式
                            transaction_date = pd.to_datetime(row['交易日期']).strftime('%Y-%m-%d')
                            
                            # 获取交易类型ID
                            transaction_type = row.get('交易类型', '其他')
                            transaction_type_id = transaction_types.get(transaction_type)
                            
                            # 提取交易金额
                            amount = float(row['交易金额'])
                            
                            # 获取交易对方
                            counterparty = row.get('交易对象', '')
                            if pd.isna(counterparty):
                                counterparty = ''
                                
                            # 获取账户余额
                            balance = row.get('账户余额')
                            if pd.isna(balance):
                                balance = None
                            else:
                                balance = float(balance)
                                
                            # 获取交易描述
                            description = row.get('交易摘要', '')
                            if pd.isna(description):
                                description = ''
                                
                            # 获取交易分类
                            category = row.get('交易分类', '')
                            if pd.isna(category):
                                category = ''
                            
                            # 检查是否存在完全相同的交易记录
                            cursor.execute('''
                                SELECT id FROM transactions 
                                WHERE account_id = ? AND transaction_date = ? AND amount = ? AND counterparty = ?
                            ''', (account_id, transaction_date, amount, counterparty))
                            
                            if cursor.fetchone() is None:
                                insert_data.append((
                                    account_id, transaction_date, amount, balance, transaction_type_id,
                                    counterparty, description, category, batch_id
                                ))
                                
                        except Exception as e:
                            self.logger.error(f"处理交易记录时出错: {str(e)}, 数据: {row.to_dict()}")
                            continue
                    
                    # 批量插入数据
                    if insert_data:
                        cursor.executemany('''
                            INSERT INTO transactions 
                            (account_id, transaction_date, amount, balance, transaction_type_id, 
                            counterparty, description, category, import_batch)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', insert_data)
                        imported_count += len(insert_data)
                        
                        # 每1000条记录提交一次事务
                        if imported_count % 1000 == 0:
                            conn.commit()
                            
                except Exception as e:
                    self.logger.error(f"处理账户 {account_number} 时出错: {str(e)}")
                    if conn:
                        conn.rollback()
                    continue
            
            # 最后提交所有更改
            if conn:
                conn.commit()
            self.logger.info(f"成功导入 {imported_count} 条交易记录")
            return imported_count
            
        except Exception as e:
            self.logger.error(f"导入数据时出错: {str(e)}")
            if conn:
                conn.rollback()
            return 0
        finally:
            if conn:
                try:
                    conn.close()
                except Exception as e:
                    self.logger.error(f"关闭数据库连接时出错: {str(e)}")
    
    def get_transactions(self, account_id=None, start_date=None, end_date=None, 
                         min_amount=None, max_amount=None, transaction_type=None,
                         counterparty=None, limit=1000, offset=0):
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
            query = f'''
                SELECT 
                    t.id, t.transaction_date, t.amount, t.balance, t.counterparty, 
                    t.description, t.category, t.created_at,
                    a.account_number, tt.type_name as transaction_type, b.bank_name
                FROM transactions t
                JOIN accounts a ON t.account_id = a.id
                JOIN banks b ON a.bank_id = b.id
                LEFT JOIN transaction_types tt ON t.transaction_type_id = tt.id
                {where_clause}
                ORDER BY t.transaction_date DESC
                LIMIT ? OFFSET ?
            '''
            
            params.extend([limit, offset])
            cursor.execute(query, params)
            
            # 返回结果
            results = []
            for row in cursor.fetchall():
                results.append(dict(row))
            
            return results
            
        except Exception as e:
            self.logger.error(f"查询交易记录时出错: {str(e)}")
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
            
            query = '''
                WITH latest_transactions AS (
                    SELECT 
                        t.account_id,
                        t.balance,
                        t.transaction_date,
                        ROW_NUMBER() OVER (PARTITION BY t.account_id ORDER BY t.transaction_date DESC) as rn
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
                FROM accounts a
                JOIN banks b ON a.bank_id = b.id
                LEFT JOIN latest_transactions lt ON a.id = lt.account_id AND lt.rn = 1
                ORDER BY b.bank_name, a.account_number
            '''
            
            cursor.execute(query)
            
            # 返回结果
            results = []
            for row in cursor.fetchall():
                results.append(dict(row))
            
            return results
            
        except Exception as e:
            self.logger.error(f"获取余额汇总时出错: {str(e)}")
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
            
            # 交易总数
            cursor.execute("SELECT COUNT(*) as count FROM transactions")
            stats['total_transactions'] = cursor.fetchone()['count']
            
            # 账户总数
            cursor.execute("SELECT COUNT(*) as count FROM accounts")
            stats['total_accounts'] = cursor.fetchone()['count']
            
            # 收入和支出总额
            cursor.execute("""
                SELECT 
                    SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) as total_income,
                    SUM(CASE WHEN amount < 0 THEN amount ELSE 0 END) as total_expense,
                    SUM(amount) as net_amount
                FROM transactions
            """)
            result = cursor.fetchone()
            stats['total_income'] = result['total_income'] or 0
            stats['total_expense'] = result['total_expense'] or 0
            stats['net_amount'] = result['net_amount'] or 0
            
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
            
            # 按银行统计
            cursor.execute("""
                SELECT 
                    b.bank_name,
                    COUNT(t.id) as transaction_count,
                    SUM(CASE WHEN t.amount > 0 THEN t.amount ELSE 0 END) as income,
                    SUM(CASE WHEN t.amount < 0 THEN t.amount ELSE 0 END) as expense
                FROM transactions t
                JOIN accounts a ON t.account_id = a.id
                JOIN banks b ON a.bank_id = b.id
                GROUP BY b.bank_name
                ORDER BY transaction_count DESC
            """)
            stats['bank_stats'] = [dict(row) for row in cursor.fetchall()]
            
            # 按账户统计
            cursor.execute("""
                SELECT 
                    a.account_number,
                    b.bank_name,
                    COUNT(t.id) as transaction_count,
                    SUM(CASE WHEN t.amount > 0 THEN t.amount ELSE 0 END) as income,
                    SUM(CASE WHEN t.amount < 0 THEN t.amount ELSE 0 END) as expense,
                    (
                        SELECT balance
                        FROM transactions
                        WHERE account_id = a.id AND balance IS NOT NULL
                        ORDER BY transaction_date DESC
                        LIMIT 1
                    ) as latest_balance
                FROM accounts a
                JOIN banks b ON a.bank_id = b.id
                LEFT JOIN transactions t ON a.id = t.account_id
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

# 如果直接运行此脚本，创建数据库结构
if __name__ == "__main__":
    db_manager = DBManager()
    print(f"数据库结构已初始化: {db_manager.db_path}") 