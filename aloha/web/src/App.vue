<script setup lang="ts">
import { onMounted } from 'vue'
import { RouterView } from 'vue-router'
import Sidebar from './components/Sidebar.vue'
import { useThemeStore } from '@/stores/theme'

const themeStore = useThemeStore()

onMounted(() => {
  themeStore.loadTheme()
})
</script>

<template>
  <div id="app">
    <Sidebar />
    <main class="main-content">
      <RouterView />
    </main>
  </div>
</template>

<style scoped>
#app {
  width: 100%;
  height: 100vh;
  overflow: hidden;
  display: flex;
}

.main-content {
  flex: 1;
  overflow: hidden;
}
</style>