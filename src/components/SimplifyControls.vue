<!-- src/components/SimplifyControls.vue -->
<script setup>
    import { ref } from 'vue'
    import { simplifyPalette, simplifyBW } from '../api.js'
    
    const intensity = ref(30)
    
    async function applySimplify() {
      await simplifyPalette(intensity.value)
    }
    
    async function applyBW() {
      await simplifyBW()
    }
    </script>
    
    <template>
      <div class="controls">
        <h3>Simplificar Paleta</h3>
        <input type="range" v-model="intensity" min="0" max="100" />
        <button @click="applySimplify">Aplicar</button>
        <h4>Presets</h4>
        <div class="presets">
          <button @click="intensity = 5; applySimplify()">Pixel Art</button>
          <button @click="intensity = 30; applySimplify()">Crochê</button>
          <button @click="intensity = 50; applySimplify()">Minimalista</button>
          <button @click="applyBW">B&W Inteligente</button>
        </div>
      </div>
    </template>
    
    <style scoped>
    .controls { margin-top: 20px; }
    input { width: 100%; }
    button { width: 100%; padding: 10px; background: #16a085; color: white; border: none; cursor: pointer; margin-top: 10px; }
    .presets { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
    </style>