<script setup>
    import { ref, watch, onMounted, onUnmounted } from "vue";
    import { sessionId, eventBus, getPalette, replaceColor, deleteColor as apiDeleteColor, mergeColors, activeColorIndex } from "../api.js";
    import SmartMergeModal from './SmartMergeModal.vue'; // <--- IMPORTAR O MODAL
    
    const palette = ref([]);
    const isMergeMode = ref(false);
    const mergeSourceIndex = ref(null);
    const showSmartModal = ref(false); // <--- ESTADO DO MODAL
    
    async function loadPalette() {
      if (!sessionId.value) { palette.value = []; return; }
      try {
        const data = await getPalette();
        palette.value = Array.isArray(data) ? data : data.palette || [];
        if (palette.value.length > 0 && activeColorIndex.value === null) {
          activeColorIndex.value = palette.value[0].index;
        }
      } catch (e) { console.error(e); }
    }
    
    watch(sessionId, loadPalette, { immediate: true });
    
    function onRefresh() {
      loadPalette();
      if (typeof window.refreshGrid === "function") window.refreshGrid();
    }
    
    onMounted(() => eventBus.addEventListener('refresh', onRefresh));
    onUnmounted(() => eventBus.removeEventListener('refresh', onRefresh));
    
    function handleColorClick(index) {
      if (isMergeMode.value) {
        if (mergeSourceIndex.value === null) {
          mergeSourceIndex.value = index;
        } else {
          if (index === mergeSourceIndex.value) { mergeSourceIndex.value = null; return; }
          executeMerge(mergeSourceIndex.value, index);
        }
      } else {
        activeColorIndex.value = index;
      }
    }
    
    async function executeMerge(from, to) {
      if (!confirm("Juntar estas duas cores?")) { mergeSourceIndex.value = null; return; }
      try { await mergeColors(from, to); mergeSourceIndex.value = null; isMergeMode.value = false; } 
      catch (e) { alert("Erro ao mesclar"); }
    }
    
    async function editHex(index, currentHex) {
      const input = document.createElement("input");
      input.type = "color"; input.value = currentHex;
      input.onchange = async () => { try { await replaceColor(index, input.value); } catch (e) {} };
      input.click();
    }
    
    async function deleteColor(index) {
      if (!confirm("Deletar esta cor?")) return;
      try { await apiDeleteColor(index); } catch (e) {}
    }
    </script>
    
    <template>
      <div class="color-palette">
        <SmartMergeModal v-if="showSmartModal" @close="showSmartModal = false" />
    
        <div class="header-actions">
          <h3>Paleta ({{ palette.length }})</h3>
          
          <div class="buttons">
            <button 
              class="btn-icon" 
              @click="showSmartModal = true"
              title="Sugestões Automáticas"
            >✨ Auto</button>
    
            <button 
              class="btn-toggle-merge" 
              :class="{ active: isMergeMode }"
              @click="isMergeMode = !isMergeMode; mergeSourceIndex = null"
              title="Juntar manual"
            >
              {{ isMergeMode ? 'Cancelar' : '🔗 Unir' }}
            </button>
          </div>
        </div>
    
        <div v-if="isMergeMode" class="instructions">
          <span v-if="mergeSourceIndex === null">Escolha a cor para <b>SUMIR</b>...</span>
          <span v-else>Escolha a cor para <b>FICAR</b>.</span>
        </div>
    
        <div class="colors">
          <div
            v-for="color in palette"
            :key="color.index"
            class="color-box"
            :class="{ 
              active: !isMergeMode && activeColorIndex === color.index,
              'merge-source': isMergeMode && mergeSourceIndex === color.index,
              'merge-mode': isMergeMode
            }"
            @click="handleColorClick(color.index)"
          >
            <div class="swatch" :style="{ backgroundColor: color.hex }"></div>
            <template v-if="!isMergeMode">
              <button @click.stop="deleteColor(color.index)" class="action-btn delete">×</button>
              <button @click.stop="editHex(color.index, color.hex)" class="action-btn edit">✎</button>
            </template>
            <div v-if="isMergeMode && mergeSourceIndex === color.index" class="merge-indicator">❌</div>
          </div>
        </div>
      </div>
    </template>
    
    <style scoped>
    .color-palette { background: #1e1e1e; padding: 20px; color: white; }
    .header-actions { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }
    .buttons { display: flex; gap: 8px; }
    h3 { margin: 0; font-size: 1.1rem; color: #ccc; }
    
    .instructions {
      background: #2c3e50; padding: 10px; border-radius: 6px; margin-bottom: 15px;
      font-size: 0.9rem; color: #f1c40f; text-align: center; border: 1px solid #f1c40f;
    }
    
    .btn-toggle-merge, .btn-icon {
      background: #444; border: 1px solid #666; color: white;
      padding: 5px 10px; border-radius: 4px; cursor: pointer; font-size: 0.8rem;
    }
    .btn-toggle-merge.active { background: #d35400; border-color: #e67e22; }
    .btn-icon { background: #8e44ad; border-color: #9b59b6; }
    .btn-icon:hover { background: #9b59b6; }
    
    .colors { display: flex; flex-wrap: wrap; gap: 10px; }
    .color-box { 
      position: relative; width: 60px; height: 60px; 
      border-radius: 8px; cursor: pointer; border: 2px solid transparent; 
      transition: transform 0.1s;
    }
    .color-box.active {
      border-color: #e67e22; transform: scale(1.1); box-shadow: 0 0 10px rgba(230, 126, 34, 0.5); z-index: 2;
    }
    .color-box.merge-source { border-color: #e74c3c; transform: scale(0.9); opacity: 0.7; }
    .merge-indicator {
      position: absolute; top: 0; left: 0; width: 100%; height: 100%;
      display: flex; align-items: center; justify-content: center; font-size: 1.5rem;
    }
    .swatch { width: 100%; height: 100%; border-radius: 6px; }
    .action-btn {
      position: absolute; width: 24px; height: 24px;
      border: none; border-radius: 50%; color: white;
      font-size: 14px; cursor: pointer; opacity: 0;
      display: flex; align-items: center; justify-content: center;
      transition: opacity 0.2s;
    }
    .color-box:hover .action-btn { opacity: 1; }
    .delete { top: -8px; right: -8px; background: #e74c3c; }
    .edit { bottom: -8px; right: -8px; background: #3498db; font-size: 12px;}
    </style>