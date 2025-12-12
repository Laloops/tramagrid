<script setup>
  import { ref, onMounted, watch } from 'vue'
  import { getColorClusters, mergeColors, getPalette } from '../api.js'
  import { showToast } from '../toast.js' // <--- Importando Toast
  
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
      showToast("Erro ao buscar sugestões inteligentes.", "error") // <--- Toast Erro
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
    try {
        const others = group.indices.filter(i => i !== group.target)
        for (const idx of others) {
          await mergeColors(idx, group.target)
        }
        group.ignored = true 
        showToast("Cores agrupadas com sucesso!", "success") // <--- Toast Sucesso
    } catch (e) {
        showToast("Erro ao agrupar cores.", "error")
    }
  }
  </script>
  
  <template>
    <div class="smart-panel">
      <div class="header">
        <h3>Sugestões Inteligentes</h3>
        <button @click="emit('close')" class="close">✕</button>
      </div>
  
      <div v-if="loading" class="loading">
          <span class="spinner-mini"></span> Analisando paleta...
      </div>
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
                title="Clique para definir como principal"
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
  /* Painel Flutuante Estilizado */
  .smart-panel {
    position: fixed;
    top: 50%;           
    right: 100px; /* Afastado da sidebar */
    transform: translateY(-50%); 
    
    width: 320px; 
    max-height: 70vh;
    
    background: #1e1e1e; /* Cor padrão do tema */
    border: 1px solid #444; 
    border-radius: 12px;
    box-shadow: 0 10px 40px rgba(0,0,0,0.6);
    display: flex; flex-direction: column;
    z-index: 2000; 
    color: #ddd;
    animation: slideIn 0.3s ease-out;
  }
  
  @keyframes slideIn {
      from { opacity: 0; transform: translateY(-40%); }
      to { opacity: 1; transform: translateY(-50%); }
  }
  
  .header {
    padding: 12px 15px; background: #252526; border-bottom: 1px solid #333;
    display: flex; justify-content: space-between; align-items: center;
    border-top-left-radius: 12px; border-top-right-radius: 12px;
  }
  .header h3 { margin: 0; font-size: 0.95rem; color: #e67e22; font-weight: 700; text-transform: uppercase; }
  .close { background: none; border: none; color: #888; cursor: pointer; font-size: 1.2rem; transition: 0.2s; }
  .close:hover { color: white; }
  
  .content { padding: 15px; display: flex; flex-direction: column; overflow: hidden; }
  
  .strategies { 
      display: flex; gap: 10px; justify-content: space-between; margin-bottom: 15px; 
      background: #252526; padding: 8px; border-radius: 8px; font-size: 0.8rem;
  }
  .strategies label { cursor: pointer; display: flex; align-items: center; gap: 5px; color: #ccc; }
  .strategies input { accent-color: #e67e22; }
  
  .list { overflow-y: auto; flex: 1; padding-right: 5px; max-height: 50vh; }
  
  .group-row { 
      display: flex; justify-content: space-between; align-items: center; 
      background: rgba(255,255,255,0.03); padding: 10px; margin-bottom: 8px; 
      border-radius: 8px; border: 1px solid transparent; transition: all 0.2s; 
  }
  .group-row:hover { border-color: #555; background: rgba(255,255,255,0.05); }
  .group-row.done { opacity: 0.3; pointer-events: none; filter: grayscale(1); }
  
  .colors-preview { display: flex; gap: 6px; flex-wrap: wrap; max-width: 50%; }
  .swatch { width: 22px; height: 22px; border-radius: 50%; border: 2px solid transparent; cursor: pointer; transition: transform 0.2s; box-shadow: 0 2px 4px rgba(0,0,0,0.3); }
  .swatch:hover { transform: scale(1.1); z-index: 2; }
  .swatch.selected { border-color: #fff; transform: scale(1.2); z-index: 3; box-shadow: 0 0 8px rgba(255,255,255,0.5); }
  
  .actions { display: flex; align-items: center; gap: 10px; }
  .arrow { color: #666; font-size: 0.9rem; }
  .final-swatch { width: 28px; height: 28px; border-radius: 6px; border: 1px solid #666; box-shadow: 0 2px 5px rgba(0,0,0,0.5); }
  
  .btn-merge { 
      background: #27ae60; border: none; color: white; padding: 6px 12px; 
      border-radius: 6px; cursor: pointer; font-size: 0.8rem; font-weight: bold; 
      transition: 0.2s; 
  }
  .btn-merge:hover { background: #2ecc71; transform: translateY(-1px); }
  
  .loading, .empty { padding: 30px; text-align: center; color: #888; font-size: 0.9rem; }
  .spinner-mini { display: inline-block; width: 12px; height: 12px; border: 2px solid #666; border-top-color: #e67e22; border-radius: 50%; animation: spin 1s infinite linear; margin-right: 8px; }
  @keyframes spin { to { transform: rotate(360deg); } }
  
  .custom-scroll::-webkit-scrollbar { width: 5px; }
  .custom-scroll::-webkit-scrollbar-track { background: transparent; }
  .custom-scroll::-webkit-scrollbar-thumb { background: #444; border-radius: 3px; }
  </style>