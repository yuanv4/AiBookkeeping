"""Alipay transaction extractor - Double-Entry Version"""

import csv
import logging
from datetime import datetime
from typing import List
from decimal import Decimal
from .base import BaseExtractor
from app.models.dto import TransactionDTO, EntryData, AccountIdentifier

logger = logging.getLogger(__name__)

class AliPayExtractor(BaseExtractor):
    """支付宝账单提取器 - 复式记账版本"""

    def can_handle(self, file_path: str, first_lines: List[str] = None) -> bool:
        if "支付宝" in file_path or "alipay" in file_path.lower():
            return True
        
        try:
            with open(file_path, 'r', encoding='gbk', errors='ignore') as f:
                head = f.read(1024)
                return "支付宝" in head
        except Exception:
            return False

    def extract(self, file_path: str) -> List[TransactionDTO]:
        try:
            # 1. 读取账户元数据
            account_name = "未知用户"
            account_number = "alipay_account"
            
            with open(file_path, 'r', encoding='gbk', errors='ignore') as f:
                lines = f.readlines()

            for i in range(min(20, len(lines))):
                line = lines[i]
                if "姓名：" in line or "姓名:" in line:
                    account_name = line.split("：")[-1].strip() if "：" in line else line.split(":")[-1].strip()
                
                if "支付宝账号" in line or "支付宝账户" in line:
                    sep = "：" if "：" in line else ":"
                    if sep in line:
                        account_number = line.split(sep)[-1].strip()

            # 2. 找到表头
            header_row_idx = None
            for i, line in enumerate(lines):
                if ("交易创建时间" in line or "交易时间" in line) and "金额" in line:
                    header_row_idx = i
                    break
            
            if header_row_idx is None:
                raise ValueError("无法找到支付宝账单表头")

            # 3. 解析交易数据
            transactions = []
            
            with open(file_path, 'r', encoding='gbk', errors='ignore') as f:
                reader = csv.reader(f)
                for _ in range(header_row_idx):
                    next(reader)
                
                headers = next(reader)
                headers = [h.strip() for h in headers]
                
                for row in reader:
                    if not row or len(row) < len(headers):
                        continue
                        
                    row_dict = {}
                    for i, h in enumerate(headers):
                        if i < len(row):
                            row_dict[h] = row[i].strip()
                    
                    # 获取交易时间
                    date_val = row_dict.get('交易创建时间') or row_dict.get('交易时间')
                    if not date_val:
                        continue
                    
                    # 解析金额和方向
                    amount_str = row_dict.get('金额（元）') or row_dict.get('金额', '0')
                    direction = row_dict.get('收/支', '').strip()
                    try:
                        amount = Decimal(amount_str)
                    except:
                        continue
                        
                    if direction == '支出':
                        amount = -amount
                    
                    # 解析日期
                    try:
                        dt = datetime.strptime(date_val.strip(), '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        continue

                    # 构建账户标识
                    alipay_account = AccountIdentifier(
                        bank_name="支付宝",
                        account_number=account_number,
                        account_name=account_name,
                        account_type="ASSET",
                        currency="CNY"
                    )
                    
                    # 构建分录
                    description = (row_dict.get('商品名称') or row_dict.get('商品说明', '')).strip()
                    counterparty = row_dict.get('交易对方', '未知').strip()
                    
                    # Entry 1: 支付宝账户变动
                    entry_alipay = EntryData(
                        account_identifier=alipay_account,
                        amount=amount,
                        memo=f"{counterparty} - {description}"
                    )
                    
                    # Entry 2: 对应的支出/收入账户 (虚拟账户)
                    if amount < 0:
                        # 支出
                        expense_account = AccountIdentifier(
                            bank_name="系统",
                            account_number="EXPENSE_GENERAL",
                            account_name="日常支出",
                            account_type="EXPENSE",
                            currency="CNY"
                        )
                        entry_expense = EntryData(
                            account_identifier=expense_account,
                            amount=-amount,  # 支出账户增加 (正数)
                            memo=description
                        )
                        transaction_type = "EXPENSE"
                        entries = [entry_alipay, entry_expense]
                    else:
                        # 收入
                        income_account = AccountIdentifier(
                            bank_name="系统",
                            account_number="INCOME_GENERAL",
                            account_name="日常收入",
                            account_type="INCOME",
                            currency="CNY"
                        )
                        entry_income = EntryData(
                            account_identifier=income_account,
                            amount=-amount,  # 收入账户减少 (负数，因为是贷方)
                            memo=description
                        )
                        transaction_type = "INCOME"
                        entries = [entry_alipay, entry_income]
                    
                    # 构建 TransactionDTO
                    transactions.append(TransactionDTO(
                        date=dt.date(),
                        description=f"{counterparty} - {description}",
                        transaction_type=transaction_type,
                        entries=entries,
                        raw_data=row_dict
                    ))

            logger.info(f"支付宝提取完成: {len(transactions)} 笔交易")
            return transactions

        except Exception as e:
            logger.error(f"支付宝账单解析失败: {e}", exc_info=True)
            raise
