<script setup>
  import { ref, onMounted, onUnmounted, watch, computed } from "vue";
  import { 
    getGridImage, updateParams, paintCell, getPixelIndex, 
    replaceColor, undoLastAction, mergeColors, replaceColorInRegion,
    activeColorIndex, getPalette, mergeState
  } from "../api.js";
  // IMPORTAR O TOAST E O CONFIRM
  import { showToast, showConfirm } from "../toast.js";

  const imageSrc = ref("");
  const zoom = ref(1.0);
  const highlightedRow = ref(-1);
  const currentTool = ref('ruler'); 
  const colorPickerInput = ref(null);
  const selectedIndexForSwap = ref(-1);
  const fullPalette = ref([]); 
  
  // Seleção Retangular
  const selectionRect = ref(null); 
  const isSelecting = ref(false);
  const selStart = ref({ x: 0, y: 0 });

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
    await updateParams({ highlighted_row: highlightedRow.value });
    refresh();
  });
  
  watch(currentTool, (newTool) => {
    if (newTool !== 'ruler') highlightedRow.value = -1;
  });

  onMounted(() => { refresh(); window.refreshGrid = refresh; });
  
  function handleWheel(e) {
    e.preventDefault();
    const delta = e.deltaY > 0 ? 0.9 : 1.1;
    zoom.value = Math.max(0.3, Math.min(10, zoom.value * delta));
  }

  function getGridCoords(clientX, clientY) {
    const canvasEl = document.querySelector('.canvas'); 
    if (!canvasEl) return { x: -1, y: -1 };
    const rect = canvasEl.getBoundingClientRect();
    const relX = clientX - rect.left - panX.value;
    const relY = clientY - rect.top - panY.value;
    const rawX = relX / zoom.value;
    const rawY = relY / zoom.value;
    const MARGIN = 50; const CELL_SIZE = 22;
    const gridX = Math.floor((rawX - MARGIN) / CELL_SIZE);
    const gridY = Math.floor((rawY - MARGIN) / CELL_SIZE);
    return { gridX, gridY };
  }

  function onMouseDown(e) {
    if (e.button === 1 || currentTool.value === 'ruler') {
      isDragging.value = true;
      dragStartX.value = e.clientX - panX.value;
      dragStartY.value = e.clientY - panY.value;
      return;
    }
    if (currentTool.value === 'select') {
      const { gridX, gridY } = getGridCoords(e.clientX, e.clientY);
      isSelecting.value = true;
      selStart.value = { x: gridX, y: gridY };
      selectionRect.value = { x: gridX, y: gridY, w: 1, h: 1 };
      return;
    }
  }

  function onMouseMove(e) {
    if (isDragging.value) {
      panX.value = e.clientX - dragStartX.value;
      panY.value = e.clientY - dragStartY.value;
      return;
    }
    if (isSelecting.value) {
      const { gridX, gridY } = getGridCoords(e.clientX, e.clientY);
      const startX = selStart.value.x;
      const startY = selStart.value.y;
      const minX = Math.min(startX, gridX);
      const minY = Math.min(startY, gridY);
      const w = Math.abs(gridX - startX) + 1;
      const h = Math.abs(gridY - startY) + 1;
      selectionRect.value = { x: minX, y: minY, w, h };
    }
  }

  function onMouseUp() {
    isDragging.value = false;
    isSelecting.value = false;
  }

  // --- AQUI ESTÁ A MÁGICA ATUALIZADA ---
  async function handleClick(e) {
    if (isDragging.value || isSelecting.value) return; 
    
    const { gridX, gridY } = getGridCoords(e.clientX, e.clientY);
    if (gridX < 0 || gridY < 0) return; 
    
    // ============================================
    // 1. MODO UNIR (GLOBAL) - Prioridade Máxima
    // ============================================
    if (mergeState.value.isActive) {
        const clickedIndex = await getPixelIndex(gridX, gridY);
        if (clickedIndex === -1) return;

        if (mergeState.value.sourceIndex === null) {
            // FASE 1: Escolha da ORIGEM
            mergeState.value.sourceIndex = clickedIndex;
            showToast("Origem selecionada. Agora clique na cor de destino.", "info");
        } 
        else {
            // FASE 2: Escolha do DESTINO
            if (clickedIndex === mergeState.value.sourceIndex) {
               showToast("Você clicou na mesma cor! Escolha outra.", "warning");
               return;
            }
            
            // SUBSTITUÍDO: confirm() por showConfirm()
            const confirmed = await showConfirm("Unir essas cores permanentemente?");
            
            if (confirmed) {
               await mergeColors(mergeState.value.sourceIndex, clickedIndex);
               mergeState.value.isActive = false;
               mergeState.value.sourceIndex = null;
               showToast("Cores unidas!", "success");
               refresh();
            }
        }
        return; 
    }
    // ============================================

    // 2. Comportamento Normal (Régua)
    if (currentTool.value === 'ruler') {
      const row = gridY + 1;
      highlightedRow.value = (highlightedRow.value === row) ? -1 : row;
      return;
    }

    const clickedIndex = await getPixelIndex(gridX, gridY);
    if (clickedIndex === -1) return;
  
    // 3. Ferramentas de Edição
    if (currentTool.value === 'brush') {
      await paintCell(gridX, gridY);
      refresh();
    } else if (currentTool.value === 'picker') {
      activeColorIndex.value = clickedIndex;
      currentTool.value = 'brush';
      showToast("Cor selecionada!", "info");
    } else if (currentTool.value === 'swap') {
      selectedIndexForSwap.value = clickedIndex;
      colorPickerInput.value.click();
    } else if (currentTool.value === 'bucket') {
      const targetColor = activeColorIndex.value; 
      const sourceColor = clickedIndex; 
      if (targetColor === sourceColor) return; 
      
      if (selectionRect.value) {
          const isInside = gridX >= selectionRect.value.x && gridX < selectionRect.value.x + selectionRect.value.w && gridY >= selectionRect.value.y && gridY < selectionRect.value.y + selectionRect.value.h;
          if (isInside) {
              await replaceColorInRegion(selectionRect.value.x, selectionRect.value.y, selectionRect.value.w, selectionRect.value.h, sourceColor, targetColor);
              refresh();
          } else {
              showToast("Clique DENTRO da seleção para usar o balde.", "warning");
          }
      } else {
          // SUBSTITUÍDO: confirm() por showConfirm()
          const confirmed = await showConfirm("Substituir essa cor na imagem INTEIRA?");
          if(confirmed) {
             await mergeColors(sourceColor, targetColor);
             showToast("Cores substituídas!", "success");
             refresh();
          }
      }
    }
  }
  
  async function undo() { await undoLastAction(); refresh(); showToast("Desfeito!", "info"); }
  function nextRow() { highlightedRow.value += 1; }
  function prevRow() { if (highlightedRow.value > 1) highlightedRow.value -= 1; }
  function toggleRulerTool() { currentTool.value = (currentTool.value === 'ruler') ? 'brush' : 'ruler'; }
  function clearSelection() { selectionRect.value = null; }

  async function onColorPicked(e) {
    const newHex = e.target.value;
    if (selectedIndexForSwap.value !== -1) {
      try { 
          await replaceColor(selectedIndexForSwap.value, newHex); 
          refresh(); 
          showToast("Cor trocada com sucesso!", "success");
      } 
      finally { selectedIndexForSwap.value = -1; e.target.value = null; }
    }
  }
</script>
  
<template>
  <div class="canvas-wrapper">
    <input type="color" ref="colorPickerInput" style="display: none" @change="onColorPicked" @click.stop />

    <div v-if="mergeState.isActive" class="merge-overlay-warning">
       <span v-if="mergeState.sourceIndex === null">👆 Clique na cor para <strong>REMOVER</strong></span>
       <span v-else>🎯 Clique na cor de <strong>DESTINO</strong></span>
    </div>

    <div class="tools-hud">
      <button @click="undo" title="Desfazer" class="action-btn">↩️</button>
      <div class="separator"></div>
      <button @click="toggleRulerTool" :class="{ active: currentTool === 'ruler' }" title="Régua">📏</button>
      <div v-if="currentTool === 'ruler'" class="row-controls">
         <button @click="prevRow" class="btn-row">⬆️</button>
         <span class="row-display">{{ highlightedRow > 0 ? 'L: ' + highlightedRow : '---' }}</span>
         <button @click="nextRow" class="btn-row">⬇️</button>
      </div>
      <div class="separator" v-if="currentTool === 'ruler'"></div>
      <template v-if="currentTool !== 'ruler'">
          <div class="smart-tool-group">
            <button v-if="currentTool !== 'brush' && currentTool !== 'bucket' && currentTool !== 'select'" @click="currentTool = 'picker'" class="btn-smart">💧 Cor</button>
            <button v-else @click="currentTool = 'picker'" class="btn-smart active"><span class="dot" :style="{ backgroundColor: activeColorHex }"></span></button>
          </div>
          <div class="selection-group">
             <button @click="currentTool = 'select'" :class="{ active: currentTool === 'select' }" title="Seleção">⛝</button>
             <button v-if="selectionRect" @click="clearSelection" class="btn-clear-sel">✖</button>
          </div>
          <div class="mode-toggle">
             <button @click="currentTool = 'brush'" :class="{ active: currentTool === 'brush' }" title="Pincel">✏️</button>
             <button @click="currentTool = 'bucket'" :class="{ active: currentTool === 'bucket' }" title="Balde">🪣</button>
          </div>
          <button @click="currentTool = 'swap'" :class="{ active: currentTool === 'swap' }" title="Trocar Hex">🔄</button>
      </template>
      <button v-else @click="currentTool = 'brush'" class="btn-edit-mode">🛠️ Editar</button>
      <div class="separator"></div>
      <div class="zoom-indicator">{{ Math.round(zoom * 100) }}%</div>
    </div>

    <div class="canvas" 
         :style="{ cursor: mergeState.isActive ? 'alias' : (currentTool === 'select' ? 'crosshair' : 'default') }"
         @wheel.prevent="handleWheel" 
         @mousedown="onMouseDown" 
         @mousemove="onMouseMove" 
         @mouseup="onMouseUp"
         @mouseleave="onMouseUp"
         @contextmenu.prevent>
         
      <div class="transform-container" 
           :style="{ transform: `translate(${panX}px, ${panY}px) scale(${zoom})`, transformOrigin: 'top left' }">
           <img v-if="imageSrc" :src="imageSrc" @click="handleClick" draggable="false" class="pixel-art" />
           <div v-if="selectionRect" class="selection-overlay" :style="{ left: (50 + selectionRect.x * 22) + 'px', top: (50 + selectionRect.y * 22) + 'px', width: (selectionRect.w * 22) + 'px', height: (selectionRect.h * 22) + 'px' }"></div>
      </div>
      <div v-if="!imageSrc" class="placeholder">Carregue uma imagem</div>
    </div>
  </div>
</template>

<style scoped>
/* (O CSS mantém-se idêntico ao original, garantindo o visual que já funcionava) */
.merge-overlay-warning { position: absolute; top: 20px; left: 50%; transform: translateX(-50%); background: rgba(230, 126, 34, 0.9); color: white; padding: 10px 20px; border-radius: 30px; font-weight: bold; z-index: 200; pointer-events: none; box-shadow: 0 4px 15px rgba(0,0,0,0.5); animation: pulse 2s infinite; }
@keyframes pulse { 0% { opacity: 0.8; } 50% { opacity: 1; transform: translateX(-50%) scale(1.05); } 100% { opacity: 0.8; } }
.canvas-wrapper { position: relative; width: 100%; height: 100%; overflow: hidden; background: #111; }
.canvas { width: 100%; height: 100%; }
.transform-container { position: absolute; top: 0; left: 0; pointer-events: none; }
.transform-container > * { pointer-events: auto; }
.pixel-art { image-rendering: pixelated; }
.selection-overlay { position: absolute; border: 2px dashed #f1c40f; background-color: rgba(241, 196, 15, 0.15); box-shadow: 0 0 4px rgba(0,0,0,0.8); pointer-events: none; z-index: 10; }
.tools-hud { position: absolute; bottom: 30px; left: 50%; transform: translateX(-50%); background: rgba(30, 30, 30, 0.95); padding: 8px 15px; border-radius: 40px; display: flex; gap: 10px; align-items: center; z-index: 100; box-shadow: 0 10px 30px rgba(0,0,0,0.6); border: 1px solid #444; backdrop-filter: blur(5px); }
.tools-hud button { background: transparent; border: none; font-size: 1.2rem; cursor: pointer; padding: 6px; border-radius: 50%; transition: all 0.2s; color: #ccc; width: 36px; height: 36px; display: flex; align-items: center; justify-content: center; }
.tools-hud button:hover { background: rgba(255,255,255,0.1); color: white; transform: translateY(-2px); }
.tools-hud button.active { background: #e67e22; color: white; box-shadow: 0 0 10px rgba(230, 126, 34, 0.4); }
.selection-group { display: flex; gap: 2px; background: #222; border-radius: 20px; padding: 0 4px; align-items: center; }
.btn-clear-sel { color: #e74c3c !important; font-size: 1rem !important; font-weight: bold; width: 28px !important; height: 28px !important; }
.btn-clear-sel:hover { background: rgba(231, 76, 60, 0.2) !important; }
.row-controls { display: flex; align-items: center; gap: 5px; background: rgba(0,0,0,0.3); padding: 2px 8px; border-radius: 20px; }
.row-display { font-family: monospace; font-size: 1rem; color: #f1c40f; font-weight: bold; min-width: 40px; text-align: center; }
.btn-row { font-size: 1rem !important; width: 30px !important; height: 30px !important; }
.btn-smart { border-radius: 20px !important; width: auto !important; padding: 0 12px !important; font-size: 0.9rem !important; font-weight: bold; gap: 5px; }
.btn-smart.active { background: #e67e22 !important; }
.dot { width: 12px; height: 12px; border-radius: 50%; border: 2px solid white; }
.mode-toggle { display: flex; background: #222; border-radius: 20px; padding: 2px; }
.separator { width: 1px; height: 20px; background: #555; }
.zoom-indicator { font-size: 0.75rem; color: #888; margin-left: 5px; }
.placeholder { color: #555; text-align: center; margin-top: 30vh; font-size: 1.2rem; }
.btn-edit-mode { font-size: 0.8rem !important; width: auto !important; border-radius: 20px !important; padding: 0 10px !important; }
</style>