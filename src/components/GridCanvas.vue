<script setup>
  import { ref, onMounted, onUnmounted, watch } from "vue";
  import { getGridImage, updateParams } from "../api.js";
  
  const imageSrc = ref("");
  const zoom = ref(1.0);
  const highlightedRow = ref(-1);
  
  const panX = ref(0);
  const panY = ref(0);
  const isDragging = ref(false);
  const dragStartX = ref(0);
  const dragStartY = ref(0);
  
  async function refresh() {
  // atualiza highlighted_row no backend (se necessário)
  await updateParams({
    highlighted_row: highlightedRow.value === -1 ? null : highlightedRow.value,
  });

  // getGridImage pode retornar:
  // - uma string (data:image/png;base64,...)
  // - ou um objeto { image_base64: "..." } dependendo de api.js
  const data = await getGridImage();

  if (!data) {
    imageSrc.value = "";
    return;
  }

  if (typeof data === "string") {
    imageSrc.value = data;
  } else if (data.image_base64) {
    // pode ser já a string 'data:image/png;base64,...' ou só o base64 (em alguns backends)
    if (data.image_base64.startsWith("data:")) {
      imageSrc.value = data.image_base64;
    } else {
      imageSrc.value = "data:image/png;base64," + data.image_base64;
    }
  } else if (data.imagem) {
    // compatibilidade com respostas que usam chave 'imagem'
    imageSrc.value = data.imagem.startsWith("data:") ? data.imagem : "data:image/png;base64," + data.imagem;
  } else {
    // fallback: stringify and show nothing
    imageSrc.value = "";
    console.warn("getGridImage: formato inesperado", data);
  }
}

  
  watch([zoom, highlightedRow], refresh, { immediate: true });
  
  onMounted(() => {
    refresh();
    window.refreshGrid = refresh;
  });
  
  function handleWheel(e) {
    e.preventDefault();
    const delta = e.deltaY > 0 ? 0.9 : 1.1;
    zoom.value = Math.max(0.3, Math.min(10, zoom.value * delta));
  }
  
  function startDrag(e) {
    if (e.button !== 0) return;
    isDragging.value = true;
    dragStartX.value = e.clientX - panX.value;
    dragStartY.value = e.clientY - panY.value;
  }
  
  function drag(e) {
    if (!isDragging.value) return;
    panX.value = e.clientX - dragStartX.value;
    panY.value = e.clientY - dragStartY.value;
  }
  
  function stopDrag() {
    isDragging.value = false;
  }
  
  onUnmounted(() => {
    document.removeEventListener("mousemove", drag);
    document.removeEventListener("mouseup", stopDrag);
  });
  
  // AQUI ESTÁ A MÁGICA – 100% FUNCIONANDO
  function handleClick(e) {
  if (isDragging.value) return;

  const rect = e.currentTarget.getBoundingClientRect();
  const clickX = e.clientX - rect.left;
  const clickY = e.clientY - rect.top;

  const originalX = clickX / zoom.value;
  const originalY = clickY / zoom.value;

  const MARGIN = 50;
  const CELL_SIZE = 22;

  if (originalY < MARGIN) return;

  const row = Math.floor((originalY - MARGIN) / CELL_SIZE) + 1;

  highlightedRow.value = highlightedRow.value === row ? -1 : row;
}
  </script>
  
  <template>
    <div
      class="canvas"
      @wheel.prevent="handleWheel"
      @mousedown="startDrag"
      @mousemove="drag"
      @mouseup="stopDrag"
      @mouseleave="stopDrag"
      @contextmenu.prevent
    >
      <img
        v-if="imageSrc"
        :src="imageSrc"
        @click="handleClick"
        :style="{
          transform: `translate(${panX}px, ${panY}px) scale(${zoom})`,
          transformOrigin: 'top left',
          imageRendering: 'pixelated',
          maxWidth: 'none',
          userSelect: 'none',
          cursor: isDragging ? 'grabbing' : 'crosshair',
        }"
        draggable="false"
      />
  
      <div v-else class="placeholder">
        Carregue uma imagem e clique em "Gerar Grade"
      </div>
    </div>
  </template>
  
  <style scoped>
  .canvas {
    height: 100%;
    background: #111;
    padding: 20px;        /* pode manter o padding, não interfere mais */
    overflow: hidden;
    cursor: default;
  }
  .placeholder {
    color: #999;
    text-align: center;
    margin-top: 20vh;
    font-size: 1.5rem;
  }
  </style>