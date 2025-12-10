<script setup>
  import { ref, onMounted, onUnmounted, watch, computed } from "vue";
  // Importamos mergeColors para a nova ferramenta de balde
  import { getGridImage, updateParams, paintCell, getPixelIndex, replaceColor, undoLastAction, mergeColors, activeColorIndex, getPalette } from "../api.js";
  
  const imageSrc = ref("");
  const zoom = ref(1.0);
  const highlightedRow = ref(-1);
  // Ferramentas: 'ruler', 'brush', 'picker', 'swap', 'bucket' (NOVO)
  const currentTool = ref('ruler') 
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
    if (currentTool.value === 'ruler') {
      await updateParams({ highlighted_row: highlightedRow.value === -1 ? null : highlightedRow.value });
    }
    refresh();
  });
  
  onMounted(() => { refresh(); window.refreshGrid = refresh; });
  
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
  
  // --- CORREÇÃO DO BUG ---
  async function onColorPicked(e) {
    const newHex = e.target.value;
    // Verifica se temos um índice válido selecionado
    if (selectedIndexForSwap.value !== -1 && selectedIndexForSwap.value !== null) {
      try { 
        await replaceColor(selectedIndexForSwap.value, newHex); 
        refresh(); 
      } catch (err) { console.error(err); }
      finally {
        // FIX: Reseta o índice para não travar na próxima vez
        selectedIndexForSwap.value = -1; 
        // Reseta o valor do input para garantir que o evento change dispare mesmo se escolher a mesma cor
        e.target.value = null;
      }
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
    const clickedIndex = await getPixelIndex(gridX, gridY);
    if (clickedIndex === -1) return;
  
    if (currentTool.value === 'ruler') {
      const row = gridY + 1;
      highlightedRow.value = highlightedRow.value === row ? -1 : row;
      
    } else if (currentTool.value === 'brush') {
      await paintCell(gridX, gridY);
      refresh();
      
    } else if (currentTool.value === 'picker') {
      activeColorIndex.value = clickedIndex;
      currentTool.value = 'brush'; 
  
    } else if (currentTool.value === 'swap') {
      selectedIndexForSwap.value = clickedIndex;
      colorPickerInput.value.click();
    
    // --- NOVA FERRAMENTA: BALDE DE FUSÃO 🪣 ---
    } else if (currentTool.value === 'bucket') {
      const targetColor = activeColorIndex.value; // A cor que está no pincel (ex: Rosa)
      const sourceColor = clickedIndex; // A cor que clicamos (ex: Marrom)
  
      if (targetColor === sourceColor) return; // Não faz nada se for a mesma
  
      // Usa a função de mesclar do backend
      await mergeColors(sourceColor, targetColor);
      refresh();
    }
  }
  
  async function undo() { await undoLastAction(); refresh(); }
  </script>
  
  <template>
    <div class="canvas-wrapper">
      <input type="color" ref="colorPickerInput" style="display: none" @change="onColorPicked" @click.stop />
  
      <div class="tools-hud">
        <button @click="undo" title="Desfazer" class="action-btn undo-btn">↩️</button>
        <div class="separator"></div>
  
        <button @click="currentTool = 'ruler'" :class="{ active: currentTool === 'ruler' }" title="Régua">📏</button>
        
        <div class="smart-tool-group">
          <button 
            v-if="currentTool !== 'brush' && currentTool !== 'bucket'" 
            @click="setSmartTool" 
            :class="{ active: currentTool === 'picker' }"
            class="btn-smart"
            title="1º Pegar a cor desejada"
          >
            💧 Pegar Cor
          </button>
  
          <button 
            v-else 
            @click="currentTool = 'picker'" 
            class="btn-smart active"
            title="Cor ativa. Clique para trocar."
          >
            <span class="dot" :style="{ backgroundColor: activeColorHex }"></span>
            <span v-if="currentTool === 'brush'">✏️ Pintar Pixel</span>
            <span v-if="currentTool === 'bucket'">🪣 Fundir Tudo</span>
          </button>
        </div>
  
        <div class="separator"></div>
  
        <div class="mode-toggle">
           <button 
            @click="currentTool = 'brush'" 
            :class="{ active: currentTool === 'brush' }"
            title="Modo Pincel: Pinta apenas um quadradinho"
            :disabled="currentTool === 'ruler' || currentTool === 'swap' || currentTool === 'picker'"
          >✏️</button>
           <button 
            @click="currentTool = 'bucket'" 
            :class="{ active: currentTool === 'bucket' }"
            title="Modo Balde: Transforma TODA a cor clicada na cor do seu pincel (Fusão)"
            :disabled="currentTool === 'ruler' || currentTool === 'swap' || currentTool === 'picker'"
          >🪣</button>
        </div>
  
        <div class="separator"></div>
  
        <button @click="currentTool = 'swap'" :class="{ active: currentTool === 'swap' }" title="Troca Global por NOVA cor">🔄</button>
        
        <div class="zoom-indicator">{{ Math.round(zoom * 100) }}%</div>
      </div>
  
      <div class="canvas" @wheel.prevent="handleWheel" @mousedown="startDrag" @mousemove="drag" @mouseup="stopDrag" @mouseleave="stopDrag" @contextmenu.prevent>
        <img v-if="imageSrc" :src="imageSrc" @click="handleClick" :style="{ transform: `translate(${panX}px, ${panY}px) scale(${zoom})`, transformOrigin: 'top left', imageRendering: 'pixelated', cursor: currentTool === 'ruler' ? (isDragging ? 'grabbing' : 'default') : (currentTool === 'picker' ? 'alias' : (currentTool === 'bucket' ? 'cell' : 'crosshair')) }" draggable="false" />
        <div v-else class="placeholder">Carregue uma imagem para começar</div>
      </div>
    </div>
  </template>
  
  <style scoped>
  .canvas-wrapper { position: relative; width: 100%; height: 100%; overflow: hidden; background: #111; }
  .canvas { width: 100%; height: 100%; cursor: default; }
  .tools-hud {
    position: absolute; top: 20px; left: 50%; transform: translateX(-50%);
    background: rgba(40, 40, 40, 0.95); padding: 8px 15px; border-radius: 30px;
    display: flex; gap: 12px; align-items: center; z-index: 100;
    box-shadow: 0 4px 15px rgba(0,0,0,0.6); border: 1px solid #555;
  }
  .tools-hud button {
    background: transparent; border: none; font-size: 1.3rem; cursor: pointer;
    padding: 6px 10px; border-radius: 8px; transition: all 0.2s; opacity: 0.7; color: white;
  }
  .tools-hud button:hover:not(:disabled) { opacity: 1; background: rgba(255,255,255,0.1); }
  .tools-hud button.active {
    background: #e67e22; opacity: 1; transform: scale(1.05); box-shadow: 0 0 10px rgba(230, 126, 34, 0.4);
  }
  .tools-hud button:disabled { opacity: 0.3; cursor: not-allowed; }
  
  .undo-btn { font-size: 1.5rem !important; }
  
  .btn-smart {
    font-size: 0.9rem !important; font-weight: bold; display: flex; align-items: center; gap: 8px;
    background: #333 !important; padding-left: 15px !important; padding-right: 15px !important;
    border-radius: 20px !important; min-width: 130px; justify-content: center;
  }
  .btn-smart.active { background: #e67e22 !important; color: white !important; }
  .dot { width: 14px; height: 14px; border-radius: 50%; border: 2px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.3); }
  
  .mode-toggle { display: flex; background: #222; border-radius: 10px; padding: 2px; border: 1px solid #444; }
  .mode-toggle button { border-radius: 8px; padding: 4px 8px; font-size: 1.1rem; }
  .mode-toggle button.active { background: #e67e22; }
  
  .separator { width: 1px; height: 20px; background: #666; margin: 0 5px; }
  .zoom-indicator { color: #aaa; font-size: 0.8rem; margin-left: 5px; border-left: 1px solid #666; padding-left: 12px; }
  .placeholder { color: #555; text-align: center; margin-top: 30vh; font-size: 1.2rem; }
  </style>