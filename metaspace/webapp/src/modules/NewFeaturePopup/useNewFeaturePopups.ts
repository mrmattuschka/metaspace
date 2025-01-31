import { reactive, computed, ref } from '@vue/composition-api'
import { isArray } from 'lodash-es'

import { getLocalStorage, setLocalStorage } from '../../lib/localStorage'

const STORAGE_KEY = 'dismissedFeaturePopups'

export const FEATURE_KEYS = [
  'uploadCustomDatabases',
  'groupDatabasesTab',
  'multipleIonImages',
]

function getDismissedPopups() {
  try {
    const list = getLocalStorage(STORAGE_KEY)
    if (isArray(list)) {
      // Filter out invalid/old entries
      return list.filter(item => FEATURE_KEYS.includes(item))
    } else {
      return []
    }
  } catch (ex) {
    return []
  }
}

const previousDismissedPopups = getDismissedPopups()

const state = reactive({
  dismissed: [...previousDismissedPopups],
  queued: [] as string[],
})

const activePopup = computed(() => state.queued[0])

function closeActivePopup() {
  const popup = state.queued.shift()
  state.dismissed.push(popup)
  return popup
}

const popoverRef = ref<HTMLElement>()

export default () => {
  return {
    activePopup,
    popoverRef,
    isDismissed(featureKey: string) {
      return state.dismissed.includes(featureKey)
    },
    queuePopup(featureKey: string) {
      if (state.dismissed.includes(featureKey) || state.queued.includes(featureKey)) {
        return
      }
      state.queued.push(featureKey)
    },
    unqueuePopup(featureKey: string) {
      const index = state.queued.indexOf(featureKey)
      if (index !== -1) {
        state.queued.splice(index, 1)
      }
    },
    remindLater() {
      closeActivePopup()
    },
    dismissPopup() {
      const popup = closeActivePopup()
      previousDismissedPopups.push(popup)
      setLocalStorage(STORAGE_KEY, previousDismissedPopups)
    },
  }
}
