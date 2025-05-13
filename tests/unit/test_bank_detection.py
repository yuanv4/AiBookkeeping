import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径以便导入模块
script_dir = Path(os.path.dirname(os.path.abspath(__file__)))
root_dir = script_dir.parent.parent  # 上溯两级到项目根目录
scripts_dir = root_dir / "scripts"

# 确保scripts目录在Python路径中
sys.path.insert(0, str(root_dir))
sys.path.insert(0, str(scripts_dir))

try:
    from scripts.bank_transaction_extractor import BankTransactionExtractor
    from scripts.cmb_transaction_extractor import CMBTransactionExtractor
    from scripts.ccb_transaction_extractor import CCBTransactionExtractor
except ImportError:
    # 如果上面的导入失败，尝试直接导入
    from bank_transaction_extractor import BankTransactionExtractor
    from cmb_transaction_extractor import CMBTransactionExtractor
    from ccb_transaction_extractor import CCBTransactionExtractor

def test_bank_detection():
    """测试银行类型检测功能"""
    print("=" * 60)
    print("银行类型检测测试")
    print("=" * 60)
    
    # 获取上传目录中的所有Excel文件
    upload_dir = root_dir / "uploads"
    
    excel_files = []
    for ext in ['*.xlsx', '*.xls']:
        excel_files.extend(list(upload_dir.glob(ext)))
    
    # 过滤掉临时文件
    excel_files = [f for f in excel_files if not f.name.startswith('~$')]
    
    if not excel_files:
        print("没有找到Excel文件，测试结束。")
        return
    
    print(f"找到 {len(excel_files)} 个Excel文件: {[f.name for f in excel_files]}")
    
    # 创建提取器
    extractors = [
        CMBTransactionExtractor(),
        CCBTransactionExtractor()
    ]
    
    # 测试每个文件
    for file_path in excel_files:
        print(f"\n测试文件: {file_path.name}")
        
        # 测试每个提取器
        for extractor in extractors:
            bank_name = extractor.bank_name
            print(f"  尝试 {bank_name} 提取器...")
            
            # 检查是否可以处理
            can_process = extractor.can_process_file(file_path)
            
            if can_process:
                print(f"  ✓ {bank_name} 提取器可以处理此文件")
            else:
                print(f"  ✗ {bank_name} 提取器不能处理此文件")
        
        # 直接使用基类的自动检测功能
        print("\n  使用自动检测功能:")
        result = None
        for extractor in extractors:
            if extractor.can_process_file(file_path):
                result = extractor.bank_name
                break
                
        if result:
            print(f"  ✓ 自动检测结果: {result}")
        else:
            print(f"  ✗ 无法自动检测银行类型")
    
    print("\n测试完成!")
    print("=" * 60)

if __name__ == "__main__":
    test_bank_detection() 