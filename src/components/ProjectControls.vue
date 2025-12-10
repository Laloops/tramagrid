<script setup>
    import { ref } from 'vue'
    import { uploadImage, generateGrid, updateParams, sessionId } from '../api.js'
    
    const fileInput = ref(null)
    
    const maxColors = ref(64)
    const gridWidth = ref(130)
    
    // Parâmetros de Imagem
    const brightness = ref(1.0)
    const contrast = ref(1.0)
    const saturation = ref(1.0)
    const gamma = ref(1.0)
    
    // NOVO: Posterização (Níveis de Cor)
    // 8 = normal (256 níveis por canal), 1 = binário
    const posterize = ref(8) 
    
    async function handleUpload(e) {
      const file = e.target.files[0]
      if (!file) return
      if (!sessionId.value) { alert("Aguarde a sessão..."); return }
      try {
        await uploadImage(file)
        alert('Imagem carregada! Use "Posterizar" para remover sombras.')
      } catch (err) {
        alert("Erro ao enviar: " + err.message)
      }
    }
    
    async function generate() {
      await updateParams({ 
        max_colors: maxColors.value, 
        grid_width_cells: gridWidth.value,
        brightness: brightness.value,
        contrast: contrast.value,
        saturation: saturation.value,
        gamma: gamma.value,
        posterize: posterize.value // Enviando novo parâmetro
      })
      await generateGrid()
    }
    </script>
    
    <template>
      <div class="project-controls">
        <h3>Projeto</h3>
        
        <div class="control-group">
          <input type="file" ref="fileInput" @change="handleUpload" hidden accept="image/*" />
          <button @click="fileInput.click()" class="btn primary full-width">📂 Carregar Imagem</button>
        </div>
    
        <div class="separator"></div>
    
        <div class="control-group">
          <label title="Reduz os níveis de cor para criar um efeito 'chapado' e remover sombras suaves.">
            <span>Posterizar: {{ posterize }}</span>
            <input v-model.number="posterize" @change="generate" type="range" min="1" max="8" step="1" class="slider" />
          </label>
          
          <label>
            <span>Sombras: {{ gamma }}</span>
            <input v-model.number="gamma" @change="generate" type="range" min="0.5" max="3.0" step="0.1" class="slider" />
          </label>
    
          <label>
            <span>Brilho: {{ brightness }}</span>
            <input v-model.number="brightness" @change="generate" type="range" min="0.1" max="5.0" step="0.1" class="slider" />
          </label>
          
          <label>
            <span>Contraste: {{ contrast }}</span>
            <input v-model.number="contrast" @change="generate" type="range" min="0.1" max="5.0" step="0.1" class="slider" />
          </label>
          
          <label>
            <span>Saturação: {{ saturation }}</span>
            <input v-model.number="saturation" @change="generate" type="range" min="0.0" max="3.0" step="0.1" class="slider" />
          </label>
        </div>
    
        <div class="separator"></div>
    
        <div class="control-group">
          <label>
            <span>Cores Máx:</span>
            <input v-model.number="maxColors" type="number" min="2" max="128" class="input-number" />
          </label>
          <label>
            <span>Largura:</span>
            <input v-model.number="gridWidth" type="number" min="20" max="300" class="input-number" />
          </label>
        </div>
    
        <button @click="generate" class="btn success full-width mt-2">▶ Gerar Grade</button>
      </div>
    </template>
    
    <style scoped>
    /* Mesmo CSS anterior */
    .project-controls { background: #1e1e1e; padding: 20px; border-radius: 12px; color: white; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
    h3 { margin-top: 0; font-size: 1.1rem; color: #e67e22; margin-bottom: 15px; font-weight: 600; }
    .control-group { display: flex; flex-direction: column; gap: 12px; }
    label { display: flex; justify-content: space-between; align-items: center; font-size: 0.85rem; color: #ccc; }
    .slider { width: 55%; cursor: pointer; accent-color: #e67e22; }
    .input-number { width: 60px; background: #333; border: 1px solid #444; color: white; padding: 4px; border-radius: 4px; text-align: center; }
    .separator { height: 1px; background: #444; margin: 15px 0; }
    .btn { padding: 12px; border: none; color: white; font-weight: bold; cursor: pointer; border-radius: 6px; transition: all 0.2s; text-transform: uppercase; font-size: 0.85rem; letter-spacing: 0.5px; }
    .btn:hover { opacity: 0.9; transform: translateY(-1px); }
    .full-width { width: 100%; }
    .mt-2 { margin-top: 10px; }
    .primary { background: #d35400; }
    .success { background: #27ae60; }
    </style>