/**
 * 设置页面的JavaScript逻辑
 * 使用现代化的类结构重构文件上传和数据库管理功能
 */

import { showNotification, formatFileSize, apiService, ui } from '../common/utils.js';

/**
 * 文件上传功能类
 */
export class UploadFeature {
    constructor(baseId = 'file-uploader') {
        this.baseId = baseId;
        this.selectedFiles = [];
        this.config = {
            allowedExtensions: ['.xlsx', '.xls'],
            maxFileSize: 50 * 1024 * 1024, // 50MB
            maxFiles: 10
        };
        
        this.elements = {};
        this.init();
    }
    
    init() {
        this.bindElements();
        if (!this.elements.fileInput && !this.elements.dropZone) {
            return; // 不在上传页面
        }
        
        this.setupEventListeners();
    }
    
    bindElements() {
        this.elements = {
            fileInput: document.getElementById(`${this.baseId}-input`),
            dropZone: document.getElementById(`${this.baseId}-drop-zone`),
            uploadProgressContainer: document.getElementById(`${this.baseId}-progress`),
            progressBar: document.getElementById(`${this.baseId}-progress-bar`),
            progressText: document.getElementById(`${this.baseId}-progress-text`),
            statusText: document.getElementById(`${this.baseId}-status-text`),
            fileInfo: document.getElementById(`${this.baseId}-file-info`),
            timeEstimate: document.getElementById(`${this.baseId}-time-estimate`),
            selectButton: document.querySelector(`[data-file-input="${this.baseId}-input"]`)
        };
    }
    
    setupEventListeners() {
        // 拖拽功能
        if (this.elements.dropZone) {
            ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
                this.elements.dropZone.addEventListener(eventName, this.preventDefaults, false);
                document.body.addEventListener(eventName, this.preventDefaults, false);
            });
            
            ['dragenter', 'dragover'].forEach(eventName => {
                this.elements.dropZone.addEventListener(eventName, () => {
                    this.elements.dropZone.classList.add('drag-over');
                }, false);
            });
            
            ['dragleave', 'drop'].forEach(eventName => {
                this.elements.dropZone.addEventListener(eventName, () => {
                    this.elements.dropZone.classList.remove('drag-over');
                }, false);
            });
            
            this.elements.dropZone.addEventListener('drop', (e) => {
                const files = e.dataTransfer.files;
                this.handleFiles(files);
            }, false);
            
            // 点击拖拽区域触发文件选择
            this.elements.dropZone.addEventListener('click', () => {
                if (this.elements.fileInput) {
                    this.elements.fileInput.click();
                }
            });
        }
        
        // 文件输入
        if (this.elements.fileInput) {
            this.elements.fileInput.addEventListener('change', (e) => {
                this.handleFiles(e.target.files);
            });
        }
        
        // 选择文件按钮
        if (this.elements.selectButton) {
            this.elements.selectButton.addEventListener('click', (e) => {
                e.stopPropagation(); // 防止冒泡到dropZone
                if (this.elements.fileInput) {
                    this.elements.fileInput.click();
                }
            });
        }
    }
    
    preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    handleFiles(files) {
        const validFiles = [];
        const errors = [];
        
        // 检查文件数量限制
        if (this.selectedFiles.length + files.length > this.config.maxFiles) {
            showNotification(`最多只能选择 ${this.config.maxFiles} 个文件`, 'error');
            return;
        }
        
        // 验证每个文件
        Array.from(files).forEach(file => {
            const validation = this.validateFile(file);
            if (validation.valid) {
                if (!this.selectedFiles.some(f => f.name === file.name)) {
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
            showNotification(errors.join('\n'), 'error');
        }
        
        // 添加有效文件并立即开始上传
        if (validFiles.length > 0) {
            this.selectedFiles = validFiles;
            this.startUpload();
        }
    }
    
    validateFile(file) {
        const fileName = file.name.toLowerCase();
        const hasValidExtension = this.config.allowedExtensions.some(ext => 
            fileName.endsWith(ext)
        );
        
        if (!hasValidExtension) {
            return {
                valid: false,
                error: `不支持的文件格式，仅支持 ${this.config.allowedExtensions.join(', ')} 格式`
            };
        }
        
        if (file.size > this.config.maxFileSize) {
            return {
                valid: false,
                error: `文件大小超过限制（最大 ${formatFileSize(this.config.maxFileSize)}）`
            };
        }
        
        if (file.size === 0) {
            return {
                valid: false,
                error: '文件为空'
            };
        }
        
        return { valid: true };
    }
    
    async startUpload() {
        if (this.selectedFiles.length === 0) {
            showNotification('请先选择要上传的文件', 'error');
            return;
        }
        
        this.showUploadProgress();
        
        // 创建FormData
        const formData = new FormData();
        this.selectedFiles.forEach(file => {
            formData.append('file', file);
        });
        
        // 启动进度模拟
        const progressPromise = this.simulateProgress();
        
        try {
            // 等待进度模拟完成后发送请求
            await progressPromise;
            
            const result = await apiService.post('/settings/upload', formData, { showLoading: false });
            
            if (result.success) {
                this.updateProgress(100, '处理完成！', '文件处理成功，正在重置界面...', 'completing');
                setTimeout(() => this.resetUploadState(), 1000);
            } else {
                this.updateProgress(100, '处理失败', result.error, 'error');
                setTimeout(() => {
                    this.hideUploadProgress();
                }, 2000);
            }
            
        } catch (error) {
            this.updateProgress(100, '上传失败', `错误: ${error.message}`, 'error');
            setTimeout(() => {
                this.hideUploadProgress();
            }, 2000);
        }
    }
    
    simulateProgress() {
        return new Promise((resolve) => {
            const totalSteps = 90;
            let currentStep = 0;
            
            const stages = [
                { name: '文件上传中...', progress: 25, stage: 'uploading' },
                { name: '格式验证中...', progress: 50, stage: 'validating' },
                { name: '数据提取中...', progress: 85, stage: 'processing' },
                { name: '保存数据中...', progress: 90, stage: 'completing' }
            ];
            
            let stageIndex = 0;
            
            const interval = setInterval(() => {
                currentStep++;
                const currentStage = stages[stageIndex];
                
                if (currentStep >= currentStage.progress && stageIndex < stages.length - 1) {
                    stageIndex++;
                }
                
                const fileInfo = this.selectedFiles.length > 0 ? 
                    `正在处理: ${this.selectedFiles[0].name}` : '';
                
                this.updateProgress(
                    currentStep, 
                    stages[stageIndex].name, 
                    fileInfo, 
                    stages[stageIndex].stage
                );
                
                if (currentStep >= totalSteps) {
                    clearInterval(interval);
                    resolve();
                }
            }, 100);
        });
    }
    
    updateProgress(percentage, status, fileInfo = '', stage = '') {
        if (!this.elements.progressBar) return;
        
        this.elements.progressBar.style.width = `${percentage}%`;
        this.elements.progressBar.setAttribute('aria-valuenow', percentage);
        
        if (this.elements.progressText) {
            this.elements.progressText.textContent = `${Math.round(percentage)}%`;
        }
        
        if (this.elements.statusText && status) {
            const iconClass = {
                'uploading': 'fas fa-upload',
                'validating': 'fas fa-check-circle',
                'processing': 'fas fa-cogs',
                'completing': 'fas fa-save',
                'error': 'fas fa-exclamation-triangle'
            }[stage] || 'fas fa-spinner fa-spin';
            
            this.elements.statusText.innerHTML = `<i class="${iconClass} me-2"></i>${status}`;
        }
        
        if (this.elements.fileInfo && fileInfo) {
            this.elements.fileInfo.textContent = fileInfo;
        }
        
        // 更新进度条样式
        this.elements.progressBar.classList.remove('uploading', 'validating', 'processing', 'completing', 'error');
        if (stage) {
            this.elements.progressBar.classList.add(stage);
        }
    }
    
    showUploadProgress() {
        if (this.elements.dropZone) {
            this.elements.dropZone.style.display = 'none';
        }
        if (this.elements.uploadProgressContainer) {
            this.elements.uploadProgressContainer.classList.remove('d-none');
        }
        this.initProgressBar();
    }
    
    hideUploadProgress() {
        if (this.elements.dropZone) {
            this.elements.dropZone.style.display = 'block';
        }
        if (this.elements.uploadProgressContainer) {
            this.elements.uploadProgressContainer.classList.add('d-none');
        }
    }
    
    initProgressBar() {
        if (!this.elements.progressBar) return;
        
        this.elements.progressBar.style.width = '0%';
        this.elements.progressBar.setAttribute('aria-valuenow', '0');
        
        if (this.elements.progressText) {
            this.elements.progressText.textContent = '0%';
        }
        
        this.elements.progressBar.classList.remove('uploading', 'validating', 'processing', 'completing', 'error');
        
        if (this.elements.statusText) {
            this.elements.statusText.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>准备上传...';
        }
        
        if (this.elements.fileInfo) {
            this.elements.fileInfo.textContent = '';
        }
        
        if (this.elements.timeEstimate) {
            this.elements.timeEstimate.textContent = '';
        }
    }
    
    resetUploadState() {
        this.selectedFiles = [];
        
        if (this.elements.fileInput) {
            this.elements.fileInput.value = '';
        }
        
        this.hideUploadProgress();
    }
    
    clearAllFiles() {
        this.selectedFiles = [];
        
        if (this.elements.fileInput) {
            this.elements.fileInput.value = '';
        }
    }
}

/**
 * 数据库管理功能类
 */
export class DatabaseFeature {
    constructor() {
        this.init();
    }
    
    init() {
        this.bindElements();
        this.setupEventListeners();
    }
    
    bindElements() {
        this.deleteBtn = document.querySelector('[data-delete-url]');
    }
    
    setupEventListeners() {
        if (this.deleteBtn) {
            this.deleteBtn.addEventListener('click', (e) => {
                this.confirmDeleteDatabase(e);
            });
        }
    }
    
    async confirmDeleteDatabase(event) {
        const button = event.target.closest('button');
        const deleteUrl = button.dataset.deleteUrl;
        const dashboardUrl = button.dataset.dashboardUrl;
        
        // 使用统一的确认对话框
        const confirmed = await ui.showConfirmationModal({
            title: '危险操作警告',
            text: '此操作将删除所有交易数据和分析结果，且无法恢复！您确定要继续吗？',
            icon: 'warning',
            confirmButtonText: '确定删除',
            cancelButtonText: '取消'
        });
        
        if (confirmed) {
            // 第二次确认
            const finalConfirmed = await ui.showConfirmationModal({
                title: '最后确认',
                text: '您真的要删除所有数据吗？此操作不可逆！',
                icon: 'error',
                confirmButtonText: '确认删除',
                cancelButtonText: '取消'
            });
            
            if (finalConfirmed) {
                this.executeDelete(deleteUrl, dashboardUrl);
            }
        }
    }
    
    async executeDelete(deleteUrl, dashboardUrl) {
        const result = await apiService.post(deleteUrl, {});
        
        if (result.success && result.data.success) {
            showNotification('成功：' + result.data.message, 'success');
            setTimeout(() => {
                window.location.href = dashboardUrl;
            }, 1500);
        } else {
            const errorMessage = result.data?.message || result.error || '删除操作失败';
            showNotification('错误：' + errorMessage, 'error');
        }
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    new UploadFeature('file-uploader');
    new DatabaseFeature();
});