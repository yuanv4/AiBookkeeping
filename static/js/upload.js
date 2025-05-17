/**
 * 上传页面的JavaScript逻辑
 * 用于处理文件上传交互和验证
 */

document.addEventListener('DOMContentLoaded', function() {
    // 获取文件输入和帮助按钮元素
    const fileInput = document.getElementById('file');
    const fileInfoBtn = document.getElementById('file-info-btn');
    
    // 监听文件选择变化
    if (fileInput) {
        fileInput.addEventListener('change', function() {
            if (this.files.length > 0) {
                // 生成文件名提示
                let fileNames = Array.from(this.files).map(file => file.name).join(', ');
                this.setAttribute('title', fileNames);
                
                // 在文件输入元素旁显示已选择的文件数量
                const fileCount = document.createElement('div');
                fileCount.className = 'selected-files-info mt-2';
                fileCount.innerHTML = `
                    <div class="d-flex align-items-center text-primary">
                        <i class="material-icons-round me-1" style="font-size: 1rem; vertical-align: -3px;">check_circle</i>
                        已选择 <strong>${this.files.length}</strong> 个文件
                    </div>
                `;
                
                // 移除之前的提示
                const prevInfo = document.querySelector('.selected-files-info');
                if (prevInfo) {
                    prevInfo.remove();
                }
                
                // 添加新提示
                this.parentNode.after(fileCount);
            } else {
                // 移除文件选择提示
                this.removeAttribute('title');
                const prevInfo = document.querySelector('.selected-files-info');
                if (prevInfo) {
                    prevInfo.remove();
                }
            }
        });
    }
    
    // 设置帮助按钮点击事件
    if (fileInfoBtn) {
        fileInfoBtn.addEventListener('click', function() {
            alert('支持上传多个Excel文件(.xlsx)，系统将自动提取其中的交易数据并进行解析。\n\n请确保Excel文件中包含必要的列，如交易日期、交易金额、交易类型等信息。');
        });
    }
}); 