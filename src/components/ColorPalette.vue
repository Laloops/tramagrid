<script setup>
    import { ref, watch, onMounted, onUnmounted } from "vue";
    import { sessionId, eventBus, getPalette, replaceColor, deleteColor as apiDeleteColor } from "../api.js";
    
    const palette = ref([]);
    
    // Carrega a paleta usando o ID partilhado
    async function loadPalette() {
      if (!sessionId.value) {
        palette.value = [];
        return;
      }
      try {
        const data = await getPalette();
        // Garante que é um array, dependendo do formato do backend
        palette.value = Array.isArray(data) ? data : data.palette || [];
      } catch (e) {
        console.error("Erro ao carregar paleta:", e);
        palette.value = [];
      }
    }
    
    // 1. Reatividade: Se o ID da sessão mudar (ex: ao criar sessão), carrega a paleta
    watch(sessionId, loadPalette, { immediate: true });
    
    // 2. Eventos: Se algo mudar (ex: gerou grade nova), recarrega
    function onRefresh() {
      loadPalette();
      // Se quiser atualizar a grade visual também (caso o componente GridCanvas use o método global)
      if (typeof window.refreshGrid === "function") {
        window.refreshGrid();
      }
    }
    
    onMounted(() => {
      eventBus.addEventListener('refresh', onRefresh);
    });
    
    onUnmounted(() => {
      eventBus.removeEventListener('refresh', onRefresh);
    });
    
    // Funções de interação
    async function pickColor(index, currentHex) {
      const input = document.createElement("input");
      input.type = "color";
      input.value = currentHex;
    
      input.onchange = async () => {
        try {
          await replaceColor(index, input.value);
          // Não precisa chamar loadPalette() aqui porque o replaceColor no api.js dispara o evento 'refresh'
        } catch (e) {
          console.error(e);
          alert("Erro ao trocar cor");
        }
      };
      input.click();
    }
    
    async function deleteColor(index) {
      if (!confirm("Deletar essa cor de todos os quadradinhos?")) return;
      try {
        await apiDeleteColor(index);
      } catch (e) {
        console.error(e);
        alert("Erro ao deletar cor");
      }
    }
    </script>
    
    <template>
      <div class="color-palette">
        <h3>Paleta de Cores ({{ palette.length }})</h3>
        <div class="colors">
          <div
            v-for="color in palette"
            :key="color.index"
            class="color-box"
            @click="pickColor(color.index, color.hex)"
            title="Clique para trocar essa cor"
          >
            <div class="swatch" :style="{ backgroundColor: color.hex }"></div>
            <button @click.stop="deleteColor(color.index)" class="delete">×</button>
          </div>
        </div>
      </div>
    </template>
    
    <style scoped>
    /* O seu CSS original mantém-se inalterado */
    .color-palette { background: #1e1e1e; padding: 20px; border-radius: 12px; color: white; width: 320px; }
    h3 { margin: 0 0 16px 0; font-size: 1.1rem; }
    .colors { display: flex; flex-wrap: wrap; gap: 14px; }
    .color-box { position: relative; width: 70px; height: 70px; border-radius: 12px; cursor: pointer; border: 3px solid transparent; transition: all 0.2s; }
    .color-box:hover { transform: scale(1.15); border-color: #0ff; box-shadow: 0 0 20px rgba(0,255,255,0.4); }
    .swatch { width: 100%; height: 100%; border-radius: 10px; }
    .delete { position: absolute; top: -10px; right: -10px; width: 28px; height: 28px; background: #e74c3c; color: white; border: none; border-radius: 50%; font-size: 18px; cursor: pointer; opacity: 0; transition: opacity 0.2s; }
    .color-box:hover .delete { opacity: 1; }
    </style>