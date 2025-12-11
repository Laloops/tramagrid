<script setup>
    import { ref } from 'vue'
    import { useRouter } from 'vue-router'
    import { createSession, uploadImage, sessionId } from '../api.js'
    
    const router = useRouter()
    const fileInput = ref(null)
    const isLoading = ref(false)
    
    async function handleStartUpload(e) {
      const file = e.target.files[0]
      if (!file) return
    
      isLoading.value = true
      try {
        // 1. Inicia Sessão
        await createSession()
        // 2. Sobe Imagem
        await uploadImage(file)
        // 3. Vai para o Editor (que agora vai gerar a grade sozinho)
        router.push('/editor')
      } catch (err) {
        alert("Erro: " + err.message)
      } finally {
        isLoading.value = false
      }
    }
    </script>
    
    <template>
      <div class="home-container">
        <div class="hero-box">
          <h1 class="title">Trama<span class="highlight">Grid</span></h1>
          <p class="subtitle">Faça upload e veja seu gráfico pronto em segundos.</p>
          
          <div class="upload-area">
            <input 
              type="file" 
              ref="fileInput" 
              @change="handleStartUpload" 
              hidden 
              accept="image/*" 
            />
            
            <button 
              @click="fileInput.click()" 
              class="btn-big-upload" 
              :disabled="isLoading"
            >
              <span v-if="isLoading" class="spinner-small"></span>
              <span v-else>✨ Criar Grade Agora</span>
            </button>
            
            <p class="hint">JPG ou PNG. Grátis e Automático.</p>
          </div>
        </div>
      </div>
    </template>
    
    <style scoped>
    /* (O CSS continua idêntico ao anterior) */
    .home-container {
      height: calc(100vh - 60px);
      display: flex; align-items: center; justify-content: center;
      background: #121212;
      background-image: radial-gradient(circle at center, #1e1e1e 0%, #121212 70%);
    }
    .hero-box {
      text-align: center; max-width: 600px; padding: 40px;
      background: rgba(30,30,30,0.5); border-radius: 20px;
      border: 1px solid #333; backdrop-filter: blur(10px);
      box-shadow: 0 20px 50px rgba(0,0,0,0.5);
    }
    .title { font-size: 3.5rem; margin-bottom: 10px; color: white; letter-spacing: -2px; }
    .highlight { color: #e67e22; }
    .subtitle { color: #aaa; font-size: 1.1rem; margin-bottom: 40px; line-height: 1.5; }
    .btn-big-upload {
      background: #e67e22; color: white; border: none; padding: 15px 40px;
      font-size: 1.2rem; font-weight: bold; border-radius: 50px; cursor: pointer;
      transition: all 0.3s; box-shadow: 0 10px 20px rgba(230, 126, 34, 0.3);
      display: flex; align-items: center; gap: 10px; margin: 0 auto;
    }
    .btn-big-upload:hover:not(:disabled) { transform: translateY(-3px); box-shadow: 0 15px 30px rgba(230, 126, 34, 0.4); background: #d35400; }
    .btn-big-upload:disabled { opacity: 0.7; cursor: wait; }
    .hint { margin-top: 15px; font-size: 0.85rem; color: #666; }
    .spinner-small { width: 20px; height: 20px; border: 3px solid rgba(255,255,255,0.3); border-top-color: white; border-radius: 50%; animation: spin 1s infinite linear; }
    @keyframes spin { to { transform: rotate(360deg); } }
    </style>