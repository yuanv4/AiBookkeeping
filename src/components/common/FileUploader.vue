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
      <div class="upload-icon"><CloudUploadOutlined /></div>
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
          <span class="file-icon">
            <AlipayCircleOutlined v-if="isAlipayFile(file)" />
            <WechatOutlined v-else-if="isWechatFile(file)" />
            <BankOutlined v-else-if="isBankFile(file)" />
            <FileTextOutlined v-else />
          </span>
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
import { ref, computed, h } from 'vue'
import { useAppStore } from '../../stores/appStore.js'
import {
  CloudUploadOutlined,
  FileTextOutlined,
  AlipayCircleOutlined,
  WechatOutlined,
  BankOutlined
} from '@ant-design/icons-vue'

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

function isAlipayFile(file) {
  if (!file) return false
  const name = (file.name || '').toLowerCase()
  return name.includes('支付宝') || file.platform === 'alipay'
}

function isWechatFile(file) {
  if (!file) return false
  const name = (file.name || '').toLowerCase()
  return name.includes('微信') || file.platform === 'wechat'
}

function isBankFile(file) {
  if (!file) return false
  return file.platform?.includes('ccb') || file.platform?.includes('cmb')
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
  border: 2px dashed var(--border-default);
  border-radius: var(--radius-lg);
  padding: 40px 20px;
  text-align: center;
  cursor: pointer;
  transition: all var(--duration-base) ease;
  background: var(--color-gray-50);
  position: relative;
}

.upload-area:hover {
  border-color: var(--border-strong);
  background: var(--color-gray-100);
}

.upload-area.dragging {
  border-color: var(--border-strong);
  background: var(--color-gray-100);
}

.upload-icon {
  font-size: 48px;
  margin-bottom: 15px;
}

.upload-text {
  font-size: 16px;
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.upload-hint {
  font-size: 13px;
  color: var(--text-secondary);
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
  background: var(--bg-card);
  border: var(--card-border);
  border-radius: var(--radius-md);
  transition: border-color var(--duration-base) ease;
}

.file-item:hover {
  border-color: var(--border-strong);
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
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-meta {
  font-size: 12px;
  color: var(--text-secondary);
}

.btn-sm {
  padding: 6px 12px;
  font-size: 13px;
}

.btn-danger {
  background: var(--color-danger);
  color: white;
  border: none;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: opacity var(--duration-base) ease;
}

.btn-danger:hover {
  opacity: 0.9;
}
</style>
