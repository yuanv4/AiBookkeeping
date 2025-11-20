"""Import service for double-entry bookkeeping system"""

import logging
from pathlib import Path
from typing import List, Any, Dict
from werkzeug.utils import secure_filename
from decimal import Decimal

from app.models import db, Account, CoreTransaction, Entry
from app.models.dto import TransactionDTO, AccountIdentifier
from app.extractors.factory import ExtractorFactory

logger = logging.getLogger(__name__)

class ImportService:
    """导入流程协调者 - 复式记账版本"""

    def __init__(self, upload_folder='uploads'):
        self.upload_folder = Path(upload_folder)
        self.upload_folder.mkdir(exist_ok=True)
        self._account_cache = {}  # 缓存账户，避免重复查询

    def process_uploaded_files(self, file_objects: List[Any]) -> tuple:
        """处理上传的文件列表"""
        logger.info(f"开始处理上传文件批次，共 {len(file_objects)} 个文件")
        results = []
        
        for file_obj in file_objects:
            if not file_obj.filename: continue
            
            filename = secure_filename(file_obj.filename)
            file_path = self.upload_folder / filename
            
            try:
                logger.info(f"接收文件: {filename}")
                file_obj.save(file_path)
                result = self._process_single_file(str(file_path))
                results.append(result)
            except Exception as e:
                logger.error(f"处理文件 {filename} 失败: {e}", exc_info=True)
                results.append({
                    "success": False, 
                    "file": filename, 
                    "error": str(e),
                    "data": None
                })
            finally:
                if file_path.exists():
                    try: file_path.unlink()
                    except: pass

        success_count = sum(1 for r in results if r['success'])
        msg = f"处理完成: 成功 {success_count}/{len(results)}"
        logger.info(f"批次处理完成. {msg}")
        return results, msg

    def _process_single_file(self, file_path: str) -> dict:
        """处理单个文件"""
        filename = Path(file_path).name
        logger.info(f"开始解析文件: {filename}")

        # 1. 获取提取器
        extractor = ExtractorFactory.get_extractor(file_path)
        if not extractor:
            logger.warning(f"未找到支持的提取器: {filename}")
            return {"success": False, "error": "不支持的文件格式", "file_path": file_path}
        
        logger.info(f"使用提取器: {extractor.__class__.__name__}")

        # 2. 提取数据
        try:
            transaction_dtos = extractor.extract(file_path)
            logger.info(f"提取成功: {len(transaction_dtos)} 笔交易")
        except Exception as e:
            logger.error(f"提取失败 {filename}: {e}", exc_info=True)
            return {"success": False, "error": f"提取失败: {str(e)}", "file_path": file_path}
        
        # 3. 入库
        added_count = 0
        duplicate_count = 0
        
        for dto in transaction_dtos:
            # 检查是否重复
            if self._is_duplicate(dto):
                duplicate_count += 1
                continue
            
            # 创建交易和分录
            try:
                self._create_transaction(dto)
                added_count += 1
            except Exception as e:
                logger.error(f"入库失败 {dto.description}: {e}", exc_info=True)
                continue
        
        logger.info(f"入库完成 {filename}: 新增 {added_count} 条, 重复 {duplicate_count} 条, 总计 {len(transaction_dtos)} 条")
        
        # 提取银行名（从第一个交易的账户信息）
        bank_name = "Unknown"
        if transaction_dtos and transaction_dtos[0].entries:
            first_entry = transaction_dtos[0].entries[0]
            bank_name = first_entry.account_identifier.bank_name
        
        return {
            "success": True,
            "bank": bank_name,
            "record_count": added_count,
            "total_extracted": len(transaction_dtos),
            "file_path": file_path
        }

    def _find_or_create_account(self, identifier: AccountIdentifier) -> Account:
        """查找或创建账户"""
        # 使用缓存避免重复查询
        cache_key = f"{identifier.bank_name}:{identifier.account_number}"
        if cache_key in self._account_cache:
            return self._account_cache[cache_key]
        
        # 查询数据库
        account = Account.query.filter_by(
            bank_name=identifier.bank_name,
            account_number=identifier.account_number
        ).first()
        
        if not account:
            # 创建新账户
            account = Account(
                name=identifier.account_name,
                type=identifier.account_type,
                currency=identifier.currency,
                bank_name=identifier.bank_name,
                account_number=identifier.account_number,
                balance=Decimal('0')
            )
            db.session.add(account)
            db.session.flush()  # 获取 ID，但不提交
            logger.info(f"创建新账户: {account.name} ({identifier.bank_name} - {identifier.account_number})")
        
        self._account_cache[cache_key] = account
        return account

    def _create_transaction(self, dto: TransactionDTO):
        """创建交易和分录（增强版 - 提取商户名和分类）"""
        # 提取商户名
        merchant_name = self._extract_merchant_name(dto)

        # 提取数据源分类
        source_category = self._extract_source_category(dto)

        # 创建交易
        transaction = CoreTransaction(
            date=dto.date,
            description=dto.description,
            merchant_name=merchant_name,
            source_category=source_category,
            type=dto.transaction_type,
            link_id=dto.link_id,
            raw_data=dto.raw_data
        )
        db.session.add(transaction)
        db.session.flush()  # 获取 transaction_id
        
        # 创建分录
        for entry_data in dto.entries:
            account = self._find_or_create_account(entry_data.account_identifier)
            
            entry = Entry(
                transaction_id=transaction.id,
                account_id=account.id,
                amount=entry_data.amount,
                memo=entry_data.memo
            )
            db.session.add(entry)
            
            # 更新账户余额
            account.balance += entry_data.amount
        
        db.session.commit()
        logger.debug(f"创建交易: {transaction.description} (ID: {transaction.id}) "
                    f"商户: {merchant_name}, 源分类: {source_category}")

    def _is_duplicate(self, dto: TransactionDTO) -> bool:
        """检查交易是否重复 (简化版)"""
        # 基于日期、描述和第一个 Entry 的金额判断
        if not dto.entries:
            return False
        
        first_entry = dto.entries[0]
        amount = first_entry.amount
        
        # 查询是否存在相同日期、描述和金额的交易
        existing = CoreTransaction.query.filter_by(
            date=dto.date,
            description=dto.description
        ).join(Entry).filter(
            Entry.amount == amount
        ).first()
        
        return existing is not None

    def _extract_merchant_name(self, dto: TransactionDTO) -> str:
        """
        从 TransactionDTO 中提取商户名称

        优先级：
        1. raw_data 中的商户字段（支付宝、微信、银行字段名不同）
        2. description（去除可能的后缀）
        """
        if dto.raw_data:
            # 尝试常见的商户字段名
            merchant_fields = ['商户', '对方名称', '交易对方', '收/付款方名称',
                             'counterparty', 'merchant']

            for field in merchant_fields:
                value = dto.raw_data.get(field)
                if value and isinstance(value, str) and value.strip():
                    return value.strip()

        # 回退到 description，尝试清理格式
        desc = dto.description.strip()

        # 去除常见的后缀分隔符
        for separator in ['-', '—', '·', '(', '（']:
            if separator in desc:
                desc = desc.split(separator)[0].strip()
                break

        return desc if desc else None

    def _extract_source_category(self, dto: TransactionDTO) -> str:
        """
        从 TransactionDTO 中提取数据源原始分类

        不同数据源的分类字段：
        - 支付宝：raw_data['交易类型'], raw_data['分类']
        - 微信：raw_data['类型'], raw_data['交易类型']
        - 银行：raw_data['交易类型'], raw_data['摘要']
        """
        if not dto.raw_data:
            return None

        # 按优先级尝试不同字段名
        category_fields = ['交易类型', '类型', '分类', '摘要', 'category']

        for field in category_fields:
            value = dto.raw_data.get(field)
            if value and isinstance(value, str) and value.strip():
                return value.strip()

        return None  # 没有找到分类信息
