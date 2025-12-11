<script setup>
  import { ref, onMounted, onUnmounted } from 'vue'
  // Removi uploadImage, pois não é mais usado aqui
  import { generateGrid, updateParams, sessionId, getParams, eventBus } from '../api.js'
  
  const maxColors = ref(64)
  const gridWidth = ref(130)
  const brightness = ref(1.0)
  const contrast = ref(1.0)
  const saturation = ref(1.0)
  const gamma = ref(1.0)
  const posterize = ref(8)
  const gaugeStitches = ref(20)
  const gaugeRows = ref(20)
  const showGrid = ref(true)
  
  async function syncParams() {
      try {
          const p = await getParams()
          if (p.max_colors !== undefined) maxColors.value = p.max_colors
          if (p.grid_width_cells !== undefined) gridWidth.value = p.grid_width_cells
          if (p.brightness !== undefined) brightness.value = p.brightness
          if (p.contrast !== undefined) contrast.value = p.contrast
          if (p.saturation !== undefined) saturation.value = p.saturation
          if (p.gamma !== undefined) gamma.value = p.gamma
          if (p.posterize !== undefined) posterize.value = p.posterize
          if (p.gauge_stitches !== undefined) gaugeStitches.value = p.gauge_stitches
          if (p.gauge_rows !== undefined) gaugeRows.value = p.gauge_rows
          if (p.show_grid !== undefined) showGrid.value = p.show_grid
      } catch (e) { console.error("Erro ao sincronizar params", e) }
  }
  
  onMounted(async () => {
      eventBus.addEventListener('refresh', syncParams)
      await syncParams()
      // Gera automaticamente se já houver sessão (fluxo vindo da Home)
      if (sessionId.value) await generate()
  })

  onUnmounted(() => {
      eventBus.removeEventListener('refresh', syncParams)
  })
  
  async function generate() {
    await updateParams({ 
      max_colors: maxColors.value, 
      grid_width_cells: gridWidth.value,
      brightness: brightness.value,
      contrast: contrast.value,
      saturation: saturation.value,
      gamma: gamma.value,
      posterize: posterize.value,
      gauge_stitches: gaugeStitches.value,
      gauge_rows: gaugeRows.value,
      show_grid: showGrid.value
    })
    await generateGrid()
  }
  
  async function toggleGrid() {
    showGrid.value = !showGrid.value
    await generate()
  }
</script>
  
<template>
<div class="project-controls">
  <h3>Projeto</h3>
  
  <div class="control-group">
      <div class="toggle-row">
          <span>Mostrar Grade</span>
          <button class="btn-toggle" :class="{ active: showGrid }" @click="toggleGrid">
              {{ showGrid ? 'ON' : 'OFF' }}
          </button>
      </div>
  </div>

  <div class="separator"></div>

  <div class="control-group">
      <h4>Amostra (10x10cm)</h4>
      <div class="gauge-row">
          <label>
              <span>Pontos:</span>
              <input v-model.number="gaugeStitches" @keyup.enter="generate" type="number" class="input-number" />
          </label>
          <label>
              <span>Carr.:</span>
              <input v-model.number="gaugeRows" @keyup.enter="generate" type="number" class="input-number" />
          </label>
      </div>
      <small class="hint">Define a proporção do ponto.</small>
  </div>

  <div class="separator"></div>

  <div class="control-group">
    <label>
      <span>Posterizar: {{ posterize }}</span>
      <input v-model.number="posterize" @change="generate" type="range" min="1" max="8" step="1" class="slider" />
    </label>
    <label>
      <span>Sombras: {{ gamma }}</span>
      <input v-model.number="gamma" @change="generate" type="range" min="0.5" max="3.0" step="0.1" class="slider" />
    </label>
    <label>
      <span>Brilho: {{ brightness }}</span>
      <input v-model.number="brightness" @change="generate" type="range" min="0.1" max="5.0" step="0.1" class="slider" />
    </label>
    <label>
      <span>Contraste: {{ contrast }}</span>
      <input v-model.number="contrast" @change="generate" type="range" min="0.1" max="5.0" step="0.1" class="slider" />
    </label>
    <label>
      <span>Saturação: {{ saturation }}</span>
      <input v-model.number="saturation" @change="generate" type="range" min="0.0" max="3.0" step="0.1" class="slider" />
    </label>
  </div>

  <div class="separator"></div>

  <div class="control-group">
    <label>
      <span>Cores Máx:</span>
      <input v-model.number="maxColors" @keyup.enter="generate" type="number" min="2" max="128" class="input-number" />
    </label>
    <label>
      <span>Largura (nós):</span>
      <input v-model.number="gridWidth" @keyup.enter="generate" type="number" min="20" max="300" class="input-number" />
    </label>
  </div>

  <button @click="generate" class="btn success full-width mt-2">↻ Atualizar Grade</button>
</div>
</template>

<style scoped>
.project-controls { background: #1e1e1e; padding: 20px; border-radius: 12px; color: white; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
h3 { margin-top: 0; font-size: 1.1rem; color: #e67e22; margin-bottom: 15px; font-weight: 600; }
h4 { margin: 5px 0 10px 0; font-size: 0.9rem; color: #aaa; text-transform: uppercase; letter-spacing: 1px; }
.control-group { display: flex; flex-direction: column; gap: 12px; }
label { display: flex; justify-content: space-between; align-items: center; font-size: 0.85rem; color: #ccc; }
.gauge-row { display: flex; gap: 10px; }
.gauge-row label { flex: 1; }
.slider { width: 55%; cursor: pointer; accent-color: #e67e22; }
.input-number { width: 60px; background: #333; border: 1px solid #444; color: white; padding: 4px; border-radius: 4px; text-align: center; }
.separator { height: 1px; background: #444; margin: 15px 0; }
.btn { padding: 12px; border: none; color: white; font-weight: bold; cursor: pointer; border-radius: 6px; transition: all 0.2s; text-transform: uppercase; font-size: 0.85rem; letter-spacing: 0.5px; }
.btn:hover { opacity: 0.9; transform: translateY(-1px); }
.full-width { width: 100%; }
.mt-2 { margin-top: 10px; }
.success { background: #27ae60; }
.hint { font-size: 0.75rem; color: #666; font-style: italic; }
.toggle-row { display: flex; justify-content: space-between; align-items: center; font-size: 0.9rem; color: #ddd; }
.btn-toggle { background: #333; border: 1px solid #555; color: #aaa; padding: 4px 12px; border-radius: 15px; cursor: pointer; transition: 0.3s; font-size: 0.8rem; font-weight: bold; }
.btn-toggle.active { background: #27ae60; color: white; border-color: #2ecc71; }
</style>