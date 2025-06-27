/**
 * 设置页面入口脚本
 */

import { UploadFeature, DatabaseFeature } from '../pages/settings.js';

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    new UploadFeature('file-uploader');
    new DatabaseFeature();
}); 