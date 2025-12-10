<!-- src/App.vue -->
<script setup>
  import { onMounted, ref } from 'vue'
  import TopToolbar from './components/TopToolbar.vue'
  import ColorPalette from './components/ColorPalette.vue'
  import GridCanvas from './components/GridCanvas.vue'
  import SimplifyControls from './components/SimplifyControls.vue'
  import { createSession } from './api.js'
  
  const isReady = ref(false)
  
  onMounted(async () => {
    await createSession()
    isReady.value = true
  })
  </script>
  
  <template>
    <div v-if="!isReady" class="loading">Carregando TramaGrid...</div>
    <div v-else class="app">
      <TopToolbar />
      <div class="main">
        <aside class="sidebar">
          <ColorPalette />
          <SimplifyControls />
        </aside>
        <main class="canvas">
          <GridCanvas />
        </main>
      </div>
    </div>
  </template>
  
  <style scoped>
  .loading { height: 100vh; display: grid; place-items: center; background: #2c3e50; color: white; font-size: 1.5rem; }
  .app { height: 100vh; display: flex; flex-direction: column; }
  .main { flex: 1; display: flex; overflow: hidden; }
  .sidebar { width: 280px; background: #2c3e50; padding: 16px; overflow-y: auto; }
  .canvas { flex: 1; background: #111; overflow: auto; padding: 20px; }
  </style>