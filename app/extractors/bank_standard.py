"""Bank standard transaction extractor - Double-Entry Version"""

import openpyxl
import xlrd
import logging
from datetime import datetime, date
from typing import List, Dict, Any
from decimal import Decimal
from .base import BaseExtractor
from app.models.dto import TransactionDTO, EntryData, AccountIdentifier

logger = logging.getLogger(__name__)

# 银行配置 (保持不变)
BANK_CONFIGS = {
    'CCB': {
        'bank_name': '建设银行',
        'bank_code': 'CCB',
        'account_name_key': '客户名称:',
        'account_number_key': '卡号/账号:',
        'transaction_header': '交易日期',
        'column_mapping': {
            '交易日期': 'date',
            '交易金额': 'amount',
            '账户余额': 'balance_after',
            '对方账号与户名': 'counterparty',
            '摘要': 'description',
            '币别': 'currency'
        },
        'date_format': '%Y%m%d'
    },
    'CMB': {
        'bank_name': '招商银行',
        'bank_code': 'CMB',
        'account_name_key': '户    名：',
        'account_number_key': '账号：',
        'transaction_header': '记账日期',
        'column_mapping': {
            '记账日期': 'date',
            '交易金额': 'amount',
            '联机余额': 'balance_after',
            '对手信息': 'counterparty',
            '交易摘要': 'description',
            '货币': 'currency'
        },
        'date_format': '%Y-%m-%d %H:%M:%S'
    }
}

class BankStandardExtractor(BaseExtractor):
    """通用银行Excel提取器 - 复式记账版本"""

    def __init__(self):
        self.configs = BANK_CONFIGS

    def can_handle(self, file_path: str, first_lines: List[str] = None) -> bool:
        return file_path.endswith(('.xls', '.xlsx')) and "支付宝" not in file_path and "微信" not in file_path

    def extract(self, file_path: str) -> List[TransactionDTO]:
        try:
            rows = []
            if file_path.lower().endswith('.xls'):
                wb = xlrd.open_workbook(file_path)
                sheet = wb.sheet_by_index(0)
                for i in range(sheet.nrows):
                    row = []
                    for j in range(sheet.ncols):
                        cell_type = sheet.cell_type(i, j)
                        val = sheet.cell_value(i, j)
                        if cell_type == xlrd.XL_CELL_DATE:
                            try:
                                val = xlrd.xldate_as_datetime(val, wb.datemode)
                            except:
                                pass
                        row.append(val)
                    rows.append(tuple(row))
            else:
                wb = openpyxl.load_workbook(file_path, data_only=True)
                sheet = wb.active
                rows = list(sheet.iter_rows(values_only=True))
            
            # 识别银行类型
            config = self._identify_bank(rows)
            if not config:
                raise ValueError("无法识别银行格式")

            # 提取账户信息
            account_name, account_number = self._extract_account_info(rows, config)
            
            # 提取交易
            transactions = self._extract_transactions(rows, config, account_name, account_number)

            logger.info(f"{config['bank_name']}提取完成: {len(transactions)} 笔交易")
            return transactions

        except Exception as e:
            logger.error(f"银行账单解析失败: {e}", exc_info=True)
            raise

    def _parse_float(self, val: Any) -> Decimal:
        """解析数值，支持千分位逗号"""
        if val is None:
            return Decimal('0')
        if isinstance(val, (int, float)):
            return Decimal(str(val))
        try:
            s = str(val).strip().replace(',', '')
            if not s:
                return Decimal('0')
            return Decimal(s)
        except:
            return Decimal('0')

    def _identify_bank(self, rows: List[tuple]) -> Dict:
        for i in range(min(10, len(rows))):
            row = rows[i]
            row_str = " ".join([str(x) for x in row if x is not None])
            for code, config in self.configs.items():
                if config['account_name_key'] in row_str or config['account_number_key'] in row_str:
                    return config
        return None

    def _extract_account_info(self, rows: List[tuple], config: Dict):
        name = None
        number = None
        for i in range(min(10, len(rows))):
            row = rows[i]
            for val in row:
                val_str = str(val) if val is not None else ""
                if config['account_name_key'] in val_str:
                    try: name = val_str.split(config['account_name_key'])[1].strip()
                    except: pass
                if config['account_number_key'] in val_str:
                    try: number = val_str.split(config['account_number_key'])[1].strip()
                    except: pass
        return name, number

    def _extract_transactions(self, rows: List[tuple], config: Dict, account_name: str, account_number: str) -> List[TransactionDTO]:
        # 找到表头
        header_row_idx = None
        for i, row in enumerate(rows):
            row_values = [str(val) for val in row if val is not None]
            if any(config['transaction_header'] in val for val in row_values):
                header_row_idx = i
                break
        
        if header_row_idx is None:
            raise ValueError("未找到交易表头")

        headers = [str(c).strip() if c is not None else "" for c in rows[header_row_idx]]
        
        mapping = config['column_mapping']
        col_indices = {}
        for col_name, field_name in mapping.items():
            try:
                idx = headers.index(col_name)
                col_indices[field_name] = idx
            except ValueError:
                for i, h in enumerate(headers):
                    if col_name in h:
                        col_indices[field_name] = i
                        break
        
        transactions = []
        
        # 构建账户标识
        bank_account = AccountIdentifier(
            bank_name=config['bank_name'],
            account_number=account_number or "unknown",
            account_name=account_name or "未知账户",
            account_type="ASSET",
            currency="CNY"
        )
        
        for i in range(header_row_idx + 1, len(rows)):
            row = rows[i]
            if not row: continue
            
            if 'date' not in col_indices: continue
            date_idx = col_indices['date']
            if date_idx >= len(row) or row[date_idx] is None: continue
            
            # 解析日期
            try:
                date_val = row[date_idx]
                if isinstance(date_val, (datetime, date)):
                    dt = date_val
                else:
                    dt = datetime.strptime(str(date_val).strip(), config['date_format'])
            except:
                continue

            # 解析金额
            try:
                amount_idx = col_indices.get('amount')
                if amount_idx is not None and amount_idx < len(row):
                    amount = self._parse_float(row[amount_idx])
                else:
                    amount = Decimal('0')
            except Exception as e:
                logger.warning(f"行 {i} 数值解析失败: {e}")
                continue

            # 其他字段
            def get_val(field):
                idx = col_indices.get(field)
                if idx is not None and idx < len(row) and row[idx] is not None:
                    val = str(row[idx]).strip()
                    return val if val else ""
                return ""

            counterparty = get_val('counterparty') or "未知交易对手"
            description = get_val('description') or "银行交易"
            
            # Entry 1: 银行账户变动
            entry_bank = EntryData(
                account_identifier=bank_account,
                amount=amount,
                memo=f"{counterparty} - {description}"
            )
            
            # Entry 2: 对应的支出/收入账户
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
                    amount=-amount,
                    memo=description
                )
                transaction_type = "EXPENSE"
                entries = [entry_bank, entry_expense]
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
                    amount=-amount,
                    memo=description
                )
                transaction_type = "INCOME"
                entries = [entry_bank, entry_income]
            
            transactions.append(TransactionDTO(
                date=dt.date() if hasattr(dt, 'date') else dt,
                description=f"{counterparty} - {description}",
                transaction_type=transaction_type,
                entries=entries,
                raw_data=None
            ))
            
        return transactions
