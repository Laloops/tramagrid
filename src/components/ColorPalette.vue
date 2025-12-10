<script setup>
import { ref, watch, onMounted, onUnmounted } from "vue";
import {
  sessionId,
  eventBus,
  getPalette,
  replaceColor,
  deleteColor as apiDeleteColor,
  mergeColors,
  activeColorIndex,
} from "../api.js";
import SmartMergeModal from "./SmartMergeModal.vue"; // <--- IMPORTAR O MODAL

const palette = ref([]);
const isMergeMode = ref(false);
const mergeSourceIndex = ref(null);
const showSmartModal = ref(false); // <--- ESTADO DO MODAL

async function loadPalette() {
  if (!sessionId.value) {
    palette.value = [];
    return;
  }
  try {
    const data = await getPalette();
    palette.value = Array.isArray(data) ? data : data.palette || [];
    if (palette.value.length > 0 && activeColorIndex.value === null) {
      activeColorIndex.value = palette.value[0].index;
    }
  } catch (e) {
    console.error(e);
  }
}

watch(sessionId, loadPalette, { immediate: true });

function onRefresh() {
  loadPalette();
  if (typeof window.refreshGrid === "function") window.refreshGrid();
}

onMounted(() => eventBus.addEventListener("refresh", onRefresh));
onUnmounted(() => eventBus.removeEventListener("refresh", onRefresh));

function handleColorClick(index) {
  if (isMergeMode.value) {
    if (mergeSourceIndex.value === null) {
      mergeSourceIndex.value = index;
    } else {
      if (index === mergeSourceIndex.value) {
        mergeSourceIndex.value = null;
        return;
      }
      executeMerge(mergeSourceIndex.value, index);
    }
  } else {
    activeColorIndex.value = index;
  }
}

async function executeMerge(from, to) {
  if (!confirm("Juntar estas duas cores?")) {
    mergeSourceIndex.value = null;
    return;
  }
  try {
    await mergeColors(from, to);
    mergeSourceIndex.value = null;
    isMergeMode.value = false;
  } catch (e) {
    alert("Erro ao mesclar");
  }
}

async function editHex(index, currentHex) {
  const input = document.createElement("input");
  input.type = "color";
  input.value = currentHex;
  input.onchange = async () => {
    try {
      await replaceColor(index, input.value);
    } catch (e) {}
  };
  input.click();
}

async function deleteColor(index) {
  if (!confirm("Deletar esta cor?")) return;
  try {
    await apiDeleteColor(index);
  } catch (e) {}
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
        >
          ✨ Auto
        </button>

        <button
          class="btn-toggle-merge"
          :class="{ active: isMergeMode }"
          @click="
            isMergeMode = !isMergeMode;
            mergeSourceIndex = null;
          "
          title="Juntar manual"
        >
          {{ isMergeMode ? "Cancelar" : "🔗 Unir" }}
        </button>
      </div>
    </div>

    <div v-if="isMergeMode" class="instructions">
      <span v-if="mergeSourceIndex === null"
        >Escolha a cor para <b>SUMIR</b>...</span
      >
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
          'merge-mode': isMergeMode,
        }"
        @click="handleColorClick(color.index)"
      >
        <div class="swatch" :style="{ backgroundColor: color.hex }"></div>
        <template v-if="!isMergeMode">
          <button
            @click.stop="deleteColor(color.index)"
            class="action-btn delete"
          >
            ×
          </button>
          <button
            @click.stop="editHex(color.index, color.hex)"
            class="action-btn edit"
          >
            ✎
          </button>
        </template>
        <div
          v-if="isMergeMode && mergeSourceIndex === color.index"
          class="merge-indicator"
        >
          ❌
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.color-palette {
  background: #1e1e1e;
  padding: 15px;
  color: white;
  border-radius: 8px;
  margin-top: 10px;
}
.header-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.buttons {
  display: flex;
  gap: 6px;
}
h3 {
  margin: 0;
  font-size: 1rem;
  color: #ccc;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.instructions {
  background: #2c3e50;
  padding: 8px;
  border-radius: 6px;
  margin-bottom: 12px;
  font-size: 0.8rem;
  color: #f1c40f;
  text-align: center;
  border: 1px solid #f1c40f;
}

.btn-toggle-merge,
.btn-icon {
  background: #333;
  border: 1px solid #555;
  color: #ccc;
  padding: 4px 8px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.75rem;
  transition: all 0.2s;
}
.btn-toggle-merge:hover,
.btn-icon:hover {
  background: #444;
  color: white;
}
.btn-toggle-merge.active {
  background: #d35400;
  border-color: #e67e22;
  color: white;
}

.colors {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(32px, 1fr));
  gap: 8px;
}

.color-box {
  position: relative;
  width: 32px;
  height: 32px;
  border-radius: 6px;
  cursor: pointer;
  border: 1px solid rgba(255, 255, 255, 0.1);
  transition: transform 0.1s, box-shadow 0.2s;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.color-box:hover {
  transform: translateY(-2px);
  z-index: 5;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.5);
  border-color: rgba(255, 255, 255, 0.5);
}

.color-box.active {
  border: 2px solid #fff;
  box-shadow: 0 0 0 2px #e67e22; /* Anel externo laranja */
  transform: scale(1.1);
  z-index: 10;
}

.color-box.merge-source {
  border-color: #e74c3c;
  opacity: 0.5;
  transform: scale(0.9);
}

.swatch {
  width: 100%;
  height: 100%;
  border-radius: 5px;
}

/* Botões de ação (editar/deletar) aparecem só no hover e são minúsculos */
.action-btn {
  position: absolute;
  width: 16px;
  height: 16px;
  border: none;
  border-radius: 50%;
  color: white;
  font-size: 10px;
  cursor: pointer;
  opacity: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: opacity 0.2s;
  z-index: 20;
}
.color-box:hover .action-btn {
  opacity: 1;
}
.delete {
  top: -6px;
  right: -6px;
  background: #e74c3c;
  box-shadow: 0 2px 2px rgba(0, 0, 0, 0.3);
}
.edit {
  bottom: -6px;
  right: -6px;
  background: #3498db;
  box-shadow: 0 2px 2px rgba(0, 0, 0, 0.3);
}

.merge-indicator {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
  text-shadow: 0 0 3px black;
}
</style>
