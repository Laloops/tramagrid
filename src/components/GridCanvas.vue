<script setup>
  import { ref, onMounted, onUnmounted, watch, computed } from "vue";
  import { getGridImage, updateParams, paintCell, getPixelIndex, replaceColor, undoLastAction, mergeColors, activeColorIndex, getPalette } from "../api.js";
  
  const imageSrc = ref("");
  const zoom = ref(1.0);
  const highlightedRow = ref(-1); // -1 = Nenhuma, 1 = Primeira Linha (Base)
  const currentTool = ref('ruler');
  const colorPickerInput = ref(null);
  const selectedIndexForSwap = ref(-1);
  const fullPalette = ref([]); 
  
  // Pan/Drag
  const panX = ref(0);
  const panY = ref(0);
  const isDragging = ref(false);
  const dragStartX = ref(0);
  const dragStartY = ref(0);
  
  const activeColorHex = computed(() => {
    const color = fullPalette.value.find(c => c.index === activeColorIndex.value);
    return color ? color.hex : 'transparent';
  });
  
  async function refresh() {
    const data = await getGridImage();
    imageSrc.value = data;
    try {
      const pal = await getPalette();
      fullPalette.value = Array.isArray(pal) ? pal : pal.palette || [];
    } catch (e) {}
  }
  
  watch([zoom, highlightedRow], async () => {
    // Sempre atualiza o backend quando a linha muda
    await updateParams({ highlighted_row: highlightedRow.value === -1 ? null : highlightedRow.value });
    refresh();
  });
  
  onMounted(() => { refresh(); window.refreshGrid = refresh; });
  
  // ... (handleWheel, Dragging logic - MANTENHA IGUAL) ...
  function handleWheel(e) {
    e.preventDefault();
    const delta = e.deltaY > 0 ? 0.9 : 1.1;
    zoom.value = Math.max(0.3, Math.min(10, zoom.value * delta));
  }
  
  function startDrag(e) {
    if (e.button === 1 || (currentTool.value === 'ruler' && e.button === 0)) {
      isDragging.value = true;
      dragStartX.value = e.clientX - panX.value;
      dragStartY.value = e.clientY - panY.value;
    }
  }
  function drag(e) {
    if (!isDragging.value) return;
    panX.value = e.clientX - dragStartX.value;
    panY.value = e.clientY - dragStartY.value;
  }
  function stopDrag() { isDragging.value = false; }
  onUnmounted(() => {
    document.removeEventListener("mousemove", drag);
    document.removeEventListener("mouseup", stopDrag);
  });
  // ... (Fim da lógica de drag mantida) ...

  async function onColorPicked(e) {
    const newHex = e.target.value;
    if (selectedIndexForSwap.value !== -1 && selectedIndexForSwap.value !== null) {
      try { 
        await replaceColor(selectedIndexForSwap.value, newHex); 
        refresh(); 
      } catch (err) { console.error(err); }
      finally { selectedIndexForSwap.value = -1; e.target.value = null; }
    }
  }
  
  async function setSmartTool() { currentTool.value = 'picker'; }
  
  async function handleClick(e) {
    if (isDragging.value) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const clickY = e.clientY - rect.top;
    const rawX = clickX / zoom.value;
    const rawY = clickY / zoom.value;
    const MARGIN = 50; const CELL_SIZE = 22;
    if (rawX < MARGIN || rawY < MARGIN) return;
    const gridX = Math.floor((rawX - MARGIN) / CELL_SIZE);
    const gridY = Math.floor((rawY - MARGIN) / CELL_SIZE);
    
    // NOVO: Se clicar com a régua, define a linha imediatamente
    if (currentTool.value === 'ruler') {
      const row = gridY + 1;
      highlightedRow.value = (highlightedRow.value === row) ? -1 : row;
      return; 
    }

    const clickedIndex = await getPixelIndex(gridX, gridY);
    if (clickedIndex === -1) return;
  
    if (currentTool.value === 'brush') {
      await paintCell(gridX, gridY);
      refresh();
    } else if (currentTool.value === 'picker') {
      activeColorIndex.value = clickedIndex;
      currentTool.value = 'brush'; 
    } else if (currentTool.value === 'swap') {
      selectedIndexForSwap.value = clickedIndex;
      colorPickerInput.value.click();
    } else if (currentTool.value === 'bucket') {
      const targetColor = activeColorIndex.value; 
      const sourceColor = clickedIndex; 
      if (targetColor === sourceColor) return; 
      await mergeColors(sourceColor, targetColor);
      refresh();
    }
  }
  
  async function undo() { await undoLastAction(); refresh(); }

  // CONTROLE DE LINHA (Próxima/Anterior)
  function nextRow() { highlightedRow.value += 1; }
  function prevRow() { if (highlightedRow.value > 1) highlightedRow.value -= 1; }
</script>
  
<template>
  <div class="canvas-wrapper">
    <input type="color" ref="colorPickerInput" style="display: none" @change="onColorPicked" @click.stop />

    <div class="tools-hud">
      <button @click="undo" title="Desfazer (Ctrl+Z)" class="action-btn undo-btn">↩️</button>
      <div class="separator"></div>

      <button @click="currentTool = 'ruler'" :class="{ active: currentTool === 'ruler' }" title="Modo Execução (Régua)">📏</button>
      
      <div v-if="currentTool === 'ruler'" class="row-controls">
         <button @click="prevRow" class="btn-row" title="Linha Anterior">⬆️</button>
         <span class="row-display" title="Linha Atual">L: {{ highlightedRow > 0 ? highlightedRow : '-' }}</span>
         <button @click="nextRow" class="btn-row" title="Próxima Linha">⬇️</button>
      </div>

      <div class="separator" v-if="currentTool === 'ruler'"></div>
      
      <template v-if="currentTool !== 'ruler'">
          <div class="smart-tool-group">
            <button 
              v-if="currentTool !== 'brush' && currentTool !== 'bucket'" 
              @click="setSmartTool" 
              class="btn-smart"
              title="1º Pegar a cor desejada"
            >💧 Cor</button>
    
            <button 
              v-else 
              @click="currentTool = 'picker'" 
              class="btn-smart active"
              title="Cor ativa"
            >
              <span class="dot" :style="{ backgroundColor: activeColorHex }"></span>
            </button>
          </div>
    
          <div class="mode-toggle">
             <button @click="currentTool = 'brush'" :class="{ active: currentTool === 'brush' }" title="Pincel">✏️</button>
             <button @click="currentTool = 'bucket'" :class="{ active: currentTool === 'bucket' }" title="Balde">🪣</button>
          </div>
          <button @click="currentTool = 'swap'" :class="{ active: currentTool === 'swap' }" title="Trocar Cor">🔄</button>
      </template>
      <button v-else @click="currentTool = 'brush'" title="Voltar para Edição" class="btn-edit-mode">🛠️ Editar</button>

      <div class="separator"></div>
      <div class="zoom-indicator">{{ Math.round(zoom * 100) }}%</div>
    </div>

    <div class="canvas" @wheel.prevent="handleWheel" @mousedown="startDrag" @mousemove="drag" @mouseup="stopDrag" @mouseleave="stopDrag" @contextmenu.prevent>
      <img v-if="imageSrc" :src="imageSrc" @click="handleClick" :style="{ transform: `translate(${panX}px, ${panY}px) scale(${zoom})`, transformOrigin: 'top left', imageRendering: 'pixelated', cursor: currentTool === 'ruler' ? (isDragging ? 'grabbing' : 'default') : 'crosshair' }" draggable="false" />
      <div v-else class="placeholder">Carregue uma imagem</div>
    </div>
  </div>
</template>
  
<style scoped>
.canvas-wrapper { position: relative; width: 100%; height: 100%; overflow: hidden; background: #111; }
.canvas { width: 100%; height: 100%; cursor: default; }

.tools-hud {
  position: absolute; bottom: 30px; /* Mudei para baixo para facilitar o uso durante execução */
  left: 50%; transform: translateX(-50%);
  background: rgba(30, 30, 30, 0.9); padding: 8px 15px; border-radius: 40px;
  display: flex; gap: 10px; align-items: center; z-index: 100;
  box-shadow: 0 10px 25px rgba(0,0,0,0.5); border: 1px solid #444;
  backdrop-filter: blur(5px);
}

.tools-hud button {
  background: transparent; border: none; font-size: 1.2rem; cursor: pointer;
  padding: 6px; border-radius: 50%; transition: all 0.2s; color: #ccc;
  width: 36px; height: 36px; display: flex; align-items: center; justify-content: center;
}
.tools-hud button:hover { background: rgba(255,255,255,0.1); color: white; transform: translateY(-2px); }
.tools-hud button.active { background: #e67e22; color: white; box-shadow: 0 0 10px rgba(230, 126, 34, 0.4); }

/* CONTROLES DE LINHA */
.row-controls { display: flex; align-items: center; gap: 5px; background: rgba(0,0,0,0.3); padding: 2px 8px; border-radius: 20px; }
.row-display { font-family: monospace; font-size: 1rem; color: #f1c40f; font-weight: bold; min-width: 40px; text-align: center; }
.btn-row { font-size: 1rem !important; width: 30px !important; height: 30px !important; }

.btn-smart {
  border-radius: 20px !important; width: auto !important; padding: 0 12px !important;
  font-size: 0.9rem !important; font-weight: bold; gap: 5px;
}
.btn-smart.active { background: #e67e22 !important; }
.dot { width: 12px; height: 12px; border-radius: 50%; border: 2px solid white; }

.mode-toggle { display: flex; background: #222; border-radius: 20px; padding: 2px; }
.separator { width: 1px; height: 20px; background: #555; }
.zoom-indicator { font-size: 0.75rem; color: #888; margin-left: 5px; }

.placeholder { color: #555; text-align: center; margin-top: 30vh; font-size: 1.2rem; }
.btn-edit-mode { font-size: 0.8rem !important; width: auto !important; border-radius: 20px !important; padding: 0 10px !important; }
</style>