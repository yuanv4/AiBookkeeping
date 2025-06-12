from flask import request, redirect, url_for, flash, render_template, current_app, jsonify
from app.models.base import db

from . import settings_bp

@settings_bp.route('/')
def settings_index():
    """设置页面主页"""
    return render_template('settings.html')

@settings_bp.route('/delete_database', methods=['POST'])
def delete_database():
    """删除数据库中的所有数据"""
    try:
        # 记录操作日志
        current_app.logger.warning("开始执行数据库删除操作")
        
        # 删除所有表
        db.drop_all()
        current_app.logger.info("所有数据表已删除")
        
        # 重新创建表结构
        db.create_all()
        current_app.logger.info("数据表结构已重新创建")
        
        current_app.logger.warning("数据库删除操作完成")
        
        return jsonify({
            'success': True,
            'message': '数据库已成功清空，所有数据已删除！'
        })
        
    except Exception as e:
        current_app.logger.error(f"数据库删除操作失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'数据库删除失败: {str(e)}'
        }), 500

@settings_bp.route('/upload', methods=['GET', 'POST'])
def upload_file_route():
    """文件上传页面 - 从upload蓝图迁移过来"""
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('没有选择文件')
            return redirect(url_for('settings_bp.upload_file_route')) 
        
        files = request.files.getlist('file')

        # 调用服务处理文件
        processed_files_result, message = current_app.file_processor_service.process_uploaded_files(files)

        if processed_files_result:
            uploaded_filenames = [f.filename for f in files if f.filename] 
            result_message_display = "处理完成。\n"
            result_message_display += f"成功处理 {len(processed_files_result)} 个文件，共提取 "
            total_records = sum(file_info['record_count'] for file_info in processed_files_result)
            result_message_display += f"{total_records} 条交易记录。\n"
            
            bank_summary = {}
            for file_info in processed_files_result:
                bank = file_info['bank']
                if bank not in bank_summary:
                    bank_summary[bank] = {'files': 0, 'records': 0}
                bank_summary[bank]['files'] += 1
                bank_summary[bank]['records'] += file_info['record_count']
            
            for bank, summary in bank_summary.items():
                result_message_display += f"  {bank}: {summary['files']} 个文件，{summary['records']} 条记录\n"
            
            flash(result_message_display, 'success')
            return redirect(url_for('main.dashboard'))
        else:
            flash(message, 'danger')
            return redirect(url_for('settings_bp.upload_file_route'))
    
    return render_template('settings.html')