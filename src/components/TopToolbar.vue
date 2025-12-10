<!-- src/components/TopToolbar.vue -->
<script setup>
  import { ref } from 'vue'
  import { uploadImage, generateGrid, updateParams, getGridImage } from '../api.js'
  
  const fileInput = ref(null)
  const maxColors = ref(64)
  const gridWidth = ref(130)
  const currentGridImage = ref('')  // para o botão salvar
  
  async function handleUpload(e) {
    const file = e.target.files[0]
    if (!file) return
    await uploadImage(file)
    alert('Imagem carregada! Clique em "Gerar Grade"')
  }
  
  async function generate() {
  console.log("Gerando grade...")  // pra você ver no console
  await updateParams({ 
    max_colors: maxColors.value, 
    grid_width_cells: gridWidth.value 
  })
  await generateGrid()
  await window.refreshGrid()   // ← FORÇA A ATUALIZAÇÃO DA IMAGEM
  console.log("Grade gerada e imagem atualizada!")
}
  
  function saveGrid() {
    if (!currentGridImage.value) {
      alert('Gere a grade primeiro!')
      return
    }
    const a = document.createElement('a')
    a.href = currentGridImage.value
    a.download = 'tramagrid.png'
    a.click()
  }
  </script>
  
  <template>
    <header class="toolbar">
      <input type="file" ref="fileInput" @change="handleUpload" hidden accept="image/*" />
      <button @click="fileInput.click()" class="btn primary">Carregar Imagem</button>
      <button @click="generate" class="btn success">Gerar Grade</button>
      <button @click="saveGrid" class="btn info">Salvar PNG</button>
      
      <div class="params">
        <label>
          Cores: 
          <input v-model.number="maxColors" type="number" min="8" max="256" style="width:70px;" />
        </label>
        <label>
          Largura: 
          <input v-model.number="gridWidth" type="number" min="50" max="300" style="width:70px;" />
        </label>
      </div>
    </header>
  </template>
  
  <style scoped>
  .toolbar {
    background: #34495e;
    height: 60px;
    display: flex;
    align-items: center;
    padding: 0 20px;
    gap: 12px;
    color: white;
  }
  .btn {
    padding: 10px 20px;
    border: none;
    color: white;
    font-weight: bold;
    cursor: pointer;
    border-radius: 4px;
  }
  .primary { background: #27ae60; }
  .success { background: #2980b9; }
  .info { background: #8e44ad; }
  .params {
    margin-left: auto;
    display: flex;
    gap: 20px;
    align-items: center;
  }
  </style>