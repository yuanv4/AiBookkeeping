#!/usr/bin/env python
"""
测试脚本：验证建设银行(CCB)提取器的修复
"""
import sys
import os
import logging
from pathlib import Path

# 添加项目根目录到PYTHONPATH
current_dir = os.path.dirname(os.path.abspath(__file__))
scripts_dir = current_dir
root_dir = os.path.dirname(scripts_dir)
if root_dir not in sys.path:
    sys.path.append(root_dir)
if scripts_dir not in sys.path:
    sys.path.append(scripts_dir)

from scripts.extractors.banks.ccb_transaction_extractor import CCBTransactionExtractor
from scripts.extractors.factory.extractor_factory import get_extractor_factory

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger('test_ccb_extractor')

def test_ccb_extractor():
    """测试CCB提取器是否能正确处理流水文件"""
    print("=" * 60)
    print("测试建设银行(CCB)提取器")
    print("=" * 60)
    
    # 获取测试文件路径
    upload_dir = os.path.join(root_dir, "uploads")
    
    # 查找CCB的测试文件
    ccb_files = []
    for file in os.listdir(upload_dir):
        if "建设银行" in file and file.endswith((".xls", ".xlsx")):
            ccb_files.append(os.path.join(upload_dir, file))
    
    if not ccb_files:
        print("未找到建设银行测试文件。请确保uploads目录中有带有'建设银行'字样的Excel文件。")
        return
    
    print(f"找到 {len(ccb_files)} 个建设银行流水文件:")
    for file in ccb_files:
        print(f"  - {os.path.basename(file)}")
    
    # 创建提取器并处理文件
    ccb_extractor = CCBTransactionExtractor()
    
    # 测试单独处理文件
    for file_path in ccb_files:
        print(f"\n处理文件: {os.path.basename(file_path)}")
        try:
            result = ccb_extractor.process_file(file_path)
            if result and result.get('success'):
                print(f"✓ 成功处理文件，提取了 {result.get('record_count', 0)} 条记录")
                print(f"  账号: {result.get('account_number', 'unknown')}")
            else:
                error_message = result.get('message', '未知错误') if result else '处理失败'
                print(f"✗ 处理失败: {error_message}")
        except Exception as e:
            print(f"✗ 处理出错: {str(e)}")
    
    # 测试工厂模式处理文件
    print("\n测试通过工厂处理文件:")
    factory = get_extractor_factory()
    processed_files = factory.auto_detect_and_process(upload_dir)
    ccb_processed = [f for f in processed_files if os.path.basename(f['file']) in [os.path.basename(f) for f in ccb_files]]
    
    if ccb_processed:
        print(f"✓ 成功通过工厂处理 {len(ccb_processed)} 个建设银行文件")
        for result in ccb_processed:
            print(f"  - {result['file']}: 提取了 {result['record_count']} 条记录")
    else:
        print("✗ 工厂模式未能处理任何建设银行文件")
    
    print("\n测试完成!")
    print("=" * 60)

if __name__ == "__main__":
    test_ccb_extractor() 