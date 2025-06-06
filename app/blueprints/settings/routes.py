from flask import request, redirect, url_for, flash, render_template, current_app

from . import settings_bp

@settings_bp.route('/')
def settings_index():
    """设置页面主页"""
    return render_template('settings.html')

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