import os
import pandas as pd
import sys

print("开始测试CSV文件加载...")

# 项目根目录
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPTS_DIR = os.path.join(ROOT_DIR, 'scripts')

# 确保路径正确添加
sys.path.insert(0, ROOT_DIR)
sys.path.insert(0, SCRIPTS_DIR)

TRANSACTIONS_FOLDER = os.path.join(ROOT_DIR, 'data', 'transactions')

# 检查目录是否存在
print(f"交易数据目录: {TRANSACTIONS_FOLDER}")
if not os.path.exists(TRANSACTIONS_FOLDER):
    print(f"错误: 目录不存在: {TRANSACTIONS_FOLDER}")
    sys.exit(1)

# 获取目录中的所有CSV文件
csv_files = [f for f in os.listdir(TRANSACTIONS_FOLDER) if f.endswith('.csv')]
print(f"发现 {len(csv_files)} 个CSV文件: {csv_files}")

if not csv_files:
    print("错误: 没有找到CSV文件")
    sys.exit(1)

# 尝试读取每个CSV文件
for csv_file in csv_files:
    file_path = os.path.join(TRANSACTIONS_FOLDER, csv_file)
    print(f"\n尝试读取文件: {csv_file}")
    
    try:
        # 尝试使用utf-8编码读取
        print("使用utf-8编码...")
        df = pd.read_csv(file_path, encoding='utf-8')
        print(f"成功! 数据行数: {len(df)}")
        print(f"列名: {df.columns.tolist()}")
        print(f"前5行数据示例:")
        print(df.head())
    except Exception as e:
        print(f"使用utf-8读取失败: {str(e)}")
        
        try:
            # 尝试使用gbk编码读取
            print("使用gbk编码...")
            df = pd.read_csv(file_path, encoding='gbk')
            print(f"成功! 数据行数: {len(df)}")
            print(f"列名: {df.columns.tolist()}")
            print(f"前5行数据示例:")
            print(df.head())
        except Exception as e:
            print(f"使用gbk读取失败: {str(e)}")
            
            try:
                # 尝试使用utf-8-sig编码读取
                print("使用utf-8-sig编码...")
                df = pd.read_csv(file_path, encoding='utf-8-sig')
                print(f"成功! 数据行数: {len(df)}")
                print(f"列名: {df.columns.tolist()}")
                print(f"前5行数据示例:")
                print(df.head())
            except Exception as e:
                print(f"使用utf-8-sig读取失败: {str(e)}")
                print(f"无法读取文件 {csv_file}")

print("\n测试完成!") 