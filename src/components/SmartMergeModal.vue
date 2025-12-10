<script setup>
    import { ref, onMounted, watch } from 'vue'
    import { getColorClusters, mergeColors, getPalette } from '../api.js'
    
    const emit = defineEmits(['close'])
    const clusters = ref([])
    const paletteData = ref({}) 
    const loading = ref(true)
    const strategy = ref('frequent') 
    
    onMounted(async () => {
      try {
        const pal = await getPalette()
        const list = Array.isArray(pal) ? pal : pal.palette || []
        
        list.forEach(c => {
          const hex = c.hex.replace('#', '')
          const r = parseInt(hex.substring(0, 2), 16)
          const g = parseInt(hex.substring(2, 4), 16)
          const b = parseInt(hex.substring(4, 6), 16)
          const luminance = 0.299*r + 0.587*g + 0.114*b 
          paletteData.value[c.index] = { ...c, luminance }
        })
    
        const rawClusters = await getColorClusters()
        clusters.value = rawClusters.map(group => ({
          indices: group,
          target: group[0],
          ignored: false
        }))
        
        applyStrategy()
      } catch (err) {
        console.error(err)
        // alert("Erro ao buscar sugestões. Tente recarregar a imagem.") 
        emit('close')
      } finally {
        loading.value = false
      }
    })
    
    function applyStrategy() {
      clusters.value.forEach(group => {
        if (group.ignored) return;
        let bestIdx = group.indices[0];
        let bestVal = getScore(bestIdx);
        group.indices.forEach(idx => {
          const val = getScore(idx);
          const isBetter = (strategy.value === 'lightest') ? (val > bestVal) :
                           (strategy.value === 'darkest')  ? (val < bestVal) :
                           (val > bestVal); 
          if (isBetter) { bestVal = val; bestIdx = idx; }
        })
        group.target = bestIdx;
      })
    }
    
    function getScore(idx) {
      const info = paletteData.value[idx];
      if (!info) return 0;
      if (strategy.value === 'frequent') return info.count;
      return info.luminance;
    }
    
    watch(strategy, applyStrategy)
    
    async function acceptMerge(group) {
      if (group.ignored) return
      const others = group.indices.filter(i => i !== group.target)
      for (const idx of others) {
        await mergeColors(idx, group.target)
      }
      group.ignored = true 
    }
    </script>
    
    <template>
      <div class="smart-panel">
        <div class="header">
          <h3>Sugestões Inteligentes</h3>
          <button @click="emit('close')" class="close">✕</button>
        </div>
    
        <div v-if="loading" class="loading">Analisando...</div>
        <div v-else-if="clusters.length === 0" class="empty">Nenhuma sugestão encontrada</div>
    
        <div v-else class="content">
          <div class="strategies">
            <label title="Mantém a cor mais usada"><input type="radio" value="frequent" v-model="strategy"> Comum</label>
            <label title="Mantém a cor mais escura"><input type="radio" value="darkest" v-model="strategy"> Escura</label>
            <label title="Mantém a cor mais clara"><input type="radio" value="lightest" v-model="strategy"> Clara</label>
          </div>
    
          <div class="list custom-scroll">
            <div v-for="(group, gIdx) in clusters" :key="gIdx" class="group-row" :class="{ done: group.ignored }">
              
              <div class="colors-preview">
                <div 
                  v-for="idx in group.indices" :key="idx" 
                  class="swatch" 
                  :style="{ backgroundColor: paletteData[idx]?.hex }"
                  :class="{ selected: group.target === idx }"
                  @click="group.target = idx"
                ></div>
              </div>
    
              <div class="actions">
                <span class="arrow">➔</span>
                <div class="final-swatch" :style="{ backgroundColor: paletteData[group.target]?.hex }"></div>
                <button @click="acceptMerge(group)" class="btn-merge">OK</button>
              </div>
    
            </div>
          </div>
        </div>
      </div>
    </template>
    
    <style scoped>
/* Estilo de PAINEL FLUTUANTE na Direita */
.smart-panel {
  position: fixed;
  top: 50%;           /* Meio da tela vertical */
  right: 80px;        /* Um pouco afastado da borda direita para não colar */
  transform: translateY(-50%); /* Centralização exata */
  
  width: 300px; 
  max-height: 80vh;
  
  background: #252526; 
  border: 1px solid #444; border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0,0,0,0.7); /* Sombra forte para destacar */
  display: flex; flex-direction: column;
  z-index: 2000; /* Bem alto para ficar acima de tudo */
  color: #ddd;
}

/* ... (O resto do CSS interno: .header, .content, etc. pode manter igual, só mudamos a posição acima) ... */
.header {
  padding: 12px 15px; background: #2c2c2c; border-bottom: 1px solid #333;
  display: flex; justify-content: space-between; align-items: center;
  border-top-left-radius: 12px; border-top-right-radius: 12px;
}
.header h3 { margin: 0; font-size: 1rem; color: #e67e22; }
.close { background: none; border: none; color: #aaa; cursor: pointer; font-size: 1.2rem; }
.content { padding: 10px; display: flex; flex-direction: column; overflow: hidden; }
.strategies { display: flex; gap: 10px; justify-content: space-between; margin-bottom: 10px; font-size: 0.8rem; }
.strategies label { cursor: pointer; display: flex; align-items: center; gap: 4px; }
.strategies input { accent-color: #e67e22; }
.list { overflow-y: auto; flex: 1; padding-right: 5px; max-height: 60vh; }
.group-row { display: flex; justify-content: space-between; align-items: center; background: rgba(0,0,0,0.2); padding: 8px; margin-bottom: 8px; border-radius: 6px; transition: opacity 0.3s; }
.group-row.done { opacity: 0.2; pointer-events: none; }
.colors-preview { display: flex; gap: 4px; flex-wrap: wrap; max-width: 55%; }
.swatch { width: 20px; height: 20px; border-radius: 50%; border: 1px solid transparent; cursor: pointer; }
.swatch.selected { border-color: white; transform: scale(1.2); z-index: 2; box-shadow: 0 0 4px white; }
.actions { display: flex; align-items: center; gap: 8px; }
.final-swatch { width: 24px; height: 24px; border-radius: 4px; border: 1px solid #555; }
.btn-merge { background: #27ae60; border: none; color: white; padding: 4px 10px; border-radius: 4px; cursor: pointer; font-size: 0.8rem; font-weight: bold; }
.btn-merge:hover { background: #2ecc71; }
.loading, .empty { padding: 20px; text-align: center; color: #888; font-size: 0.9rem; }
.custom-scroll::-webkit-scrollbar { width: 6px; }
.custom-scroll::-webkit-scrollbar-thumb { background: #444; border-radius: 3px; }
</style>