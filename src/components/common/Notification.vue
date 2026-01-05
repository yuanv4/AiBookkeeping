<template>
  <Teleport to="body">
    <div class="notification-container">
      <TransitionGroup name="notification">
        <div
          v-for="notif in notificationStore.notifications"
          :key="notif.id"
          :class="['notification', `notification-${notif.type}`]"
        >
          <span class="notification-icon">
            <CheckCircleOutlined v-if="notif.type === 'success'" />
            <CloseCircleOutlined v-else-if="notif.type === 'error'" />
            <ExclamationCircleOutlined v-else-if="notif.type === 'warning'" />
            <InfoCircleOutlined v-else />
          </span>
          <span class="notification-message">{{ notif.message }}</span>
          <button @click="notificationStore.remove(notif.id)" class="notification-close">
            <CloseOutlined />
          </button>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<script setup>
import { useNotificationStore } from '../../stores/notificationStore.js'
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  ExclamationCircleOutlined,
  InfoCircleOutlined,
  CloseOutlined
} from '@ant-design/icons-vue'

const notificationStore = useNotificationStore()
</script>

<style scoped>
.notification-container {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-width: 400px;
}

.notification {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  background: white;
  animation: slideIn 0.3s ease-out;
}

.notification-icon {
  font-size: 20px;
  flex-shrink: 0;
}

.notification-message {
  flex: 1;
  font-size: 14px;
  color: #333;
}

.notification-close {
  background: none;
  border: none;
  font-size: 24px;
  color: #999;
  cursor: pointer;
  padding: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: all 0.2s;
}

.notification-close:hover {
  background: #f0f0f0;
  color: #333;
}

.notification-success {
  border-left: 4px solid #52c41a;
}

.notification-error {
  border-left: 4px solid #ff4d4f;
}

.notification-warning {
  border-left: 4px solid #faad14;
}

.notification-info {
  border-left: 4px solid #1890ff;
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

.notification-enter-active,
.notification-leave-active {
  transition: all 0.3s ease;
}

.notification-enter-from {
  opacity: 0;
  transform: translateX(100%);
}

.notification-leave-to {
  opacity: 0;
  transform: translateX(100%);
}
</style>
