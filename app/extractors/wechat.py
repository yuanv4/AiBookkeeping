"""WeChat Pay transaction extractor - Double-Entry Version"""

import csv
import logging
from datetime import datetime
from typing import List
from decimal import Decimal
from .base import BaseExtractor
from app.models.dto import TransactionDTO, EntryData, AccountIdentifier

logger = logging.getLogger(__name__)

class WeChatExtractor(BaseExtractor):
    """微信支付账单提取器 - 复式记账版本"""

    def can_handle(self, file_path: str, first_lines: List[str] = None) -> bool:
        if "微信" in file_path or "wechat" in file_path.lower():
            return True
            
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                head = f.read(1024)
                return "微信支付" in head
        except Exception:
            return False

    def extract(self, file_path: str) -> List[TransactionDTO]:
        try:
            account_name = "微信用户"
            account_number = "wechat_account"

            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # 寻找表头行
            header_row_idx = None
            for i, line in enumerate(lines):
                if "交易时间" in line and "金额" in line:
                    header_row_idx = i
                    break
            
            if header_row_idx is None:
                raise ValueError("无法找到微信账单表头")

            transactions = []
            
            with open(file_path, 'r', encoding='utf-8') as f:
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

                    if not row_dict.get('交易时间'):
                        continue

                    # 解析金额
                    amount_str = row_dict.get('金额(元)', '0').replace('¥', '').strip()
                    direction = row_dict.get('收/支', '').strip()
                    try:
                        amount = Decimal(amount_str)
                    except:
                        continue

                    if direction == '支出':
                        amount = -amount
                    
                    # 解析日期
                    date_str = row_dict.get('交易时间', '').strip()
                    try:
                        dt = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        continue

                    # 构建账户标识
                    wechat_account = AccountIdentifier(
                        bank_name="微信支付",
                        account_number=account_number,
                        account_name=account_name,
                        account_type="ASSET",
                        currency="CNY"
                    )
                    
                    counterparty = row_dict.get('交易对方', '未知').strip()
                    description = row_dict.get('商品', '').strip()
                    
                    # Entry 1: 微信账户变动
                    entry_wechat = EntryData(
                        account_identifier=wechat_account,
                        amount=amount,
                        memo=f"{counterparty} - {description}"
                    )
                    
                    # Entry 2: 对应的支出/收入账户
                    if amount < 0:
                        expense_account = AccountIdentifier(
                            bank_name="系统",
                            account_number="EXPENSE_GENERAL",
                            account_name="日常支出",
                            account_type="EXPENSE",
                            currency="CNY"
                        )
                        entry_expense = EntryData(
                            account_identifier=expense_account,
                            amount=-amount,
                            memo=description
                        )
                        transaction_type = "EXPENSE"
                        entries = [entry_wechat, entry_expense]
                    else:
                        income_account = AccountIdentifier(
                            bank_name="系统",
                            account_number="INCOME_GENERAL",
                            account_name="日常收入",
                            account_type="INCOME",
                            currency="CNY"
                        )
                        entry_income = EntryData(
                            account_identifier=income_account,
                            amount=-amount,
                            memo=description
                        )
                        transaction_type = "INCOME"
                        entries = [entry_wechat, entry_income]
                    
                    transactions.append(TransactionDTO(
                        date=dt.date(),
                        description=f"{counterparty} - {description}",
                        transaction_type=transaction_type,
                        entries=entries,
                        raw_data=row_dict
                    ))

            logger.info(f"微信提取完成: {len(transactions)} 笔交易")
            return transactions

        except Exception as e:
            logger.error(f"微信账单解析失败: {e}", exc_info=True)
            raise
