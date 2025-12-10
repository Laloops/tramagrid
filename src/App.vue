<script setup>
  import { onMounted, ref } from 'vue'
  import TopToolbar from './components/TopToolbar.vue'
  import ProjectControls from './components/ProjectControls.vue' 
  import ColorPalette from './components/ColorPalette.vue'
  import GridCanvas from './components/GridCanvas.vue'
  import { createSession } from './api.js'
  
  const isReady = ref(false)
  
  onMounted(async () => {
    try {
      await createSession()
      isReady.value = true
    } catch (e) {
      console.error("Erro ao iniciar sessão:", e)
    }
  })
</script>
  
<template>
  <div v-if="!isReady" class="loading">
    <div class="spinner"></div>
    <p>Iniciando TramaGrid...</p>
  </div>
  
  <div v-else class="app">
    <TopToolbar />

    <div class="main-layout">
      <aside class="sidebar custom-scroll">
        <ProjectControls />
        <ColorPalette />
      </aside>

      <main class="canvas-area">
        <GridCanvas />
      </main>
    </div>
  </div>
</template>
  
<style scoped>
.loading { 
  height: 100vh; 
  display: flex; 
  flex-direction: column; 
  justify-content: center; 
  align-items: center; 
  background: #1a1a1a; 
  color: #aaa; 
  gap: 15px;
}
.spinner {
  width: 40px; height: 40px;
  border: 4px solid #333;
  border-top-color: #e67e22;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.app { 
  height: 100vh; 
  display: flex; 
  flex-direction: column; 
  background-color: #121212;
}

.main-layout { 
  flex: 1; 
  display: flex; 
  overflow: hidden; 
}

.sidebar { 
  width: 320px; 
  background: #252526; 
  padding: 20px; 
  overflow-y: auto; 
  display: flex; 
  flex-direction: column; 
  gap: 10px;
  border-right: 1px solid #333;
}

.canvas-area { 
  flex: 1; 
  background: #0f0f0f; 
  overflow: hidden; 
  position: relative;
}

.custom-scroll::-webkit-scrollbar { width: 8px; }
.custom-scroll::-webkit-scrollbar-track { background: #1e1e1e; }
.custom-scroll::-webkit-scrollbar-thumb { background: #444; border-radius: 4px; }
.custom-scroll::-webkit-scrollbar-thumb:hover { background: #555; }
</style>