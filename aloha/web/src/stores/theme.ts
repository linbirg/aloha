import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

export type Theme = 'dark' | 'light'

const THEME_STORAGE_KEY = 'aloha_theme'

export const useThemeStore = defineStore('theme', () => {
  const currentTheme = ref<Theme>('dark')

  function loadTheme() {
    try {
      const stored = localStorage.getItem(THEME_STORAGE_KEY)
      if (stored === 'light' || stored === 'dark') {
        currentTheme.value = stored
      } else if (window.matchMedia('(prefers-color-scheme: light)').matches) {
        currentTheme.value = 'light'
      }
    } catch {
      currentTheme.value = 'dark'
    }
    applyTheme(currentTheme.value)
  }

  function applyTheme(theme: Theme) {
    document.documentElement.setAttribute('data-theme', theme)
  }

  function toggleTheme() {
    currentTheme.value = currentTheme.value === 'dark' ? 'light' : 'dark'
  }

  function saveTheme() {
    try {
      localStorage.setItem(THEME_STORAGE_KEY, currentTheme.value)
    } catch {
      // Ignore localStorage errors
    }
  }

  watch(currentTheme, (newTheme) => {
    applyTheme(newTheme)
    saveTheme()
  })

  return {
    currentTheme,
    loadTheme,
    toggleTheme,
    applyTheme
  }
})
