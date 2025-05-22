from flask import request, redirect, url_for, flash, render_template, current_app

from . import upload_bp

@upload_bp.route('/', methods=['GET', 'POST']) # 蓝图根路径对应 /upload/
def upload_file_route(): # 重命名函数以避免与原 app.py 中的函数名潜在冲突 (虽然现在分模块了)
    """文件上传页面"""
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('没有选择文件')
            # 注意 url_for 现在需要指定蓝图名 'main.dashboard'
            return redirect(url_for('main.dashboard')) 
        
        files = request.files.getlist('file')

        # 调用服务处理文件 (服务通过 current_app.file_processor_service 访问)
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
            
            result_message_display += "按银行分组统计：\n"
            for bank, stats in bank_summary.items():
                result_message_display += f"- {bank}: {stats['files']} 个文件, {stats['records']} 条记录\n"
            
            flash(f'文件上传成功: {", ".join(uploaded_filenames)}')
            flash(result_message_display)
        else:
            flash(message or '处理文件时发生未知错误，未能成功提取任何交易记录。请确保文件格式正确。')

        return redirect(url_for('main.dashboard'))
        
    # GET请求，显示上传页面
    # 模板 upload.html 应该在 app/templates/ 目录下能被找到
    return render_template('upload.html') 