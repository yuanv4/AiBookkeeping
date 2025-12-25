import { defineStore } from 'pinia'

export const useNotificationStore = defineStore('notification', {
  state: () => ({
    notifications: []
  }),

  actions: {
    show(message, type = 'info', duration = 3000) {
      const id = Date.now()
      this.notifications.push({ id, message, type })
      if (duration > 0) {
        setTimeout(() => this.remove(id), duration)
      }
      return id
    },

    remove(id) {
      const index = this.notifications.findIndex(n => n.id === id)
      if (index > -1) this.notifications.splice(index, 1)
    }
  }
})
