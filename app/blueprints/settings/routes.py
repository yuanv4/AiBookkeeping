import logging
import time
from flask import request, redirect, url_for, flash, render_template, jsonify
from app.models.base import db
from app.utils.decorators import handle_errors, is_api_request
from app.utils import get_import_service, DataUtils

from . import settings_bp

logger = logging.getLogger(__name__)

@settings_bp.route('/')
def settings_index():
    """设置页面主页"""
    from app.utils import TransactionCompatLayer
    from app.models import CoreTransaction

    try:
        # 获取统计数据 (使用兼容层)
        summary = TransactionCompatLayer.get_summary()

        # 获取最新记录的创建时间
        latest_transaction = CoreTransaction.query.order_by(CoreTransaction.created_at.desc()).first()
        last_updated = latest_transaction.created_at if latest_transaction else None

        # 判断系统状态
        system_status = 'normal' if summary['total_count'] >= 0 else 'error'

        return render_template('settings.html',
                             total_records=summary['total_count'],
                             last_updated=last_updated,
                             system_status=system_status)
    except Exception as e:
        logger.error(f"获取系统统计数据失败: {e}")
        # 出错时使用默认值
        return render_template('settings.html',
                             total_records=0,
                             last_updated=None,
                             system_status='error')

@settings_bp.route('/delete_database', methods=['POST'])
@handle_errors
def delete_database():
    """删除数据库中的所有数据"""
    logger.info("访问数据库删除路由")
    logger.warning("开始执行数据库删除操作")

    # 删除所有表
    db.drop_all()
    logger.info("所有数据表已删除")

    # 重新创建表结构
    db.create_all()
    logger.info("数据表结构已重新创建")

    logger.warning("数据库删除操作完成")

    return DataUtils.format_api_response(
        success=True,
        message='数据库已成功清空，所有数据已删除！'
    )

@settings_bp.route('/upload', methods=['GET', 'POST'])
@handle_errors
def upload_file_route():
    """文件上传页面"""
    if request.method == 'POST':
        if 'file' not in request.files:
            if is_api_request():
                return DataUtils.format_api_response(success=False, error='没有选择文件')
            flash('没有选择文件')
            return redirect(url_for('settings_bp.upload_file_route'))

        files = request.files.getlist('file')
        start_time = time.time()

        # 获取导入服务
        import_service = get_import_service()

        # 处理文件
        processed_files_result, message = import_service.process_uploaded_files(files)
        processing_time = time.time() - start_time

        if processed_files_result:
            # 统计逻辑保持不变
            uploaded_filenames = [f.filename for f in files if f.filename]
            total_records = sum(file_info.get('record_count', 0) for file_info in processed_files_result)

            # 构建银行汇总信息
            bank_summary = {}
            for file_info in processed_files_result:
                bank = file_info.get('bank')
                if bank and bank not in bank_summary:
                    bank_summary[bank] = {'files': 0, 'records': 0}
                if bank:
                    bank_summary[bank]['files'] += 1
                    bank_summary[bank]['records'] += file_info.get('record_count', 0)

            # API请求返回JSON响应
            if is_api_request():
                return DataUtils.format_api_response(
                    success=True,
                    data={
                        'message': '文件处理完成',
                        'processed_files': processed_files_result,
                        'total_records': total_records,
                        'processing_time': round(processing_time, 2),
                        'bank_summary': bank_summary,
                        'processing_stages': [
                            {'stage': 'upload', 'status': 'completed'},
                            {'stage': 'validate', 'status': 'completed'},
                            {'stage': 'extract', 'status': 'completed'},
                            {'stage': 'save', 'status': 'completed'}
                        ]
                    }
                )

            # Web请求返回传统响应
            result_message_display = "处理完成。\n"
            result_message_display += f"成功处理 {len(processed_files_result)} 个文件，共提取 {total_records} 条交易记录。\n"
            for bank, summary in bank_summary.items():
                result_message_display += f"  {bank}: {summary['files']} 个文件，{summary['records']} 条记录\n"

            flash(result_message_display, 'success')
            return redirect(url_for('main.index'))
        else:
            # 处理失败
            if is_api_request():
                return DataUtils.format_api_response(success=False, error=message)
            flash(message, 'danger')
            return redirect(url_for('settings_bp.upload_file_route'))

    return render_template('settings.html')
