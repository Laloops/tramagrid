<script setup>
    import { ref, watch, onMounted } from "vue";
    
    const sessionId = ref(localStorage.getItem("sessionId"));
    const palette = ref([]);
    
    // Helper: tenta forçar refresh da grade (GridCanvas define window.refreshGrid())
    function tryRefreshGrid() {
      try {
        if (typeof window.refreshGrid === "function") {
          window.refreshGrid();
          return;
        }
        // fallback: trigger a custom event (opcional)
        window.dispatchEvent(new Event("tramagrid:refresh"));
      } catch (e) {
        console.warn("refreshGrid unavailable", e);
      }
    }
    
    async function pickColor(index, currentHex) {
      const input = document.createElement("input");
      input.type = "color";
      input.value = currentHex;
    
      input.onchange = async () => {
        try {
          // aguarda a troca no backend
          const res = await fetch(`/api/color/replace/${sessionId.value}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              index: index,
              new_hex: input.value,
            }),
          });
    
          if (!res.ok) throw new Error("Erro ao trocar cor");
    
          // atualiza paleta lateral
          await loadPalette();
    
          // pede ao GridCanvas para atualizar a grade
          tryRefreshGrid();
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
        const res = await fetch(`/api/color/delete/${sessionId.value}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ index }),
        });
        if (!res.ok) throw new Error("Erro ao deletar cor");
    
        // recarrega paleta e grade
        await loadPalette();
        tryRefreshGrid();
      } catch (e) {
        console.error(e);
        alert("Erro ao deletar cor");
      }
    }
    
    async function loadPalette() {
      if (!sessionId.value) {
        palette.value = [];
        return;
      }
      try {
        const res = await fetch(`/api/palette/${sessionId.value}`);
        if (!res.ok) throw new Error("Palette fetch failed");
        const data = await res.json();
        // se o backend já devolve ordenado, use direto; senão:
        palette.value = Array.isArray(data) ? data.sort((a, b) => b.count - a.count) : data.palette || [];
      } catch (e) {
        console.error(e);
        palette.value = [];
      }
    }
    
    // sincroniza mudança de sessão
    watch(
      () => localStorage.getItem("sessionId"),
      (newId) => {
        sessionId.value = newId;
        if (newId) loadPalette();
        else palette.value = [];
      },
      { immediate: true }
    );
    
    onMounted(() => {
      if (sessionId.value) loadPalette();
      // também escuta event fallback
      window.addEventListener("tramagrid:refresh", () => {
        // noop — GridCanvas já vai atualizar quando necessário, mas mantemos por segurança
        loadPalette().catch(()=>{});
      });
    });
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
    /* mantém seu CSS atual — sem alterações */
    .color-palette { background: #1e1e1e; padding: 20px; border-radius: 12px; color: white; width: 320px; }
    h3 { margin: 0 0 16px 0; font-size: 1.1rem; }
    .colors { display: flex; flex-wrap: wrap; gap: 14px; }
    .color-box { position: relative; width: 70px; height: 70px; border-radius: 12px; cursor: pointer; border: 3px solid transparent; transition: all 0.2s; }
    .color-box:hover { transform: scale(1.15); border-color: #0ff; box-shadow: 0 0 20px rgba(0,255,255,0.4); }
    .swatch { width: 100%; height: 100%; border-radius: 10px; }
    .delete { position: absolute; top: -10px; right: -10px; width: 28px; height: 28px; background: #e74c3c; color: white; border: none; border-radius: 50%; font-size: 18px; cursor: pointer; opacity: 0; transition: opacity 0.2s; }
    .color-box:hover .delete { opacity: 1; }
    </style>
    