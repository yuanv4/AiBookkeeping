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
            processingContainer: document.getElementById(`${this.baseId}-processing`),
            processingStage: document.getElementById(`${this.baseId}-processing-stage`),
            processingFileInfo: document.getElementById(`${this.baseId}-processing-file-info`),
            processingTimeEstimate: document.getElementById(`${this.baseId}-processing-time-estimate`),
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

        this.showProcessingIndicator();

        // 创建FormData
        const formData = new FormData();
        this.selectedFiles.forEach(file => {
            formData.append('file', file);
        });

        // 设置超时处理
        const timeoutId = setTimeout(() => {
            this.handleProcessingTimeout();
        }, 30000); // 30秒超时

        try {
            // 启动阶段模拟和实际请求
            const stagePromise = this.simulateProcessingStages();
            const uploadPromise = apiService.post('/settings/upload', formData, { showLoading: false });

            // 等待两者都完成
            const [_, result] = await Promise.all([stagePromise, uploadPromise]);

            // 清除超时
            clearTimeout(timeoutId);

            if (result.success) {
                // 显示成功动画
                this.showSuccessAnimation();
                this.updateProcessingStage('save', '处理完成！', '文件处理成功，正在重置界面...');

                // 显示处理结果通知
                if (result.data && result.data.total_records) {
                    showNotification(`成功处理 ${result.data.total_records} 条交易记录`, 'success');
                }

                setTimeout(() => this.resetUploadState(), 2000);
            } else {
                this.updateProcessingStage('error', '处理失败', result.error || '未知错误');
                setTimeout(() => {
                    this.hideProcessingIndicator();
                }, 3000);
            }

        } catch (error) {
            clearTimeout(timeoutId);
            this.updateProcessingStage('error', '上传失败', `错误: ${error.message}`);
            setTimeout(() => {
                this.hideProcessingIndicator();
            }, 3000);
        }
    }

    handleProcessingTimeout() {
        this.updateProcessingStage('error', '处理超时', '文件处理时间过长，请稍后重试');
        setTimeout(() => {
            this.hideProcessingIndicator();
        }, 3000);
    }

    showSuccessAnimation() {
        const spinner = this.elements.processingContainer?.querySelector('.processing-spinner');
        if (spinner) {
            spinner.innerHTML = '<i class="fas fa-check-circle text-success" style="font-size: 3rem;"></i>';
        }

        // 标记所有阶段为完成
        this.updateStageIndicator('completed');
    }
    

    
    updateProcessingStage(stage, status, fileInfo = '') {
        if (!this.elements.processingContainer) return;

        // 更新阶段指示器
        this.updateStageIndicator(stage);

        // 更新状态文字
        if (this.elements.processingStage && status) {
            this.elements.processingStage.textContent = status;

            // 应用状态样式
            this.elements.processingStage.classList.remove('success', 'error');
            if (stage === 'error') {
                this.elements.processingStage.classList.add('error');
            } else if (stage === 'save' && status.includes('完成')) {
                this.elements.processingStage.classList.add('success');
            }
        }

        // 更新文件信息
        if (this.elements.processingFileInfo && fileInfo) {
            this.elements.processingFileInfo.textContent = fileInfo;
        }

        // 更新容器样式
        this.elements.processingContainer.classList.remove('success', 'error');
        if (stage === 'error') {
            this.elements.processingContainer.classList.add('error');
            const spinner = this.elements.processingContainer.querySelector('.processing-spinner');
            if (spinner) {
                spinner.innerHTML = '<i class="fas fa-exclamation-triangle text-danger" style="font-size: 3rem;"></i>';
            }
        } else if (stage === 'save' && status.includes('完成')) {
            this.elements.processingContainer.classList.add('success');
        }
    }

    updateStageIndicator(currentStage) {
        const stageOrder = ['upload', 'validate', 'extract', 'save'];
        const stageDots = this.elements.processingContainer?.querySelectorAll('.stage-dot');
        if (!stageDots) return;

        // 特殊处理：全部完成
        if (currentStage === 'completed') {
            stageDots.forEach(dot => {
                dot.classList.remove('active');
                dot.classList.add('completed');
            });
            return;
        }

        const currentIndex = stageOrder.indexOf(currentStage);
        if (currentIndex === -1) return;

        stageDots.forEach((dot, index) => {
            dot.classList.remove('active', 'completed');
            if (index < currentIndex) {
                dot.classList.add('completed');
            } else if (index === currentIndex) {
                dot.classList.add('active');
            }
        });
    }

    estimateProcessingTime(totalSize) {
        const baseSizeKB = totalSize / 1024;
        if (baseSizeKB < 100) return "约 1-2 秒";
        if (baseSizeKB < 500) return "约 2-5 秒";
        if (baseSizeKB < 2000) return "约 5-15 秒";
        return "约 15-30 秒";
    }

    simulateProcessingStages() {
        return new Promise((resolve) => {
            const stages = [
                { stage: 'upload', message: '正在上传文件...', delay: 500 },
                { stage: 'validate', message: '正在验证文件格式...', delay: 800 },
                { stage: 'extract', message: '正在提取交易数据...', delay: 1200 },
                { stage: 'save', message: '正在保存到数据库...', delay: 600 }
            ];

            let currentIndex = 0;

            const processNextStage = () => {
                if (currentIndex >= stages.length) {
                    resolve();
                    return;
                }

                const currentStage = stages[currentIndex];
                this.updateProcessingStage(currentStage.stage, currentStage.message, '');

                setTimeout(() => {
                    currentIndex++;
                    processNextStage();
                }, currentStage.delay);
            };

            processNextStage();
        });
    }
    
    showProcessingIndicator() {
        if (this.elements.dropZone) {
            this.elements.dropZone.style.display = 'none';
        }
        if (this.elements.processingContainer) {
            this.elements.processingContainer.classList.remove('d-none');
        }
        this.initProcessingIndicator();
    }

    hideProcessingIndicator() {
        if (this.elements.dropZone) {
            this.elements.dropZone.style.display = 'block';
        }
        if (this.elements.processingContainer) {
            this.elements.processingContainer.classList.add('d-none');
        }
    }
    
    initProcessingIndicator() {
        // 重置阶段指示器
        this.updateStageIndicator('upload');

        // 设置初始状态
        if (this.elements.processingStage) {
            this.elements.processingStage.textContent = '准备处理文件...';
        }

        // 显示文件信息和时间预估
        if (this.selectedFiles.length > 0) {
            const totalSize = this.selectedFiles.reduce((sum, file) => sum + file.size, 0);
            const fileNames = this.selectedFiles.map(f => f.name).join(', ');

            if (this.elements.processingFileInfo) {
                this.elements.processingFileInfo.textContent = `正在处理: ${fileNames}`;
            }

            if (this.elements.processingTimeEstimate) {
                this.elements.processingTimeEstimate.textContent = `预计用时: ${this.estimateProcessingTime(totalSize)}`;
            }
        }

        // 确保旋转加载器正常显示
        const spinner = this.elements.processingContainer?.querySelector('.processing-spinner');
        if (spinner) {
            spinner.innerHTML = `
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">处理中...</span>
                </div>
            `;
        }
    }
    
    resetUploadState() {
        this.selectedFiles = [];

        if (this.elements.fileInput) {
            this.elements.fileInput.value = '';
        }

        this.hideProcessingIndicator();
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
                this.executeDelete(deleteUrl);
            }
        }
    }
    
    async executeDelete(deleteUrl) {
        const result = await apiService.post(deleteUrl, {});

        if (result.success && result.data.success) {
            showNotification('成功：' + result.data.message, 'success');
            // 删除成功后留在当前页面，不重定向
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