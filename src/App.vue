<script setup>
  import { onMounted, ref } from 'vue'
  import TopToolbar from './components/TopToolbar.vue'
  import ProjectControls from './components/ProjectControls.vue' 
  import ColorPalette from './components/ColorPalette.vue'
  import GridCanvas from './components/GridCanvas.vue'
  import { createSession } from './api.js'
  
  const isReady = ref(false)
  const isSidebarOpen = ref(true) 
  
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
      <button 
        v-if="!isSidebarOpen" 
        class="toggle-sidebar-floating"
        @click="isSidebarOpen = true"
        title="Abrir Menu"
      >
        <span class="icon">☰</span>
      </button>

      <aside class="sidebar" :class="{ closed: !isSidebarOpen }">
        
        <div class="sidebar-header">
            <h2 class="sidebar-title">Ferramentas</h2>
            <button @click="isSidebarOpen = false" class="close-btn" title="Recolher Menu">
                ✕
            </button>
        </div>
        
        <div class="sidebar-content custom-scroll">
            <ProjectControls />
            <ColorPalette />
        </div>

      </aside>

      <main class="canvas-area">
        <GridCanvas />
      </main>
    </div>
  </div>
</template>
  
<style scoped>
/* Loading Styles */
.loading { height: 100vh; display: flex; flex-direction: column; justify-content: center; align-items: center; background: #1a1a1a; color: #aaa; gap: 15px; }
.spinner { width: 40px; height: 40px; border: 4px solid #333; border-top-color: #e67e22; border-radius: 50%; animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

/* App Layout */
.app { height: 100vh; display: flex; flex-direction: column; background-color: #121212; }
.main-layout { flex: 1; display: flex; overflow: hidden; position: relative; }

/* --- SIDEBAR --- */
.sidebar { 
  width: 340px; /* Um pouco mais largo para conforto */
  background: #252526; 
  border-right: 1px solid #333;
  transition: width 0.3s cubic-bezier(0.25, 0.8, 0.25, 1); /* Animação mais suave estilo "Gemini" */
  
  /* Mágica do Layout Flex */
  display: flex; 
  flex-direction: column; 
  overflow: hidden; /* Impede o conteúdo de vazar durante a animação */
}

/* Estado Fechado */
.sidebar.closed { 
  width: 0; 
  border: none;
}

/* 1. Header Fixo */
.sidebar-header { 
  flex-shrink: 0; /* Impede que o header seja esmagado */
  height: 55px;
  display: flex; 
  align-items: center; 
  justify-content: space-between; 
  padding: 0 20px;
  border-bottom: 1px solid #333;
  background-color: #252526; /* Garante que o conteúdo rolando por baixo não apareça */
  z-index: 10;
}

.sidebar-title {
  margin: 0;
  font-size: 0.95rem;
  color: #ddd;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.close-btn { 
  background: transparent; 
  border: none; 
  color: #aaa; 
  cursor: pointer; 
  font-size: 1.1rem; 
  width: 32px; 
  height: 32px; 
  border-radius: 6px;
  display: flex; 
  align-items: center; 
  justify-content: center;
  transition: all 0.2s;
}
.close-btn:hover { background: rgba(255,255,255,0.1); color: white; }

/* 2. Conteúdo com Scroll */
.sidebar-content {
  flex: 1; /* Ocupa todo o espaço restante verticalmente */
  overflow-y: auto; /* Scroll bar aparece AQUI, não na sidebar inteira */
  padding: 20px;
  padding-bottom: 40px; /* Espaço extra no final */
}

/* Botão Flutuante (Aparece quando fechado) */
.toggle-sidebar-floating {
    position: absolute; 
    left: 20px; 
    top: 20px; 
    z-index: 50;
    
    background: #252526; 
    color: #fff; 
    border: 1px solid #444;
    
    width: 44px; height: 44px; 
    border-radius: 8px; /* Quadrado arredondado (Moderno) */
    
    cursor: pointer; 
    display: flex; align-items: center; justify-content: center;
    box-shadow: 0 4px 12px rgba(0,0,0,0.4);
    transition: all 0.2s;
}
.toggle-sidebar-floating:hover { 
  background: #333; 
  transform: translateY(-2px); 
  border-color: #e67e22; 
  color: #e67e22;
}
.icon { font-size: 1.4rem; line-height: 1; }

/* Canvas Area */
.canvas-area { flex: 1; background: #0f0f0f; overflow: hidden; position: relative; }

/* Scrollbar Customizada */
.custom-scroll::-webkit-scrollbar { width: 6px; }
.custom-scroll::-webkit-scrollbar-track { background: transparent; }
.custom-scroll::-webkit-scrollbar-thumb { background: #444; border-radius: 3px; }
.custom-scroll::-webkit-scrollbar-thumb:hover { background: #555; }
</style>