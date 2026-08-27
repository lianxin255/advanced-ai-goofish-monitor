import { ref, onMounted } from 'vue'
import * as settingsApi from '@/api/settings'
import type {
  NotificationSettings,
  NotificationSettingsUpdate,
  NotificationTestResponse,
  AiSettings,
  RotationSettings,
  BrowserSettings,
  SystemStatus
} from '@/api/settings'

export function useSettings() {
  const notificationSettings = ref<NotificationSettings>({})
  const aiSettings = ref<AiSettings>({})
  const rotationSettings = ref<RotationSettings>({})
  const browserSettings = ref<BrowserSettings>({})
  const systemStatus = ref<SystemStatus | null>(null)
  const globalBlacklistKeywords = ref<string[]>([])
  const isReady = ref(false)
  
  const isLoading = ref(false)
  const isSaving = ref(false)
  const error = ref<Error | null>(null)

  async function fetchAll() {
    isLoading.value = true
    error.value = null
    try {
      const [notif, ai, rotation, browser, status, blacklist] = await Promise.all([
        settingsApi.getNotificationSettings(),
        settingsApi.getAiSettings(),
        settingsApi.getRotationSettings(),
        settingsApi.getBrowserSettings(),
        settingsApi.getSystemStatus(),
        settingsApi.getGlobalBlacklist()
      ])
      notificationSettings.value = notif
      aiSettings.value = ai
      rotationSettings.value = rotation
      browserSettings.value = browser
      systemStatus.value = status
      globalBlacklistKeywords.value = blacklist.keywords
    } catch (e) {
      if (e instanceof Error) error.value = e
    } finally {
      isLoading.value = false
      isReady.value = true
    }
  }

  async function refreshStatus() {
    isLoading.value = true
    error.value = null
    try {
      systemStatus.value = await settingsApi.getSystemStatus()
    } catch (e) {
      if (e instanceof Error) error.value = e
      throw e
    } finally {
      isLoading.value = false
    }
  }

  async function saveNotificationSettings(payload: NotificationSettingsUpdate) {
    isSaving.value = true
    try {
      await settingsApi.updateNotificationSettings(payload)
      const [notif, status] = await Promise.all([
        settingsApi.getNotificationSettings(),
        settingsApi.getSystemStatus()
      ])
      notificationSettings.value = notif
      systemStatus.value = status
    } catch (e) {
      if (e instanceof Error) error.value = e
      throw e
    } finally {
      isSaving.value = false
    }
  }

  async function testNotification(payload: {
    channel?: string
    settings: NotificationSettingsUpdate
  }): Promise<NotificationTestResponse> {
    isSaving.value = true
    try {
      return await settingsApi.testNotificationSettings(payload)
    } catch (e) {
      if (e instanceof Error) error.value = e
      throw e
    } finally {
      isSaving.value = false
    }
  }

  async function saveAiSettings() {
    isSaving.value = true
    try {
      const payload = { ...aiSettings.value }
      const apiKey = (payload.OPENAI_API_KEY || '').trim()
      if (apiKey) {
        payload.OPENAI_API_KEY = apiKey
      } else {
        delete payload.OPENAI_API_KEY
      }
      await settingsApi.updateAiSettings(payload)
      if (aiSettings.value.OPENAI_API_KEY) {
        aiSettings.value.OPENAI_API_KEY = ''
      }
      // Refresh status
      systemStatus.value = await settingsApi.getSystemStatus()
    } catch (e) {
      if (e instanceof Error) error.value = e
      throw e
    } finally {
      isSaving.value = false
    }
  }

  async function saveRotationSettings() {
    isSaving.value = true
    try {
      await settingsApi.updateRotationSettings(rotationSettings.value)
    } catch (e) {
      if (e instanceof Error) error.value = e
      throw e
    } finally {
      isSaving.value = false
    }
  }

  async function saveBrowserSettings() {
    isSaving.value = true
    try {
      await settingsApi.updateBrowserSettings(browserSettings.value)
    } catch (e) {
      if (e instanceof Error) error.value = e
      throw e
    } finally {
      isSaving.value = false
    }
  }

  async function saveGlobalBlacklist(keywords: string[]) {
    isSaving.value = true
    try {
      const result = await settingsApi.updateGlobalBlacklist(keywords)
      globalBlacklistKeywords.value = result.keywords
    } catch (e) {
      if (e instanceof Error) error.value = e
      throw e
    } finally {
      isSaving.value = false
    }
  }

  async function testAiConnection() {
    isSaving.value = true
    try {
      const payload = { ...aiSettings.value }
      const apiKey = (payload.OPENAI_API_KEY || '').trim()
      if (apiKey) {
        payload.OPENAI_API_KEY = apiKey
      } else {
        delete payload.OPENAI_API_KEY
      }
      const res = await settingsApi.testAiSettings(payload)
      return res
    } catch (e) {
      if (e instanceof Error) error.value = e
      throw e
    } finally {
      isSaving.value = false
    }
  }

  onMounted(fetchAll)

  return {
    notificationSettings,
    aiSettings,
    rotationSettings,
    browserSettings,
    systemStatus,
    globalBlacklistKeywords,
    isLoading,
    isSaving,
    isReady,
    error,
    fetchAll,
    saveNotificationSettings,
    testNotification,
    saveAiSettings,
    saveRotationSettings,
    saveBrowserSettings,
    saveGlobalBlacklist,
    testAiConnection,
    refreshStatus,
  }
}
