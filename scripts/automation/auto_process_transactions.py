import os
import sys
from pathlib import Path

# 添加脚本目录到Python路径
script_dir = Path(os.path.dirname(os.path.abspath(__file__)))
scripts_dir = script_dir.parent
root_dir = scripts_dir.parent
sys.path.append(str(root_dir))  # 添加项目根目录
sys.path.append(str(scripts_dir))  # 添加脚本目录

# 导入各模块
try:
    from scripts.extractors.bank_transaction_extractor import BankTransactionExtractor
    from scripts.analyzers.transaction_analyzer import TransactionAnalyzer
except ImportError as e:
    print(f"导入模块失败: {e}")
    print("请确保scripts目录及其子目录在Python路径中")
    sys.exit(1)

def main():
    """
    自动处理银行交易明细:
    1. 扫描uploads目录中的Excel文件
    2. 自动检测银行类型并进行提取
    3. 分析提取的交易数据
    """
    print("=" * 60)
    print("自动银行交易明细处理系统")
    print("=" * 60)
    
    # 获取脚本的根目录
    root_dir = Path(os.path.dirname(script_dir))
    
    # 指定目录路径
    upload_dir = root_dir / "uploads"
    data_dir = root_dir / "data" / "transactions"
    output_file = root_dir / "data" / "analysis_data.json"
    
    print(f"上传目录: {upload_dir}")
    print(f"数据目录: {data_dir}")
    print(f"分析输出文件: {output_file}")
    
    # 自动检测银行类型并处理文件
    print("\n步骤 1: 自动处理银行交易明细文件...")
    processed_files = BankTransactionExtractor.auto_detect_bank_and_process(upload_dir, data_dir)
    
    if not processed_files:
        print("没有处理任何文件，程序结束。")
        return
    
    # 等待用户确认
    input("\n按Enter键继续分析提取的交易数据...")
    
    # 分析提取的交易数据
    print("\n步骤 2: 分析交易数据...")
    analyzer = TransactionAnalyzer()
    if analyzer.load_multiple_data(data_dir):
        # 生成分析数据
        if analyzer.generate_json_data(output_file):
            print(f"分析数据已保存到 {output_file}")
        else:
            print("生成分析数据失败")
    else:
        print("加载交易数据失败")
    
    print("\n处理完成!")
    print("=" * 60)

if __name__ == "__main__":
    main() 