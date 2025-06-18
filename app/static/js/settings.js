/**
 * 设置页面的JavaScript逻辑
 * 包含文件上传和数据库删除功能
 */

// 全局变量，供所有函数访问
let selectedFiles = [];
let uploadContainer = null;
let uploadProgressContainer = null;
let fileInput = null;
let dropZone = null;
let fileListContainer = null;
let fileList = null;
let clearBtn = null;

document.addEventListener('DOMContentLoaded', function() {
    console.log('[SETTINGS] DOM加载完成，初始化设置页面功能');
    
    // 初始化所有功能模块
    initUploadFeature();
    initDatabaseDeleteFeature();
});

/**
 * 初始化文件上传功能
 */
function initUploadFeature() {
    console.log('[UPLOAD] 初始化文件上传功能');
    
    // 获取DOM元素并赋值给全局变量
    fileInput = document.getElementById('fileInput');
    dropZone = document.getElementById('dropZone');
    fileListContainer = document.getElementById('fileListContainer');
    fileList = document.getElementById('fileList');
    clearBtn = document.getElementById('clearBtn');
    uploadProgressContainer = document.getElementById('uploadProgress');
    uploadContainer = document.getElementById('uploadContainer');
    
    console.log('[UPLOAD] 元素获取结果:');
    console.log('  - fileInput:', fileInput ? '✓' : '✗');
    console.log('  - dropZone:', dropZone ? '✓' : '✗');
    console.log('  - fileListContainer:', fileListContainer ? '✓' : '✗');
    console.log('  - fileList:', fileList ? '✓' : '✗');
    console.log('  - clearBtn:', clearBtn ? '✓' : '✗');
    console.log('  - uploadProgressContainer:', uploadProgressContainer ? '✓' : '✗');
    console.log('  - uploadContainer:', uploadContainer ? '✓' : '✗');
    
    // 如果没有找到上传相关元素，说明不在上传页面，直接返回
    if (!fileInput && !dropZone) {
        console.log('[UPLOAD] 未找到上传相关元素，跳过上传功能初始化');
        return;
    }
    
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
    
    // 清空全部按钮处理
    if (clearBtn) {
        clearBtn.addEventListener('click', function() {
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
            showUploadError(`最多只能选择 ${config.maxFiles} 个文件`);
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
        
        // 显示错误信息
        if (errors.length > 0) {
            showUploadError(errors.join('\n'));
        }
        
        // 添加有效文件并立即开始上传
        if (validFiles.length > 0) {
            selectedFiles = validFiles; // 直接替换为当前选择的文件
            console.log('[UPLOAD] 文件验证通过，立即开始上传');
            handleUploadClick();
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
        
        // 重置文件输入
        if (fileInput) {
            fileInput.value = '';
        }
    }
    
    /**
     * 重置上传状态，恢复到初始界面
     */
    function resetUploadState() {
        console.log('[UPLOAD] 重置上传状态');
        
        // 重置文件数组
        selectedFiles = [];
        
        // 清空文件输入
        if (fileInput) {
            fileInput.value = '';
        }
        
        // 隐藏进度条，显示上传界面
        hideUploadProgress();
        
        console.log('[UPLOAD] 上传状态重置完成');
    }
    
    function handleUploadClick() {
        console.log('[UPLOAD] 开始即时上传流程');
        console.log('[UPLOAD] 当前选中文件数量:', selectedFiles.length);
        
        if (selectedFiles.length === 0) {
            console.log('[UPLOAD] 没有选中文件，显示错误信息');
            showUploadError('请先选择要上传的文件');
            return;
        }
        
        console.log('[UPLOAD] 开始上传流程，显示进度条');
        // 显示上传进度
        showUploadProgress();
        
        // 创建FormData
        const formData = new FormData();
        selectedFiles.forEach(file => {
            formData.append('file', file);
        });
        
        // 启动进度模拟
        const progressPromise = simulateProcessingStages(selectedFiles);
        
        // 发送请求
        console.log('[UPLOAD] 开始上传文件，文件数量:', selectedFiles.length);
        console.log('[UPLOAD] 上传URL: /settings/upload');
        
        // 等待进度模拟完成后再发送实际请求
        progressPromise.then(() => {
            console.log('[UPLOAD] 进度模拟完成，发送实际请求');
            
            fetch('/settings/upload', {
                method: 'POST',
                body: formData,
                redirect: 'manual'  // 手动处理重定向
            })
            .then(response => {
                console.log('[UPLOAD] 收到响应:');
                console.log('  - 状态码:', response.status);
                console.log('  - 状态文本:', response.statusText);
                console.log('  - 响应类型:', response.type);
                console.log('  - 是否重定向:', response.redirected);
                console.log('  - URL:', response.url);
                console.log('  - Headers:', Object.fromEntries(response.headers.entries()));
                
                // 更新进度到100%
                updateProgress(100, '处理完成！', '文件处理成功，正在重置界面...', '', 'completing');
                
                if (response.type === 'opaqueredirect' || (response.status >= 300 && response.status < 400)) {
                    console.log('[UPLOAD] 检测到重定向，重置上传状态');
                    setTimeout(() => {
                        resetUploadState();
                    }, 1000);
                    return;
                }
                if (response.ok) {
                    console.log('[UPLOAD] 响应成功，读取响应内容');
                    return response.text();
                } else {
                    console.log('[UPLOAD] 响应失败，状态码:', response.status);
                    throw new Error(`上传失败: ${response.status} ${response.statusText}`);
                }
            })
            .then(data => {
                console.log('[UPLOAD] 处理响应数据:');
                console.log('  - 数据类型:', typeof data);
                console.log('  - 数据长度:', data ? data.length : 'undefined');
                console.log('  - 数据内容预览:', data ? data.substring(0, 200) + '...' : 'undefined');
                
                if (data !== undefined) {
                    // 如果有响应数据但不是重定向，可能是错误情况
                    // 检查是否包含错误信息
                    if (data.includes('alert-danger') || data.includes('错误')) {
                        console.log('[UPLOAD] 检测到错误信息，解析错误内容');
                        // 解析错误信息并显示
                        const parser = new DOMParser();
                        const doc = parser.parseFromString(data, 'text/html');
                        const errorAlert = doc.querySelector('.alert-danger');
                        if (errorAlert) {
                            console.log('[UPLOAD] 提取到错误信息:', errorAlert.textContent.trim());
                            updateProgress(100, '处理失败', errorAlert.textContent.trim(), '', 'error');
                            setTimeout(() => {
                                hideUploadProgress();
                                showUploadError(errorAlert.textContent.trim());
                            }, 2000);
                            return;
                        }
                    }
                    console.log('[UPLOAD] 没有检测到错误，重置上传状态');
                    // 其他情况，重置上传状态
                    setTimeout(() => {
                        resetUploadState();
                    }, 1000);
                } else {
                    console.log('[UPLOAD] 响应数据为undefined，重置上传状态');
                    setTimeout(() => {
                        resetUploadState();
                    }, 1000);
                }
            })
            .catch(error => {
                console.error('[UPLOAD] 上传过程中发生错误:', error);
                console.error('  - 错误类型:', error.constructor.name);
                console.error('  - 错误消息:', error.message);
                console.error('  - 错误堆栈:', error.stack);
                
                // 更新进度条显示错误状态
                updateProgress(100, '上传失败', `错误: ${error.message}`, '', 'error');
                
                setTimeout(() => {
                    hideUploadProgress();
                    showUploadError(`上传失败: ${error.message}`);
                }, 2000);
            });
        }).catch(error => {
            console.error('[PROGRESS] 进度模拟过程中发生错误:', error);
            hideUploadProgress();
            showUploadError('进度显示错误，请重试');
        });
    }
    
    /**
     * 初始化进度条组件
     */
    function initProgressBar() {
        console.log('[PROGRESS] 初始化进度条组件');
        
        const progressBar = document.getElementById('progressBar');
        const progressText = document.getElementById('progressText');
        const statusText = document.getElementById('statusText');
        const fileInfo = document.getElementById('fileInfo');
        const timeEstimate = document.getElementById('timeEstimate');
        
        // 检查进度条元素是否存在
        if (!progressBar || !progressText || !statusText || !fileInfo || !timeEstimate) {
            console.warn('[PROGRESS] 进度条元素未找到，跳过初始化');
            return false;
        }
        
        // 重置进度条状态
        progressBar.style.width = '0%';
        progressBar.setAttribute('aria-valuenow', '0');
        progressText.textContent = '0%';
        
        // 移除所有状态类
        progressBar.classList.remove('uploading', 'validating', 'processing', 'completing', 'error');
        
        // 重置状态文字
        statusText.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>准备上传...';
        
        // 清空文件信息和时间估算
        fileInfo.textContent = '';
        timeEstimate.textContent = '';
        
        console.log('[PROGRESS] 进度条组件初始化完成');
        return true;
    }
    
    /**
     * 更新进度条和状态信息
     * @param {number} percentage - 进度百分比 (0-100)
     * @param {string} status - 状态文字
     * @param {string} fileInfo - 文件信息
     * @param {string} timeEstimate - 时间估算
     * @param {string} stage - 处理阶段 (uploading, validating, processing, completing, error)
     */
    function updateProgress(percentage, status, fileInfo = '', timeEstimate = '', stage = '') {
        console.log(`[PROGRESS] 更新进度: ${percentage}%, 状态: ${status}, 阶段: ${stage}`);
        
        const progressBar = document.getElementById('progressBar');
        const progressText = document.getElementById('progressText');
        const statusText = document.getElementById('statusText');
        const fileInfoElement = document.getElementById('fileInfo');
        const timeEstimateElement = document.getElementById('timeEstimate');
        
        // 检查元素是否存在
        if (!progressBar || !progressText || !statusText) {
            console.warn('[PROGRESS] 进度条元素未找到，无法更新进度');
            return;
        }
        
        // 更新进度条
        progressBar.style.width = `${percentage}%`;
        progressBar.setAttribute('aria-valuenow', percentage);
        progressText.textContent = `${Math.round(percentage)}%`;
        
        // 更新状态文字
        if (status) {
            let icon = 'fas fa-spinner fa-spin';
            
            // 根据阶段选择图标
            switch (stage) {
                case 'uploading':
                    icon = 'fas fa-upload';
                    break;
                case 'validating':
                    icon = 'fas fa-check-circle';
                    break;
                case 'processing':
                    icon = 'fas fa-cogs';
                    break;
                case 'completing':
                    icon = 'fas fa-save';
                    break;
                case 'error':
                    icon = 'fas fa-exclamation-triangle';
                    break;
                default:
                    icon = 'fas fa-spinner fa-spin';
            }
            
            statusText.innerHTML = `<i class="${icon} me-2"></i>${status}`;
        }
        
        // 更新文件信息
        if (fileInfoElement && fileInfo) {
            fileInfoElement.textContent = fileInfo;
        }
        
        // 更新时间估算
        if (timeEstimateElement && timeEstimate) {
            timeEstimateElement.textContent = timeEstimate;
        }
        
        // 更新进度条样式类
        progressBar.classList.remove('uploading', 'validating', 'processing', 'completing', 'error');
        if (stage) {
            progressBar.classList.add(stage);
        }
        
        console.log(`[PROGRESS] 进度更新完成: ${percentage}%`);
    }
    
    /**
     * 模拟文件处理的不同阶段
     * @param {Array} files - 文件数组
     * @returns {Promise} 处理完成的Promise
     */
    function simulateProcessingStages(files) {
        return new Promise((resolve, reject) => {
            console.log('[PROGRESS] 开始模拟处理阶段');
            
            const fileCount = files.length;
            const totalSize = files.reduce((sum, file) => sum + file.size, 0);
            
            // 计算各阶段的时间分配
            const baseTime = Math.max(1000, Math.min(5000, totalSize / 1024 / 1024 * 1000)); // 基于文件大小
            const uploadTime = baseTime * 0.3;
            const validateTime = baseTime * 0.2;
            const processTime = baseTime * 0.4;
            const completeTime = baseTime * 0.1;
            
            let currentFileIndex = 0;
            let currentStage = 'uploading';
            let currentProgress = 0;
            
            console.log(`[PROGRESS] 处理配置: ${fileCount}个文件, ${formatFileSize(totalSize)}, 预计总时间: ${Math.round(baseTime)}ms`);
            
            // 阶段1: 上传阶段 (0-25%)
            const uploadInterval = setInterval(() => {
                currentProgress += 1;
                const percentage = Math.min(25, currentProgress);
                
                const currentFile = files[currentFileIndex];
                const fileInfo = `正在上传: ${currentFile.name} (${formatFileSize(currentFile.size)})`;
                const timeEstimate = `预计剩余时间: ${Math.round((25 - percentage) * uploadTime / 25)}ms`;
                
                updateProgress(percentage, '文件上传中...', fileInfo, timeEstimate, 'uploading');
                
                if (percentage >= 25) {
                    clearInterval(uploadInterval);
                    currentStage = 'validating';
                    currentProgress = 25;
                    
                    // 阶段2: 验证阶段 (25-50%)
                    const validateInterval = setInterval(() => {
                        currentProgress += 1;
                        const percentage = Math.min(50, currentProgress);
                        
                        const fileInfo = `正在验证: ${currentFile.name} 格式`;
                        const timeEstimate = `预计剩余时间: ${Math.round((50 - percentage) * validateTime / 25)}ms`;
                        
                        updateProgress(percentage, '格式验证中...', fileInfo, timeEstimate, 'validating');
                        
                        if (percentage >= 50) {
                            clearInterval(validateInterval);
                            currentStage = 'processing';
                            currentProgress = 50;
                            
                            // 阶段3: 处理阶段 (50-85%)
                            const processInterval = setInterval(() => {
                                currentProgress += 1;
                                const percentage = Math.min(85, currentProgress);
                                
                                const fileInfo = `正在处理: ${currentFile.name} 数据提取`;
                                const timeEstimate = `预计剩余时间: ${Math.round((85 - percentage) * processTime / 35)}ms`;
                                
                                updateProgress(percentage, '数据提取中...', fileInfo, timeEstimate, 'processing');
                                
                                if (percentage >= 85) {
                                    clearInterval(processInterval);
                                    currentStage = 'completing';
                                    currentProgress = 85;
                                    
                                    // 阶段4: 完成阶段 (85-90%)
                                    const completeInterval = setInterval(() => {
                                        currentProgress += 1;
                                        const percentage = Math.min(90, currentProgress);
                                        
                                        const fileInfo = `正在保存: ${currentFile.name} 到数据库`;
                                        const timeEstimate = `预计剩余时间: ${Math.round((90 - percentage) * completeTime / 5)}ms`;
                                        
                                        updateProgress(percentage, '保存数据中...', fileInfo, timeEstimate, 'completing');
                                        
                                        if (percentage >= 90) {
                                            clearInterval(completeInterval);
                                            console.log('[PROGRESS] 模拟处理阶段完成，等待后端响应');
                                            resolve();
                                        }
                                    }, completeTime / 5);
                                }
                            }, processTime / 35);
                        }
                    }, validateTime / 25);
                }
            }, uploadTime / 25);
        });
    }
    
    /**
     * 调试函数：检查DOM元素状态
     */
    function debugElements() {
        console.log('[DEBUG] DOM元素状态检查:');
        console.log('  - uploadContainer:', uploadContainer);
        console.log('  - uploadProgressContainer:', uploadProgressContainer);
        console.log('  - uploadContainer display:', uploadContainer ? uploadContainer.style.display : 'N/A');
        console.log('  - uploadProgressContainer display:', uploadProgressContainer ? uploadProgressContainer.style.display : 'N/A');
        
        if (uploadProgressContainer) {
            const progressBar = uploadProgressContainer.querySelector('#progressBar');
            const statusText = uploadProgressContainer.querySelector('#statusText');
            const fileInfo = uploadProgressContainer.querySelector('#fileInfo');
            const timeEstimate = uploadProgressContainer.querySelector('#timeEstimate');
            
            console.log('  - progressBar:', progressBar);
            console.log('  - statusText:', statusText);
            console.log('  - fileInfo:', fileInfo);
            console.log('  - timeEstimate:', timeEstimate);
        }
    }
    
    function showUploadProgress() {
        console.log('[PROGRESS] 显示上传进度界面');
        
        // 调用调试函数
        debugElements();
        
        if (!uploadContainer) {
            console.error('[PROGRESS] uploadContainer 未找到');
            return;
        }
        
        if (!uploadProgressContainer) {
            console.error('[PROGRESS] uploadProgressContainer 未找到');
            return;
        }
        
        try {
            // 隐藏上传容器
            uploadContainer.style.display = 'none';
            console.log('[PROGRESS] 已隐藏上传容器');
            
            // 显示进度容器
            uploadProgressContainer.style.display = 'block';
            console.log('[PROGRESS] 已显示进度容器');
            
            // 初始化进度条
            if (!initProgressBar()) {
                console.warn('[PROGRESS] 进度条初始化失败，使用默认进度显示');
            } else {
                console.log('[PROGRESS] 进度条初始化成功');
            }
        } catch (error) {
            console.error('[PROGRESS] 显示进度界面时发生错误:', error);
        }
    }
    
    function hideUploadProgress() {
        if (uploadContainer && uploadProgressContainer) {
            uploadContainer.style.display = 'block';
            uploadProgressContainer.style.display = 'none';
        }
    }
    
    function showUploadError(message) {
        console.log('[ERROR] 显示上传错误:', message);
        
        // 如果进度条正在显示，先更新进度条状态
        const progressBar = document.getElementById('progressBar');
        if (progressBar && progressBar.style.display !== 'none') {
            updateProgress(100, '上传失败', `错误: ${message}`, '', 'error');
            
            // 延迟显示错误提示，让用户先看到进度条错误状态
            setTimeout(() => {
                showErrorAlert(message);
            }, 1500);
        } else {
            // 直接显示错误提示
            showErrorAlert(message);
        }
    }
    
    /**
     * 显示错误提示框
     * @param {string} message - 错误信息
     */
    function showErrorAlert(message) {
        // 创建错误提示
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-danger alert-dismissible fade show mt-3';
        alertDiv.innerHTML = `
            <div class="d-flex align-items-center">
                <i class="fas fa-exclamation-triangle me-2"></i>
                <div>
                    <strong>上传失败:</strong> ${escapeHtml(message).replace(/\n/g, '<br>')}
                </div>
            </div>
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
        
        // 隐藏进度条，显示上传界面
        hideUploadProgress();
    }
    
    // 全局函数，供HTML调用
    window.removeFile = function(index) {
        selectedFiles.splice(index, 1);
        updateFileList();
        
        if (selectedFiles.length === 0) {
            hideFileListContainer();
        }
    };
}

/**
 * 初始化数据库删除功能
 */
function initDatabaseDeleteFeature() {
    console.log('[DELETE] 初始化数据库删除功能');
    
    // 获取删除数据库按钮
    const deleteDbBtn = document.querySelector('[data-delete-url]');
    
    if (deleteDbBtn) {
        console.log('[DELETE] 找到删除数据库按钮，绑定事件监听器');
        deleteDbBtn.addEventListener('click', confirmDeleteDatabase);
    } else {
        console.log('[DELETE] 未找到删除数据库按钮');
    }
}

/**
 * 确认删除数据库函数
 * 通过双重确认来防止误操作
 */
function confirmDeleteDatabase(event) {
    console.log('[DELETE] 删除数据库按钮被点击');
    
    // 获取按钮元素和URL
    const button = event.target.closest('button');
    const deleteUrl = button.dataset.deleteUrl;
    const dashboardUrl = button.dataset.dashboardUrl;
    
    console.log('[DELETE] 删除URL:', deleteUrl);
    console.log('[DELETE] 仪表板URL:', dashboardUrl);
    
    // 第一次确认
    if (confirm('警告：此操作将删除所有交易数据和分析结果，且无法恢复！\n\n确定要继续吗？')) {
        // 第二次确认
        if (confirm('最后确认：您真的要删除所有数据吗？此操作不可逆！')) {
            console.log('[DELETE] 用户确认删除，开始发送请求');
            
            // 发送删除请求到后端
            fetch(deleteUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
            })
            .then(response => {
                console.log('[DELETE] 收到删除响应:', response.status);
                return response.json();
            })
            .then(data => {
                console.log('[DELETE] 删除响应数据:', data);
                
                if (data.success) {
                    alert('成功：' + data.message);
                    console.log('[DELETE] 删除成功，重定向到仪表板');
                    // 成功后重定向到仪表板
                    window.location.href = dashboardUrl;
                } else {
                    alert('错误：' + data.message);
                    console.error('[DELETE] 删除失败:', data.message);
                }
            })
            .catch(error => {
                console.error('[DELETE] 删除数据库时发生错误:', error);
                alert('删除数据库时发生网络错误，请检查网络连接后重试。');
            });
        } else {
            console.log('[DELETE] 用户取消了第二次确认');
        }
    } else {
        console.log('[DELETE] 用户取消了第一次确认');
    }
}

// ========== 共享工具函数 ==========

/**
 * 格式化文件大小
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * HTML转义
 */
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

// ========== 全局函数导出 ==========

// 导出函数供全局使用（如果需要）
window.confirmDeleteDatabase = confirmDeleteDatabase;