<template>
  <div class="file-uploader">
    <div
      class="upload-area"
      :class="{ dragging }"
      @dragover.prevent="dragging = true"
      @dragleave.prevent="dragging = false"
      @drop.prevent="handleDrop"
      @click="triggerFileInput"
    >
      <div class="upload-icon">📁</div>
      <div class="upload-text">{{ uploadText }}</div>
      <div class="upload-hint">{{ uploadHint }}</div>
      <input
        ref="fileInput"
        type="file"
        :multiple="multiple"
        :accept="accept"
        @change="handleFileSelect"
        class="file-input"
      />
    </div>

    <!-- 文件列表 -->
    <div v-if="showFileList && files.length > 0" class="file-list">
      <div v-for="file in files" :key="file.id" class="file-item">
        <div class="file-info">
          <span class="file-icon">{{ getFileIcon(file) }}</span>
          <div class="file-details">
            <span class="file-name">{{ file.name }}</span>
            <span class="file-meta">{{ formatFileSize(file.size) }} · {{ file.platform || '未识别' }}</span>
          </div>
        </div>
        <button class="btn btn-danger btn-sm" @click.stop="removeFile(file.id)">删除</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useAppStore } from '../../stores/appStore.js'

const props = defineProps({
  uploadText: {
    type: String,
    default: '点击或拖拽文件到此处上传'
  },
  uploadHint: {
    type: String,
    default: '支持微信账单(xlsx)、支付宝账单(csv)、银行账单(xls/pdf)'
  },
  multiple: {
    type: Boolean,
    default: true
  },
  accept: {
    type: String,
    default: '.csv,.xlsx,.xls,.pdf'
  },
  showFileList: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['files-added'])

const appStore = useAppStore()
const fileInput = ref(null)
const dragging = ref(false)

const files = computed(() => appStore.files)

function triggerFileInput() {
  fileInput.value?.click()
}

function handleFileSelect(event) {
  const selectedFiles = Array.from(event.target.files || [])
  addFiles(selectedFiles)
  event.target.value = ''
}

function handleDrop(event) {
  dragging.value = false
  const droppedFiles = Array.from(event.dataTransfer?.files || [])
  addFiles(droppedFiles)
}

function addFiles(newFiles) {
  appStore.addFiles(newFiles)
  emit('files-added', newFiles)
}

function removeFile(id) {
  appStore.removeFile(id)
}

function getFileIcon(file) {
  if (!file || !file.name) return '📄'
  const name = file.name.toLowerCase()
  if (name.includes('支付宝') || file.platform === 'alipay') return '💙'
  if (name.includes('微信') || file.platform === 'wechat') return '💚'
  if (file.platform?.includes('ccb') || file.platform?.includes('cmb')) return '🏦'
  return '📄'
}

function formatFileSize(bytes) {
  if (bytes === undefined || bytes === null) return '0 B'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}
</script>

<style scoped>
.file-uploader {
  width: 100%;
}

.upload-area {
  border: 2px dashed #d1d5db;
  border-radius: 12px;
  padding: 40px 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  background: #f9fafb;
  position: relative;
}

.upload-area:hover {
  border-color: #667eea;
  background: #f3f4f6;
}

.upload-area.dragging {
  border-color: #667eea;
  background: rgba(102, 126, 234, 0.05);
}

.upload-icon {
  font-size: 48px;
  margin-bottom: 15px;
}

.upload-text {
  font-size: 16px;
  font-weight: 500;
  color: #1f2937;
  margin-bottom: 8px;
}

.upload-hint {
  font-size: 13px;
  color: #6b7280;
}

.file-input {
  display: none;
}

.file-list {
  margin-top: 20px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.file-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 15px;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  transition: all 0.2s ease;
}

.file-item:hover {
  border-color: #667eea;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.1);
}

.file-info {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
  min-width: 0;
}

.file-icon {
  font-size: 24px;
  flex-shrink: 0;
}

.file-details {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
  flex: 1;
}

.file-name {
  font-size: 14px;
  font-weight: 500;
  color: #1f2937;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-meta {
  font-size: 12px;
  color: #6b7280;
}

.btn-sm {
  padding: 6px 12px;
  font-size: 13px;
}

.btn-danger {
  background: #ef4444;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.2s ease;
}

.btn-danger:hover {
  background: #dc2626;
}
</style>
