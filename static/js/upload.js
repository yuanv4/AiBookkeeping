// upload.js - 处理文件上传页面的交互逻辑

document.addEventListener('DOMContentLoaded', function() {
    // 文件上传时的样式效果
    const fileInput = document.getElementById('file');
    const fileInfoBtn = document.getElementById('file-info-btn');
    
    if (fileInput) {
        fileInput.addEventListener('change', function() {
            if (this.files.length > 0) {
                let fileNames = Array.from(this.files).map(file => file.name).join(', ');
                this.setAttribute('title', fileNames);
            } else {
                this.removeAttribute('title');
            }
        });
    }
    
    if (fileInfoBtn) {
        fileInfoBtn.addEventListener('click', function() {
            alert('支持上传多个Excel文件(.xlsx)，系统将自动提取其中的交易数据并进行解析。\n\n请确保Excel文件中包含必要的列，如交易日期、交易金额、交易类型等信息。');
        });
    }
}); 