# 使用新的服务层
from flask import request, render_template, redirect, url_for, flash, current_app, make_response
import csv
import io
from datetime import datetime
from app.services.core.account_service import AccountService
from app.services.core.transaction_service import TransactionService
from app.utils.decorators import handle_errors

from . import transactions_bp

class Pagination:
    """简单的分页对象，模拟Flask-SQLAlchemy的分页功能"""
    def __init__(self, page, per_page, total, items=None):
        self.page = page
        self.per_page = per_page
        self.total = total
        self.items = items or []
        
    @property
    def pages(self):
        """总页数"""
        return (self.total + self.per_page - 1) // self.per_page
    
    @property
    def has_prev(self):
        """是否有上一页"""
        return self.page > 1
    
    @property
    def has_next(self):
        """是否有下一页"""
        return self.page < self.pages
    
    @property
    def prev_num(self):
        """上一页页码"""
        return self.page - 1 if self.has_prev else None
    
    @property
    def next_num(self):
        """下一页页码"""
        return self.page + 1 if self.has_next else None
    
    def iter_pages(self, left_edge=2, left_current=2, right_current=3, right_edge=2):
        """生成页码迭代器"""
        last = self.pages
        for num in range(1, last + 1):
            if num <= left_edge or \
               (self.page - left_current - 1 < num < self.page + right_current) or \
               num > last - right_edge:
                yield num

@transactions_bp.route('/') # 蓝图根路径对应 /transactions/
@handle_errors(template='transactions.html', 
               default_data={'data': {'transactions': [], 'accounts': [], 'transaction_types': [], 'currencies': [], 'current_filters': {}}, 'pagination': Pagination(1, 20, 0, []), 'total_count': 0}, 
               log_prefix="交易记录页面")
def transactions_list_route(): # 重命名函数
    """交易记录页面"""
    # 使用新的服务层
    transaction_service = TransactionService()
    
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 20, type=int)
    
    account_number_req = request.args.get('account_number', None) 
    start_date_req = request.args.get('start_date', None)
    end_date_req = request.args.get('end_date', None)
    min_amount_req = request.args.get('min_amount', None, type=float)
    max_amount_req = request.args.get('max_amount', None, type=float)
    transaction_type_req = request.args.get('type', None) 
    counterparty_req = request.args.get('counterparty', None)
    currency_req = request.args.get('currency', None) 
    account_name_req = request.args.get('account_name_filter', None)
    distinct_req = request.args.get('distinct', False, type=lambda v: v.lower() == 'true')

    offset = (page - 1) * limit

    # 构建查询过滤器
    filters = {}
    if account_number_req:
        filters['account_number'] = account_number_req
    if start_date_req:
        filters['start_date'] = start_date_req
    if end_date_req:
        filters['end_date'] = end_date_req
    if min_amount_req is not None:
        filters['min_amount'] = min_amount_req
    if max_amount_req is not None:
        filters['max_amount'] = max_amount_req
    if transaction_type_req:
        filters['transaction_type'] = transaction_type_req
    if counterparty_req:
        filters['counterparty'] = counterparty_req
    if currency_req:
        filters['currency'] = currency_req
    if account_name_req:
        filters['account_name'] = account_name_req

    # 获取交易记录和总数
    transactions_list = transaction_service.get_transactions_with_filters(
        filters=filters,
        limit=limit,
        offset=offset
    )
    
    total_transactions = transaction_service.count_transactions_with_filters(filters)

    accounts = AccountService.get_all_accounts()
    
    transaction_types_for_filter = TransactionService.get_all_transaction_types()

    currencies_for_filter = AccountService.get_all_currencies()

    current_filters = {
        'account_number': account_number_req,
        'start_date': start_date_req,
        'end_date': end_date_req,
        'min_amount': min_amount_req,
        'max_amount': max_amount_req,
        'type': transaction_type_req,
        'counterparty': counterparty_req,
        'currency': currency_req,
        'account_name_filter': account_name_req,
        'distinct': distinct_req
    }

    # 转换交易记录为模板需要的格式
    transactions_data = []
    for trans in transactions_list:
        transactions_data.append({
            'id': trans.id,
            'transaction_date': trans.date.strftime('%Y-%m-%d') if trans.date else '',
            'amount': float(trans.amount) if trans.amount else 0.0,
            'counterparty': trans.counterparty,
            'description': trans.description,
            'account_number': trans.account.account_number if trans.account else 'N/A',
            'account_name': trans.account.account_name if trans.account else 'N/A',
            'bank_name': trans.account.bank.name if trans.account and trans.account.bank else 'N/A',
            'transaction_type': trans.get_transaction_type() if trans.get_transaction_type() else 'N/A',
            'currency': trans.currency,
            'balance': float(trans.balance_after) if trans.balance_after else 0.0
        })

    # 创建分页对象
    pagination = Pagination(
        page=page,
        per_page=limit,
        total=total_transactions,
        items=transactions_data
    )
    
    data_for_template = {
        'transactions': transactions_data,
        'accounts': accounts,
        'transaction_types': transaction_types_for_filter,
        'currencies': currencies_for_filter,
        'current_filters': current_filters
    }

    return render_template(
        'transactions.html', 
        data=data_for_template,
        pagination=pagination,
        total_count=total_transactions
    )

@transactions_bp.route('/export')
@handle_errors(template='transactions.html', 
               default_data={'data': {'transactions': [], 'accounts': [], 'transaction_types': [], 'currencies': [], 'current_filters': {}}, 'pagination': Pagination(1, 20, 0, []), 'total_count': 0}, 
               log_prefix="导出交易")
def export_transactions():
    """导出交易记录"""
    format_type = request.args.get('format', 'csv')
    
    # 使用与列表页面相同的过滤逻辑
    transaction_service = TransactionService()
    
    # 获取所有过滤参数
    account_number_req = request.args.get('account_number', None) 
    start_date_req = request.args.get('start_date', None)
    end_date_req = request.args.get('end_date', None)
    min_amount_req = request.args.get('min_amount', None, type=float)
    max_amount_req = request.args.get('max_amount', None, type=float)
    transaction_type_req = request.args.get('type', None) 
    counterparty_req = request.args.get('counterparty', None)
    currency_req = request.args.get('currency', None) 
    account_name_req = request.args.get('account_name_filter', None)
    
    # 构建查询过滤器
    filters = {}
    if account_number_req:
        filters['account_number'] = account_number_req
    if start_date_req:
        filters['start_date'] = start_date_req
    if end_date_req:
        filters['end_date'] = end_date_req
    if min_amount_req is not None:
        filters['min_amount'] = min_amount_req
    if max_amount_req is not None:
        filters['max_amount'] = max_amount_req
    if transaction_type_req:
        filters['transaction_type'] = transaction_type_req
    if counterparty_req:
        filters['counterparty'] = counterparty_req
    if currency_req:
        filters['currency'] = currency_req
    if account_name_req:
        filters['account_name'] = account_name_req
    
    # 获取所有符合条件的交易记录（不分页）
    transactions_list = transaction_service.get_transactions_with_filters(
        filters=filters,
        limit=None,  # 不限制数量
        offset=0
    )
    
    if format_type.lower() == 'csv':
        return _export_csv(transactions_list)
    elif format_type.lower() == 'excel':
        return _export_excel(transactions_list)
    else:
        flash('不支持的导出格式', 'error')
        return redirect(url_for('transactions_bp.transactions_list_route'))

def _export_csv(transactions_list):
    """导出CSV格式"""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # 写入表头
    headers = ['交易日期', '金额', '对方', '描述', '账户号码', '账户名称', '银行名称', '交易类型', '货币', '余额']
    writer.writerow(headers)
    
    # 写入数据
    for trans in transactions_list:
        row = [
            trans.date.strftime('%Y-%m-%d') if trans.date else '',
            float(trans.amount) if trans.amount else 0.0,
            trans.counterparty or '',
            trans.description or '',
            trans.account.account_number if trans.account else 'N/A',
            trans.account.account_name if trans.account else 'N/A',
            trans.account.bank.name if trans.account and trans.account.bank else 'N/A',
            trans.get_transaction_type() if trans.get_transaction_type() else 'N/A',
            trans.currency or '',
            float(trans.balance_after) if trans.balance_after else 0.0
        ]
        writer.writerow(row)
    
    # 创建响应
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    response.headers['Content-Disposition'] = f'attachment; filename=transactions_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    
    return response

def _export_excel(transactions_list):
    """导出Excel格式（基础实现）"""
    # 由于没有openpyxl依赖，暂时返回CSV格式
    # 在实际部署时可以安装openpyxl并实现真正的Excel导出
    response = _export_csv(transactions_list)
    response.headers['Content-Disposition'] = f'attachment; filename=transactions_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    return response

# TODO: 以下功能待实现
# - 添加交易
# - 导入交易
# - 编辑交易