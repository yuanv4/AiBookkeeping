import os
import sys
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('test_analysis')

# 项目根目录
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPTS_DIR = os.path.join(ROOT_DIR, 'scripts')

# 确保路径正确添加
sys.path.insert(0, ROOT_DIR)
sys.path.insert(0, SCRIPTS_DIR)

# 导入 app.py 中的 generate_analysis_data 函数
print("导入 app.py 中的 generate_analysis_data 函数...")
try:
    from app import generate_analysis_data, TRANSACTIONS_FOLDER, DATA_FOLDER, TransactionAnalyzer
except ImportError as e:
    print(f"导入错误: {e}")
    sys.exit(1)

print(f"交易数据目录: {TRANSACTIONS_FOLDER}")
print(f"数据目录: {DATA_FOLDER}")

# 检查目录是否存在
if not os.path.exists(TRANSACTIONS_FOLDER):
    print(f"错误: 交易数据目录不存在: {TRANSACTIONS_FOLDER}")
    sys.exit(1)

# 获取目录中的所有CSV文件
csv_files = [f for f in os.listdir(TRANSACTIONS_FOLDER) if f.endswith('.csv')]
print(f"发现 {len(csv_files)} 个CSV文件: {csv_files}")

if not csv_files:
    print("错误: 没有找到CSV文件")
    sys.exit(1)

# 直接使用交易分析器加载数据
print("\n尝试直接使用交易分析器加载数据...")
analyzer = TransactionAnalyzer()
if analyzer.load_multiple_data(TRANSACTIONS_FOLDER):
    print("成功加载交易数据!")
    
    # 生成分析数据
    print("\n尝试生成分析数据...")
    json_file = os.path.join(DATA_FOLDER, 'analysis_data.json')
    if analyzer.generate_json_data(json_file):
        print(f"成功生成分析数据并保存到: {json_file}")
    else:
        print("生成分析数据失败")
else:
    print("加载交易数据失败")

# 运行 app.py 中的 generate_analysis_data 函数
print("\n尝试运行 app.py 中的 generate_analysis_data 函数...")
result = generate_analysis_data()
print(f"generate_analysis_data 返回值: {result}")

print("\n测试完成!") 