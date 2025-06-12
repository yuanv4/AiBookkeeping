/**
 * 上传页面的JavaScript逻辑
 * 用于处理文件上传交互和验证
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('[DEBUG] DOM加载完成，初始化上传功能');
    
    const fileInput = document.getElementById('fileInput');
    const dropZone = document.getElementById('dropZone');
    const fileListContainer = document.getElementById('fileListContainer');
    const fileList = document.getElementById('fileList');
    const uploadBtn = document.getElementById('uploadBtn');
    const clearAllBtn = document.getElementById('clearAllBtn');
    const uploadProgressContainer = document.getElementById('uploadProgressContainer');
    const uploadContainer = document.getElementById('uploadContainer');
    
    console.log('[DEBUG] 元素获取结果:');
    console.log('  - fileInput:', fileInput ? '✓' : '✗');
    console.log('  - dropZone:', dropZone ? '✓' : '✗');
    console.log('  - fileListContainer:', fileListContainer ? '✓' : '✗');
    console.log('  - fileList:', fileList ? '✓' : '✗');
    console.log('  - uploadBtn:', uploadBtn ? '✓' : '✗');
    console.log('  - clearAllBtn:', clearAllBtn ? '✓' : '✗');
    console.log('  - uploadProgressContainer:', uploadProgressContainer ? '✓' : '✗');
    console.log('  - uploadContainer:', uploadContainer ? '✓' : '✗');
    
    let selectedFiles = [];
    
    // 文件验证配置
    const config = {
        allowedExtensions: ['.xlsx', '.xls'],
        maxFileSize: 50 * 1024 * 1024, // 50MB
        maxFiles: 10
    };
    
    // 初始化拖拽功能
    if (dropZone) {
        // 阻止默认拖拽行为
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, preventDefaults, false);
            document.body.addEventListener(eventName, preventDefaults, false);
        });
        
        // 拖拽视觉反馈
        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, highlight, false);
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, unhighlight, false);
        });
        
        // 处理文件拖放
        dropZone.addEventListener('drop', handleDrop, false);
    }
    
    // 文件输入变化处理
    if (fileInput) {
        fileInput.addEventListener('change', function() {
            handleFiles(this.files);
        });
    }
    
    // 上传按钮点击处理
    if (uploadBtn) {
        uploadBtn.addEventListener('click', function() {
            console.log('[DEBUG] 上传按钮事件触发');
            if (selectedFiles.length > 0) {
                handleUploadClick();
            } else {
                console.log('[DEBUG] 没有选中文件，不执行上传');
            }
        });
    }
    
    // 清空全部按钮处理
    if (clearAllBtn) {
        clearAllBtn.addEventListener('click', function() {
            clearAllFiles();
        });
    }
    
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    function highlight(e) {
        dropZone.classList.add('drag-over');
    }
    
    function unhighlight(e) {
        dropZone.classList.remove('drag-over');
    }
    
    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        handleFiles(files);
    }
    
    function handleFiles(files) {
        const validFiles = [];
        const errors = [];
        
        // 检查文件数量限制
        if (selectedFiles.length + files.length > config.maxFiles) {
            showError(`最多只能选择 ${config.maxFiles} 个文件`);
            return;
        }
        
        // 验证每个文件
        Array.from(files).forEach(file => {
            const validation = validateFile(file);
            if (validation.valid) {
                // 检查是否已存在同名文件
                if (!selectedFiles.some(f => f.name === file.name)) {
                    validFiles.push(file);
                } else {
                    errors.push(`文件 "${file.name}" 已存在`);
                }
            } else {
                errors.push(`文件 "${file.name}": ${validation.error}`);
            }
        });
        
        // 添加有效文件
        if (validFiles.length > 0) {
            selectedFiles.push(...validFiles);
            updateFileList();
            showFileListContainer();
        }
        
        // 显示错误信息
        if (errors.length > 0) {
            showError(errors.join('\n'));
        }
    }
    
    function validateFile(file) {
        // 检查文件扩展名
        const fileName = file.name.toLowerCase();
        const hasValidExtension = config.allowedExtensions.some(ext => 
            fileName.endsWith(ext)
        );
        
        if (!hasValidExtension) {
            return {
                valid: false,
                error: `不支持的文件格式，仅支持 ${config.allowedExtensions.join(', ')} 格式`
            };
        }
        
        // 检查文件大小
        if (file.size > config.maxFileSize) {
            return {
                valid: false,
                error: `文件大小超过限制（最大 ${formatFileSize(config.maxFileSize)}）`
            };
        }
        
        // 检查文件是否为空
        if (file.size === 0) {
            return {
                valid: false,
                error: '文件为空'
            };
        }
        
        return { valid: true };
    }
    
    function updateFileList() {
        if (!fileList) return;
        
        fileList.innerHTML = '';
        
        selectedFiles.forEach((file, index) => {
            const fileItem = createFileItem(file, index);
            fileList.appendChild(fileItem);
        });
        
        // 更新上传按钮状态
        if (uploadBtn) {
            uploadBtn.disabled = selectedFiles.length === 0;
        }
    }
    
    function createFileItem(file, index) {
        const fileItem = document.createElement('div');
        fileItem.className = 'file-item d-flex align-items-center justify-content-between p-3 border rounded mb-2';
        
        fileItem.innerHTML = `
            <div class="d-flex align-items-center flex-grow-1">
                <div class="file-icon me-3">
                    <i class="bi bi-file-earmark-excel text-success" style="font-size: 1.5rem;"></i>
                </div>
                <div class="file-info flex-grow-1">
                    <div class="file-name fw-semibold">${escapeHtml(file.name)}</div>
                    <div class="file-size text-muted small">${formatFileSize(file.size)}</div>
                </div>
            </div>
            <button type="button" class="btn btn-outline-danger btn-sm" onclick="removeFile(${index})">
                <i class="bi bi-trash"></i>
            </button>
        `;
        
        return fileItem;
    }
    
    function showFileListContainer() {
        if (fileListContainer) {
            fileListContainer.style.display = 'block';
        }
    }
    
    function hideFileListContainer() {
        if (fileListContainer) {
            fileListContainer.style.display = 'none';
        }
    }
    
    function clearAllFiles() {
        selectedFiles = [];
        updateFileList();
        hideFileListContainer();
        
        // 重置文件输入
        if (fileInput) {
            fileInput.value = '';
        }
    }
    
    function handleUploadClick() {
        console.log('[DEBUG] 上传按钮被点击');
        console.log('[DEBUG] 当前选中文件数量:', selectedFiles.length);
        
        if (selectedFiles.length === 0) {
            console.log('[DEBUG] 没有选中文件，显示错误信息');
            showError('请先选择要上传的文件');
            return;
        }
        
        console.log('[DEBUG] 开始上传流程，显示进度条');
        // 显示上传进度
        showUploadProgress();
        
        // 创建FormData
        const formData = new FormData();
        selectedFiles.forEach(file => {
            formData.append('file', file);
        });
        
        // 发送请求
        console.log('[DEBUG] 开始上传文件，文件数量:', selectedFiles.length);
        console.log('[DEBUG] 上传URL: /settings/upload');
        
        fetch('/settings/upload', {
            method: 'POST',
            body: formData,
            redirect: 'manual'  // 手动处理重定向
        })
        .then(response => {
            console.log('[DEBUG] 收到响应:');
            console.log('  - 状态码:', response.status);
            console.log('  - 状态文本:', response.statusText);
            console.log('  - 响应类型:', response.type);
            console.log('  - 是否重定向:', response.redirected);
            console.log('  - URL:', response.url);
            console.log('  - Headers:', Object.fromEntries(response.headers.entries()));
            
            if (response.type === 'opaqueredirect' || (response.status >= 300 && response.status < 400)) {
                console.log('[DEBUG] 检测到重定向，跳转到dashboard');
                window.location.href = '/dashboard';
                return;
            }
            if (response.ok) {
                console.log('[DEBUG] 响应成功，读取响应内容');
                return response.text();
            } else {
                console.log('[DEBUG] 响应失败，状态码:', response.status);
                throw new Error(`上传失败: ${response.status} ${response.statusText}`);
            }
        })
        .then(data => {
            console.log('[DEBUG] 处理响应数据:');
            console.log('  - 数据类型:', typeof data);
            console.log('  - 数据长度:', data ? data.length : 'undefined');
            console.log('  - 数据内容预览:', data ? data.substring(0, 200) + '...' : 'undefined');
            
            if (data !== undefined) {
                // 如果有响应数据但不是重定向，可能是错误情况
                // 检查是否包含错误信息
                if (data.includes('alert-danger') || data.includes('错误')) {
                    console.log('[DEBUG] 检测到错误信息，解析错误内容');
                    // 解析错误信息并显示
                    const parser = new DOMParser();
                    const doc = parser.parseFromString(data, 'text/html');
                    const errorAlert = doc.querySelector('.alert-danger');
                    if (errorAlert) {
                        const errorText = errorAlert.textContent.trim();
                        console.log('[DEBUG] 提取到错误信息:', errorText);
                        hideUploadProgress();
                        showError(errorText);
                        return;
                    }
                }
                console.log('[DEBUG] 没有检测到错误，跳转到dashboard');
                // 其他情况，跳转到dashboard
                window.location.href = '/dashboard';
            } else {
                console.log('[DEBUG] 响应数据为undefined，可能是重定向已处理');
            }
        })
        .catch(error => {
            console.error('[DEBUG] 上传过程中发生错误:', error);
            console.error('  - 错误类型:', error.constructor.name);
            console.error('  - 错误消息:', error.message);
            console.error('  - 错误堆栈:', error.stack);
            hideUploadProgress();
            showError(`上传失败: ${error.message}`);
        });
    }
    
    function showUploadProgress() {
        if (uploadContainer && uploadProgressContainer) {
            uploadContainer.style.display = 'none';
            uploadProgressContainer.style.display = 'block';
        }
    }
    
    function hideUploadProgress() {
        if (uploadContainer && uploadProgressContainer) {
            uploadContainer.style.display = 'block';
            uploadProgressContainer.style.display = 'none';
        }
    }
    
    function showError(message) {
        // 创建错误提示
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-danger alert-dismissible fade show mt-3';
        alertDiv.innerHTML = `
            <strong>错误:</strong> ${escapeHtml(message).replace(/\n/g, '<br>')}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        // 插入到上传容器前面
        if (uploadContainer && uploadContainer.parentNode) {
            uploadContainer.parentNode.insertBefore(alertDiv, uploadContainer);
            
            // 5秒后自动移除
            setTimeout(() => {
                if (alertDiv.parentNode) {
                    alertDiv.parentNode.removeChild(alertDiv);
                }
            }, 5000);
        }
    }
    
    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    function escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, function(m) { return map[m]; });
    }
    
    // 全局函数，供HTML调用
    window.removeFile = function(index) {
        selectedFiles.splice(index, 1);
        updateFileList();
        
        if (selectedFiles.length === 0) {
            hideFileListContainer();
        }
    };
});