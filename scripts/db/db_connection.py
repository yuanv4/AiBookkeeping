import sqlite3
import os
import threading
from scripts.common.logging_setup import get_logger

logger = get_logger(__name__)

class DBConnection:
    def __init__(self, db_path=None):
        self._db_path = self._resolve_db_path(db_path)
        self._local = threading.local() # 使用 threading.local() 来存储每个线程的连接
        logger.info(f"DBConnection initialized with path: {self._db_path}")

    def _resolve_db_path(self, db_path):
        if db_path is not None and db_path != '':
            return db_path
        else:
            # Default path if not provided, similar to original db_manager
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
            return os.path.join(base_dir, 'instance', 'app.db')

    def get_connection(self):
        # 检查当前线程是否已经有一个连接
        if not hasattr(self._local, 'connection') or self._local.connection is None:
            self._local.connection = self._connect()
        return self._local.connection

    def _connect(self):
        """建立并返回一个新的数据库连接"""
        try:
            current_db_path = self._db_path
            
            if current_db_path == ':memory:':
                logger.info("Connecting to in-memory SQLite database. Skipping directory creation.")
            else:
                db_dir = os.path.dirname(current_db_path)
                if db_dir: # Only attempt makedirs if there's a non-empty directory part
                    os.makedirs(db_dir, exist_ok=True)
                    logger.debug(f"Ensured directory exists: {db_dir}")
                else:
                    # Path is a filename in CWD or an invalid/empty path.
                    # sqlite3.connect will handle CWD case.
                    logger.debug(f"Database path '{current_db_path}' has no directory component or is empty. Relying on sqlite3.connect for CWD.")
                
            conn = sqlite3.connect(current_db_path) # 每个线程独立的连接
            conn.row_factory = sqlite3.Row
            logger.info(f"Database connected for thread {threading.get_ident()}: {current_db_path}")
            return conn
        except sqlite3.Error as e:
            logger.error(f"SQLite connection error for '{current_db_path}': {e}")
            return None 
        except OSError as e:
            logger.error(f"OS error during database directory setup for '{current_db_path}': {e}")
            return None
        except Exception as e: 
            logger.error(f"Unexpected error during database connection for '{current_db_path}': {e}")
            return None

    def close_connection(self):
        """关闭当前线程的数据库连接"""
        if hasattr(self._local, 'connection') and self._local.connection is not None:
            self._local.connection.close()
            logger.info(f"Database connection closed for thread {threading.get_ident()}.")
            self._local.connection = None

    def init_db(self):
        # init_db 应该在一个主线程中执行，或者确保在执行时获取到连接
        conn = self.get_connection()
        if conn is None:
            logger.error("Cannot initialize database: No connection.")
            return

        cursor = conn.cursor()
        try:
            # Create tables
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS banks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bank_id INTEGER NOT NULL,
                    account_number TEXT NOT NULL,
                    account_name TEXT,
                    currency TEXT DEFAULT 'CNY',
                    FOREIGN KEY (bank_id) REFERENCES banks(id)
                    UNIQUE (bank_id, account_number)
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS transaction_types (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    is_income BOOLEAN NOT NULL DEFAULT 0
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_id INTEGER NOT NULL,
                    date TEXT NOT NULL,
                    type_id INTEGER NOT NULL,
                    amount REAL NOT NULL,
                    currency TEXT DEFAULT 'CNY',
                    description TEXT,
                    counterparty TEXT,
                    notes TEXT,
                    original_description TEXT,
                    FOREIGN KEY (account_id) REFERENCES accounts(id),
                    FOREIGN KEY (type_id) REFERENCES transaction_types(id)
                )
            ''')
            conn.commit()
            logger.info("Database tables created or already exist.")

            # Populate common transaction types if not exist
            common_types = [
                ('工资', True),
                ('餐饮', False),
                ('交通', False),
                ('购物', False),
                ('娱乐', False),
                ('医疗', False),
                ('教育', False),
                ('住房', False),
                ('通讯', False),
                ('其他收入', True),
                ('其他支出', False)
            ]
            for name, is_income in common_types:
                cursor.execute("INSERT OR IGNORE INTO transaction_types (name, is_income) VALUES (?, ?)", (name, is_income))
            conn.commit()
            logger.info("Common transaction types populated.")

            # Populate common banks if not exist
            common_banks = [
                '招商银行',
                '建设银行',
                '工商银行',
                '农业银行',
                '中国银行',
                '交通银行',
                '邮储银行',
                '浦发银行',
                '中信银行',
                '兴业银行',
                '民生银行',
                '光大银行',
                '平安银行',
                '华夏银行',
                '广发银行',
                '北京银行',
                '上海银行',
                '宁波银行',
                '杭州银行',
                '江苏银行',
                '南京银行',
                '徽商银行',
                '渤海银行',
                '浙商银行',
                '恒丰银行',
                '广西北部湾银行',
                '富滇银行',
                '昆仑银行',
                '盛京银行',
                '晋商银行',
                '龙江银行',
                '齐鲁银行',
                '青岛银行',
                '重庆银行',
                '成都银行',
                '贵阳银行',
                '兰州银行',
                '乌鲁木齐银行',
                '西安银行',
                '郑州银行',
                '长沙银行',
                '徽商银行',
                '东莞银行',
                '顺德农商银行',
                '广州农商银行',
                '深圳农商银行',
                '上海农商银行',
                '北京农商银行',
                '天津农商银行',
                '重庆农商银行',
                '成都农商银行',
                '武汉农商银行',
                '南京农商银行',
                '杭州联合银行',
                '苏州银行',
                '无锡银行',
                '常熟银行',
                '张家港行',
                '江阴银行',
                '吴江银行',
                '昆山农商银行',
                '江南农村商业银行',
                '东营银行',
                '威海市商业银行',
                '德州银行',
                '莱商银行',
                '日照银行',
                '临商银行',
                '齐商银行',
                '枣庄银行',
                '泰安银行',
                '济宁银行',
                '滨州银行',
                '聊城银行',
                '菏泽银行',
                '烟台银行',
                '潍坊银行',
                '泉州银行',
                '厦门银行',
                '福建海峡银行',
                '江西银行',
                '九江银行',
                '赣州银行',
                '南昌银行',
                '吉林银行',
                '哈尔滨银行',
                '大连银行',
                '锦州银行',
                '葫芦岛银行',
                '鞍山银行',
                '本溪银行',
                '丹东银行',
                '营口银行',
                '盘锦银行',
                '阜新银行',
                '朝阳银行',
                '辽阳银行',
                '铁岭银行',
                '葫芦岛银行',
                '包商银行',
                '鄂尔多斯银行',
                '乌海银行',
                '赤峰银行',
                '呼和浩特银行',
                '包头银行',
                '晋城银行',
                '长治银行',
                '阳泉银行',
                '大同银行',
                '朔州银行',
                '忻州银行',
                '吕梁银行',
                '临汾银行',
                '运城银行',
                '晋中银行',
                '晋商银行',
                '河北银行',
                '唐山银行',
                '秦皇岛银行',
                '邯郸银行',
                '邢台银行',
                '保定银行',
                '张家口银行',
                '承德银行',
                '廊坊银行',
                '沧州银行',
                '衡水银行',
                '石家庄银行',
                '沧州银行',
                '廊坊银行',
                '衡水银行',
                '邢台银行',
                '邯郸银行',
                '保定银行',
                '张家口银行',
                '承德银行',
                '唐山银行',
                '秦皇岛银行',
                '石家庄银行',
                '河北银行',
                '中原银行',
                '洛阳银行',
                '平顶山银行',
                '安阳银行',
                '焦作银行',
                '新乡银行',
                '许昌银行',
                '漯河银行',
                '三门峡银行',
                '南阳银行',
                '商丘银行',
                '信阳银行',
                '周口银行',
                '驻马店银行',
                '济源银行',
                '开封银行',
                '濮阳银行',
                '鹤壁银行',
                '许昌银行',
                '漯河银行',
                '三门峡银行',
                '南阳银行',
                '商丘银行',
                '信阳银行',
                '周口银行',
                '驻马店银行',
                '济源银行',
                '开封银行',
                '濮阳银行',
                '鹤壁银行',
                '中原银行',
                '洛阳银行',
                '平顶山银行',
                '安阳银行',
                '焦作银行',
                '新乡银行',
                '郑州银行',
                '长沙银行',
                '株洲银行',
                '湘潭银行',
                '衡阳银行',
                '邵阳银行',
                '岳阳银行',
                '常德银行',
                '张家界银行',
                '益阳银行',
                '郴州银行',
                '永州银行',
                '怀化银行',
                '娄底银行',
                '湘西银行',
                '华融湘江银行',
                '长沙银行',
                '株洲银行',
                '湘潭银行',
                '衡阳银行',
                '邵阳银行',
                '岳阳银行',
                '常德银行',
                '张家界银行',
                '益阳银行',
                '郴州银行',
                '永州银行',
                '怀化银行',
                '娄底银行',
                '湘西银行',
                '华融湘江银行',
                '湖北银行',
                '武汉农村商业银行',
                '汉口银行',
                '宜昌银行',
                '襄阳银行',
                '荆州银行',
                '黄石银行',
                '十堰银行',
                '鄂州银行',
                '孝感银行',
                '黄冈银行',
                '咸宁银行',
                '随州银行',
                '恩施银行',
                '仙桃银行',
                '潜江银行',
                '天门银行',
                '神农架林区农村商业银行',
                '湖北银行',
                '武汉农村商业银行',
                '汉口银行',
                '宜昌银行',
                '襄阳银行',
                '荆州银行',
                '黄石银行',
                '十堰银行',
                '鄂州银行',
                '孝感银行',
                '黄冈银行',
                '咸宁银行',
                '随州银行',
                '恩施银行',
                '仙桃银行',
                '潜江银行',
                '天门银行',
                '神农架林区农村商业银行',
                '广东华兴银行',
                '东莞银行',
                '广东南粤银行',
                '广州银行',
                '深圳农村商业银行',
                '珠海华润银行',
                '顺德农村商业银行',
                '南海农村商业银行',
                '广州农村商业银行',
                '深圳前海微众银行',
                '广东顺德农村商业银行',
                '广东南海农村商业银行',
                '广东中山农村商业银行',
                '广东江门农村商业银行',
                '广东肇庆农村商业银行',
                '广东惠州农村商业银行',
                '广东汕头农村商业银行',
                '广东湛江农村商业银行',
                '广东茂名农村商业银行',
                '广东梅州农村商业银行',
                '广东河源农村商业银行',
                '广东阳江农村商业银行',
                '广东清远农村农村商业银行',
                '广东潮州农村商业银行',
                '广东揭阳农村商业银行',
                '广东云浮农村商业银行',
                '广东华兴银行',
                '东莞银行',
                '广东南粤银行',
                '广州银行',
                '深圳农村商业银行',
                '珠海华润银行',
                '顺德农村商业银行',
                '南海农村商业银行',
                '广州农村商业银行',
                '深圳前海微众银行',
                '广东顺德农村商业银行',
                '广东南海农村商业银行',
                '广东中山农村商业银行',
                '广东江门农村商业银行',
                '广东肇庆农村商业银行',
                '广东惠州农村商业银行',
                '广东汕头农村商业银行',
                '广东湛江农村商业银行',
                '广东茂名农村商业银行',
                '广东梅州农村商业银行',
                '广东河源农村商业银行',
                '广东阳江农村商业银行',
                '广东清远农村农村商业银行',
                '广东潮州农村商业银行',
                '广东揭阳农村商业银行',
                '广东云浮农村商业银行',
                '富邦华一银行',
                '渣打银行',
                '汇丰银行',
                '东亚银行',
                '恒生银行',
                '星展银行',
                '花旗银行',
                '摩根大通银行',
                '美国银行',
                '德意志银行',
                '法国巴黎银行',
                '瑞士信贷银行',
                '瑞银集团',
                '三井住友银行',
                '三菱日联银行',
                '瑞穗银行',
                '澳新银行',
                '西太平洋银行',
                '澳大利亚国民银行',
                '联邦银行',
                '加拿大皇家银行',
                '多伦多道明银行',
                '加拿大丰业银行',
                '蒙特利尔银行',
                '加拿大帝国商业银行',
                '富邦华一银行',
                '渣打银行',
                '汇丰银行',
                '东亚银行',
                '恒生银行',
                '星展银行',
                '花旗银行',
                '摩根大通银行',
                '美国银行',
                '德意志银行',
                '法国巴黎银行',
                '瑞士信贷银行',
                '瑞银集团',
                '三井住友银行',
                '三菱日联银行',
                '瑞穗银行',
                '澳新银行',
                '西太平洋银行',
                '澳大利亚国民银行',
                '联邦银行',
                '加拿大皇家银行',
                '多伦多道明银行',
                '加拿大丰业银行',
                '蒙特利尔银行',
                '加拿大帝国商业银行'
            ]
            for bank_name in common_banks:
                cursor.execute("INSERT OR IGNORE INTO banks (name) VALUES (?)", (bank_name,))
            conn.commit()
            logger.info("Common banks populated.")

        except sqlite3.Error as e:
            logger.error(f"Database initialization error: {e}")
            conn.rollback()

# Example usage (for testing purposes, will be removed later)
if __name__ == "__main__":
    # Specify a test database path
    test_db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'instance', 'test_app.db'))
    
    # Ensure old test db is removed for a clean test
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
        print(f"Removed existing test DB: {test_db_path}")

    db_conn = DBConnection(test_db_path)
    conn = db_conn.get_connection()
    if conn:
        print(f"Successfully connected to {test_db_path}")
        db_conn.init_db()
        print("Database initialized.")

        # Verify tables and data
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print("Tables in DB:", [t['name'] for t in tables])

        cursor.execute("SELECT * FROM transaction_types;")
        types = cursor.fetchall()
        print("Transaction Types:", [t['name'] for t in types])

        cursor.execute("SELECT * FROM banks;")
        banks = cursor.fetchall()
        print("Banks:", [b['name'] for b in banks[:5]], "...") # Print first 5 banks

        db_conn.close_connection()
    else:
        print("Failed to connect to database.")